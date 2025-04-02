import socket


def main():
    host = '0.0.0.0'
    port = 5001
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    while True:
        client_conn, client_addr = server_socket.accept()
        print(f"Connect34ed by {client_addr}")
        try:
            message = "Hello from server"
            client_conn.send(message.encode())
        except Exception as e:
            print(f"Error sending message: {e}")
        finally:
            client_conn.close()


if __name__ == "__main__":
    main()
