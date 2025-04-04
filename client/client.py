import os
import json
import socket
import select

class Client:
    def __init__(self):
        self.username = self.get_username()
        self.host = os.environ.get('SERVER_HOST', 'localhost')
        self.port = int(os.environ.get('SERVER_PORT', 5003))
        self.socket = None
        self.state = False

    def get_username(self):
        while True:
            username = input("Enter your username: ").strip()
            if username:
                return username
            print("Username cannot be empty.")

    def connect(self):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect((self.host, self.port))
            payload = {
                "username": self.username,
                "op": "connect",
            }
            status, resp = self.send_payload(client_socket, payload)
            if resp and resp.get("res", {}).get("status") == "ok":
                print(f"Connected to server at {self.host}:{self.port}")
                self.socket = client_socket
                self.state = True
                return client_socket
            else:
                print(f"Failed to connect to server: {resp.get('res', {}).get('status') if resp else 'No Response'}")
                self.close_connection(client_socket)
                return None
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            return None

    def receive_message(self, s):
        try:
            data = s.recv(1024).decode()
            if data:
                try:
                    message = json.loads(data)
                    print(f"Received message: {message}")
                    message_status = message.get("res", {}).get("status")
                    if message_status == "exit":
                        print("Server requested to close the connection.")
                        s.close()
                        return False, None
                    return True, message
                except json.JSONDecodeError:
                    print(f"Received non-JSON message: {data}")
            else:
                print("No data received.")
        except Exception as e:
            print(f"Error receiving message: {e}")
        return False, None

    def send_payload(self, s, payload):
        try:
            s.send(json.dumps(payload).encode())
            print(f"Sent payload: {payload}")
            return self.receive_message(s)
        except Exception as e:
            print(f"Failed to send payload: {e}")
        return False, None

    def close_connection(self, s):
        try:
            self.send_payload(s, {"op": "exit"})
            s.close()
            print("Connection closed.")
        except Exception as e:
            print(f"Error closing connection: {e}")

    def check_server_message(self, s, timeout=0.1):
        ready, _, _ = select.select([s], [], [], timeout)
        if ready:
            try:
                data = s.recv(1024)
                if data:
                    message_status = json.loads(data).get("res", {}).get("status")
                    if message_status == "exit":
                        print("Server requested to close the connection.")
                        s.close()
                        return False
            except Exception as e:
                print(f"Error receiving data: {e}")
        return None

    def main_menu(self):
        if not self.state:
            print("You are not connected to the server.")
        print(f"Logged as: {self.username}, Main Menu:")
        print("1. Show all users")
        print("2. Chat with user")
        print("9. Close application")
        choice = input("Choose an option: ")
        return choice

    def chat_menu(self, chat_user):
        print(f"Logged as: {self.username}, Chat with {chat_user}:")
        print("1. Send message")
        print("2. Show all messages")
        print("9. Exit chat")
        choice = input("Choose an option: ")
        return choice

    def start(self):
        # Try to connect to the server
        if not self.connect():
            print("Connection failed. Exiting.")
            return

        try:
            while True:
                main_choice = self.main_menu()
                if main_choice == '1':
                    payload = {"username": self.username, "op": "show_users"}
                    self.send_payload(self.socket, payload)
                elif main_choice == '2':
                    chat_user = input("Enter the username you want to chat with: ")
                    payload = {"username": self.username, "op": "chat_with_user", "other_username": chat_user}
                    status, resp = self.send_payload(self.socket, payload)
                    if resp and resp.get("res", {}).get("status") == "ok":
                        while True:
                            chat_choice = self.chat_menu(chat_user)
                            if chat_choice == '1':
                                message = input("Enter your message: ")
                                payload = {"username": self.username, "op": "send_message", "other_username": chat_user, "message": message}
                                self.send_payload(self.socket, payload)
                            elif chat_choice == '2':
                                payload = {"username": self.username, "op": "show_messages", "other_username": chat_user}
                                self.send_payload(self.socket, payload)
                            elif chat_choice == '9':
                                print("Exiting chat.")
                                break
                            else:
                                self.check_server_message(self.socket)
                                print("Invalid choice. Please try again.")
                    else:
                        print("Chat initiation failed.")
                elif main_choice == '9':
                    print("Closing application.")
                    break
                else:
                    self.check_server_message(self.socket)
                    print("Invalid choice. Please try again.")
        except KeyboardInterrupt:
            print("Ctrl-C pressed. Closing application.")
        finally:
            self.close_connection(self.socket)

if __name__ == "__main__":
    client = Client()
    client.start()