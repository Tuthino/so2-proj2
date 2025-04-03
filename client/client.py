import os
import select
import socket
import json

# TODO: simple tui interface for;
# - choosng the username
# - choosing the chat
# - exit the application
# After choosing the chat;
# - sending the message
# - force loading all chat messages
# - exit to previous menu
# ALL data needs to be sent as json

# TODO: OPTIONAL server ip and port as input variable when
# running the app


def get_username():
    while True:
        username = input("Enter your username: ").strip()
        if username:
            return username
        print("Username cannot be empty.")


def connect():
    # TODO: server ip and port as user input vars
    host = os.environ.get('SERVER_HOST', 'localhost')
    port = 5003

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host, port))
        print(f"Connected to server at {host}:{port}")
        return client_socket
    except Exception as e:
        print(f"Failed to connect to server: {e}")
        return None


def receive_message(s):
    # if the server sends payload to close the connection
    # this function will return False, otherwise True
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
                    return False
                return True
            except json.JSONDecodeError:
                print(f"Received non-JSON message: {data}")
        else:
            print("No data received.")
    except Exception as e:
        print(f"Error receiving message: {e}")


def send_payload(s, payload):
    try:
        s.send(json.dumps(payload).encode())
        print(f"Sent payload: {payload}")
        # TODO: it is possible that we do not need this
        return receive_message(s)  # False if server requested to close conn
    except Exception as e:
        print(f"Failed to send payload: {e}")


def close_connection(s):
    try:
        send_payload(s, {"op": "exit"})
        s.close()
        print("Connection closed.")
    except Exception as e:
        print(f"Error closing connection: {e}")


def check_server_message(s, timeout=0.1):
    # select.select monitors the socket 'sock' for readability.
    # It returns three lists: readable, writable, and exceptional sockets.
    # We only care about sockets that are ready for reading.
    ready, _, _ = select.select([s], [], [], timeout)
    if ready:
        try:
            data = s.recv(1024)
            message_status = json.loads(data).get("res", {}).get("status")
            if data:
                if message_status == "exit":
                    print("Server requested to close the connection.")
                    s.close()
                    return False
        except Exception as e:
            print(f"Error receiving data: {e}")
    return None


def main_menu(user, s, state):
    if state == 0:
        print("You are not connected to the server.")
    print("Main Menu:")
    print("1. Show all users")
    print("2. Show all chats")
    print("3. Chat with user")
    print("9. Close application")
    choice = input("Choose an option: ")
    return choice


def main():
    username = get_username()
    s = connect()
    state = False  # indicates if socket is connected
    # init empty payload
    payload = {}  # TODO: it is possible that we do not need this
    if not s:
        print("Connection failed. Exiting.")
        return
    state = True
    main_menu_choice = None
    # this try/catch is needed to catch ctrl-c interrupt
    # to close the socket connection before exiting the app
    try:
        while True:
            if state is not True:
                state = check_server_message(s)
            main_menu_choice = main_menu(username, s, state)
            if main_menu_choice == '1':
                op = "show_users"
                payload = {
                    "username": username,
                    "op": op,
                }
                state = send_payload(s, payload)
            elif main_menu_choice == '2':
                op = "show_chats"
                payload = {
                    "username": username,
                    "op": op,
                }
                state = send_payload(s, payload)
            elif main_menu_choice == '3':
                op = "chat_with_user"
                # maybe add here function to fetch usernames first
                chat_user = input("Enter the username you want to chat with: ")
                payload = {
                    "username": username,
                    "op": op,
                    "other_username": chat_user
                }
                state = send_payload(s, payload)

            elif main_menu_choice == '9':
                print("Closing application.")
                break
            else:
                print("Invalid choice. Please try again.")
                continue
    except KeyboardInterrupt:
        print("Ctrl-C pressed. Closing application.")
    finally:
        close_connection(s)


if __name__ == "__main__":
    main()
