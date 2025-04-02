import os
import socket
import time
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


def main():

    print('1Sleeping to wait for server initialization')
    time.sleep(2)
    server_host = os.environ.get('SERVER_HOST', 'localhost')
    server_port = 5001

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_host, server_port))
    message = client_socket.recv(1024)
    print("Received:", message.decode())
    client_socket.close()


if __name__ == "__main__":
    print('Sleeping to wait for server initialization')
    time.sleep(1)
    main()
