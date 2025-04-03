import json
import threading
import socket


class ClientHandler(threading.Thread):
    def __init__(self, client_conn, client_addr, active_conns):
        super().__init__()
        self.client_conn = client_conn
        self.client_addr = client_addr
        self.active_conns = active_conns  # Passed from server.py
        self.username = None
        self.state = True  # indicates if socket is connected
        self.thread_id = None
        self.chat_id = None  # future use

    def close_connection(self):
        # however the client does not yet process this exit payload
        # im trying to check if the socket is still open
        # by sending empty payload
        try:
            response = {
                "res": {
                    "status": "exit",
                }
            }
            self.send_response(response)
            self.client_conn.close()
            self.state = False
            print(f"Connection closed with {self.client_addr}")
        except Exception as e:
            print(f"Error closing connection: {e}")

    def send_response(self, response):
        try:
            self.client_conn.send(json.dumps(response).encode())
            print(f"Sent response: {response}")
        except Exception as e:
            print(f"Failed to send response: {e}")

    def read_chats(chat_file):
        '''
        holds username and their chats
        new user gets created an empty "chats": []
        example file
        [
        {
            "username": "alice",
            "chats": [
                {
                    "chat_id": "chat123",
                    "other_username": "bob"
                },
                {
                    "chat_id": "chat456",
                    "other_username": "charlie"
                }
            ]
        },
        {
            "username": "bob",
            "chats": [
                {
                    "chat_id": "chat123",
                    "other_username": "alice"
                },
                {
                    "chat_id": "chat789",
                    "other_username": "david"
                }
            ]
        }
        ]
        '''

        with open(chat_file, 'r') as file:
            data = json.load(file)

        return data

    def read_messages(msg_file, chat_id):
        '''
        here we have only the chat_id and it's messages with
        sender, text, timestamp



        example entries:
        [
            {
            "chat_id": "chat123",
            "messages": [
                {
                    "sender": "alice",
                    "text": "Hello, Bob!",
                    "timestamp": "2025-04-02T12:00:00Z"
                },
                {
                    "sender": "bob",
                    "text": "Hi, Alice! How are you?",
                    "timestamp": "2025-04-02T12:00:05Z"
                },
                {
                    "sender": "alice",
                    "text": "I'm good, thanks. What about you?",
                    "timestamp": "2025-04-02T12:00:10Z"
                }
                ]
            }
        ]

        '''
        with open("messages.json", "r") as file:
            data = json.load(file)

        # Find the messages object with the specified chat_id
        chat_entry = next((entry for entry in data if entry.get(
            "chat_id") == chat_id), None)

        if chat_entry:
            # Now chat_entry is a dict and you can use .get('messages') on it
            messages = chat_entry.get("messages")
            result = {
                "chat_id": chat_id,
                "messages": messages
            }
        else:
            result = {
                "error": f"No chat found with chat_id {chat_id}"
            }
        return result

    def run(self):
        thread_id = threading.get_ident()
        # regitser this handler to active_conns
        self.thread_id = thread_id
        self.active_conns[thread_id] = self
        self.client_conn.settimeout(1.0)
        try:
            # this loop is needed to keep the connection open until
            # client send payload 'op': 'exit'
            while self.state:

                try:
                    if self.state:
                        return
                    data = self.client_conn.recv(1024).decode()
                    # here the connection is established and client send the payload
                    info = json.loads(data)
                    self.username = info.get("username", "unknown")
                    self.chat_id = info.get("chat_id", "unknown")
                    print(f"thread {thread_id} Received data from {
                          self.client_addr}: {info}")
                    if info.get("op") == "exit":
                        print(f"Client {self.client_addr} requested to exit.")
                        return
                except socket.timeout:
                    # Timeout happened, check if we should exit immediately.
                    continue
                except Exception as e:
                    # error in decoding the json
                    error_response = {
                        "res": {
                            "status": "error",
                            "message": f"Error decoding JSON: {e}"
                        }
                    }
                    # if the state is False, the conn is closed, do not send
                    if self.state:
                        print(f"{thread_id} sending to client {
                              self.client_conn} error response {error_response}")
                        self.send_response(error_response)
                    return

                # client payload received and decoded with success
                response = {
                    "res": {
                        "status": "ok",
                        "message": f"Hello {self.username}, welcome to the chat!"
                    }
                }
                self.send_response(response)

        except Exception as e:
            # connection error
            error_response = {
                "res": {
                    "status": "error",
                    "message": f"Error in connection: {e}"
                }
            }
            try:
                # I am not sure if this will work since the connection
                # might be closed or broken
                self.send_response(response)
            except Exception:
                pass
            print(f"Error in connection {self.client_addr}: {e}")
        finally:
            print(f"Thread {thread_id} finally block.")
            if self.thread_id in self.active_conns:
                self.close_connection()
