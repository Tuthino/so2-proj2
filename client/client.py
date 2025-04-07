import os
import threading
import json
import socket
import select

class Client:
    def __init__(self):
        self.username = self.get_username()
        self.host = os.environ.get('SERVER_HOST', 'localhost')
        self.port = int(os.environ.get('SERVER_PORT', 5003))
        self.socket = None
        self.state = False  # incidate if we are connected to the server
        self.status = ''  # status of the last response
        # we do not need thread lock, because we are using a condition variable, 
        # after sending the payload, we wait until the listenet thread process the response
        # sets the status and free the condition variable
        self.response_condition = threading.Condition()
        self.listener_thread = None

    def get_username(self):
        # function to get username input from the cli
        while True:
            username = input("Enter your username: ").strip()
            if username:
                return username
            print("Username cannot be empty.")

    def display_chat_messages(self, payload):
        # set the witdth of the output, either max terminal width or 80
        try:
            width = os.get_terminal_size().columns
        except OSError:
            width = 80  # fallback value if terminal size can't be determined

        print("Displaying chat messages:")
        for msg in payload.get("res", {}).get("body", {}).get("messages", []):
            sender = msg.get("sender")
            text = msg.get("text")
            timestamp = msg.get("timestamp")
            if sender == self.username:
                # Right-aligned message
                metadata = f"{timestamp} {sender}:"
                print(metadata.rjust(width))
                text = f"{text}"
                print(text.rjust(width))
            else:
                # Left-aligned message
                metadata = f"{timestamp} {sender}:"
                print(metadata)
                text = f"{text}"
                print(text)
    
    def display_users(self, payload):
        print("Displaying all users:")
        users = payload.get("res", {}).get("body", {}).get("users", [])
        if not users:
            print("No users found.")
            return
        for user in users:
            print(user)

    def listen_for_notifications(self):
        # function to listening thread
        print("Listening for notifications...")
        while True:
            if self.socket.fileno() < 0:
                break
            try:
                ready, _, _ = select.select([self.socket], [], [], 0.5)
                if ready:
                    message = self.receive_message()
                    if message:
                        message_status = message.get("res", {}).get("status")
                        self.status = message_status
                        with self.response_condition:
                            self.response_condition.notify_all()
                        if message_status == "new_message":
                            print("\n*** NEW MESSAGE RECEIVED ***")
                            print(f"From: {message.get("res", {}).get('sender')}, Message: {message.get("res", {}).get('text')}\n")

            except Exception as e:
                print(f"Error in notification listener: {e}")

    def connect(self):
        # we create the socket, connect, start the listener thread and 
        # send the payload with username to fully connect to the server
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            print(f"Connecting to server at {self.host}:{self.port}...")
            self.socket.connect((self.host, self.port))
            self.listener_thread = threading.Thread(target=self.listen_for_notifications, daemon=True)
            self.listener_thread.start()
            payload = {
                "username": self.username,
                "op": "connect",
            }
            status = self.send_payload(payload)
            if status:
                print(f"Connected to server at {self.host}:{self.port}")
                self.state = True
            else:
                print(f"Failed to connect to server") 
                self.close_connection()
                return None
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            return None

    def receive_message(self):
        # function to receive the message
        # decodes status to activate needed function to process the body
        try:
            data = self.socket.recv(1024).decode()
            if data:
                try:
                    message = json.loads(data)
                    # print(f"Received message: {message}")
                    message_status = message.get("res", {}).get("status")
                    self.status = message_status
                    if message_status == "exit":
                        print("Server requested to close the connection.")
                        self.socket.close()
                        self.state = False
                        return  None
                    elif message_status == "show_messages":
                        self.display_chat_messages(message)
                    elif message_status == "show_users":
                        self.display_users(message)
                    return message
                except json.JSONDecodeError:
                    print(f"Received non-JSON message: {data}")
            else:
                print("No data received.")
        except Exception as e:
            print(f"Error receiving message: {e}")
        return  None

    def send_payload(self, payload):
        # clear the status, the listener thread will set it after receiving the response
        self.status = ''
        try:
            self.socket.send(json.dumps(payload).encode())
        except Exception as e:
            print(f"Failed to send payload: {e}")
        with self.response_condition:
            self.response_condition.wait_for(lambda: self.status != '', timeout=5)
        return self.status

    def close_connection(self):
        try:
            # send the payload to close the connection, so the server
            # can clean up the resources (terminate the thread)
            self.send_payload({"op": "exit"})
            self.socket.close()
            print("Connection closed.")
        except Exception as e:
            print(f"Error closing connection: {e}")

    def main_menu(self):
        if not self.state:
            print("You are not connected to the server.")
        print(f"\nLogged as: {self.username}, Main Menu:")
        print("1. Show all users")
        print("2. Chat with user")
        print("9. Close application")
        choice = input("Choose an option: ")
        return choice

    def chat_menu(self, chat_user):
        # this menu is shown after the user has selected a chat
        if not self.state:
            print("You are not connected to the server.")
        print(f"\nLogged as: {self.username}, Chat with {chat_user}:")
        print("1. Send message")
        print("2. Show all messages")
        print("9. Exit chat")
        choice = input("Choose an option: ")
        return choice

    def start(self):
        # try to connect to the server
        self.connect()
        if not self.state:
            print("Connection failed. Exiting.")
            return
        try:
            while True:
                main_choice = self.main_menu()
                if main_choice == '1':
                    payload = {"username": self.username, "op": "show_users"}
                    self.send_payload(payload)
                elif main_choice == '2':
                    chat_user = input("Enter the username you want to chat with: ")
                    payload = {"username": self.username, "op": "chat_with_user", "other_username": chat_user}
                    self.send_payload(payload)
                    if self.status != 'error':
                        # enter here only if server didn't return an error, for example
                        # if we want to chat with user that does not exist
                        while True:
                            chat_choice = self.chat_menu(chat_user)
                            if chat_choice == '1':
                                message = input("Enter your message: ")
                                payload = {"username": self.username, "op": "send_message", "other_username": chat_user, "message": message}
                                self.send_payload(payload)
                            elif chat_choice == '2':
                                payload = {"username": self.username, "op": "show_messages", "other_username": chat_user}
                                self.send_payload(payload)
                            elif chat_choice == '9':
                                print("Exiting chat.")
                                break
                            else:
                                print("Invalid choice. Please try again.")
                    else:
                        print("Chat initiation failed.")
                elif main_choice == '9':
                    # the state could be False, if server closed the connection
                    # so we need to check for that before calling the close_connection
                    if self.state:
                        self.close_connection()
                    print("Closing application.")
                    break
                else:
                    print("Invalid choice. Please try again.")
        except KeyboardInterrupt:
            print("Ctrl-C pressed. Closing application.")
        finally:
            # we get here in 2 scenarions:
            # 1. user pressed Ctrl-C
            # 2. user selected option 9
            # in both cases we need to check first if we are still connected 
            # and then we close the connection, thread ends loop after calling close_connection
            # because the self.state is set to False
            if self.state:
                self.close_connection()
            else:
                self.socket.close()
                self.state = False
                self.listener_thread.join()

if __name__ == "__main__":
    client = Client()
    client.start()