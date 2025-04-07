import socket
import os
import threading
from client_handler import ClientHandler

# global variables
# it is a list, under the active_conns[thread_id] we have the ClientHandler
active_conns = {}
# create locks for chats and messages
users_lock = threading.Lock()
messages_lock = threading.Lock()
users_file = 'users.json'
msg_file = 'messages.json'


def main():
    host = os.environ.get('SERVER_HOST', '0.0.0.0')
    port = int(os.environ.get('SERVER_PORT', 5003))
    print(f"Server host: {host}, port: {port}")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    try:
        while True:
            client_conn, client_addr = server_socket.accept()
            print(f"Connected by {client_addr}")
            client_thread = ClientHandler(
                client_conn, client_addr, active_conns,
                users_lock, messages_lock, users_file, msg_file)
            client_thread.start()
    except KeyboardInterrupt:
        print("Server shutting down...")
    finally:
        # close all connections and delete threads
        for thread_id, handler in list(active_conns.items()):
            handler.close_connection()
            del active_conns[thread_id]
            handler.join()
            print(f"Thread {thread_id}: Connection closed.")
        server_socket.close()
        print("Server socket closed.")


if __name__ == "__main__":
    main()
