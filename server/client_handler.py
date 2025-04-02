import json
import threading

class ClientHandler(threading.Thread):
    def __init__(self, client_conn, client_addr, active_conns):
        super().__init__()
        self.client_conn = client_conn
        self.client_addr = client_addr
        self.active_conns = active_conns  # Passed from server.py
        self.username = None
        self.chat_id = None # future use 

    def run(self):
        thread_id = threading.get_ident()
        # Register this connection using the passed active_conns dict
        self.active_conns[thread_id] = {
            "username": self.username,
            # "chat_id": self.chat_id
        }
        try:
            data = self.client_conn.recv(1024).decode()
            try:
                info = json.loads(data)
                self.username = info.get("username", "unknown")
                self.chat_id = info.get("chat_id", "unknown")
            except Exception as e:
                print(f"Error decoding JSON: {e}")
            
            # Update the global dictionary information for this thread
            self.active_conns[thread_id]["username"] = self.username
            # self.active_conns[thread_id]["chat_id"] = self.chat_id

            message = f"Hello {self.username}, welcome to the chat!"
            self.client_conn.send(message.encode())
        except Exception as e:
            print(f"Error in connection {self.client_addr}: {e}")
        finally:
            self.client_conn.close()
            del self.active_conns[thread_id]