import json
import threading
import socket
from datetime import datetime
import hashlib

# TODO: make sure that the chats and username are synchronized
# because right now we are reading it only if the variable is empty
# moreover the messages can be overwritten if there are multiple threads
# because they are using the same variable


class ClientHandler(threading.Thread):
    def __init__(self, client_conn, client_addr, active_conns,chats_lock, messages_lock, users_file, msg_file):
        super().__init__()
        self.client_conn = client_conn
        self.client_addr = client_addr
        self.active_conns = active_conns  # Passed from server.py
        self.chats_lock = chats_lock
        self.messages_lock = messages_lock
        self.users_file = users_file
        self.msg_file = msg_file
        self.state = True  # indicates if socket is connected
        self.thread_id = None

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


    def read_messages_for_chatid(self, chat_id):
        # WARNING!!!! we do not lock here.
        # you need to lock the mutex BEFORE calling this function
        with open(self.msg_file, "r") as file:
            data = json.load(file)

        # Find the messages object with the specified chat_id
        chat_entry = next((entry for entry in data if entry.get(
            "chat_id") == chat_id), None)

        if chat_entry:
            # Now chat_entry is a dict and we can use .get('messages') on it
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


    def get_usernames(self):
        # add lock for chats here
        with self.chats_lock:
            with open(self.users_file, 'r') as file:
                users_json = json.load(file)
                # filer usernames
                print(f"chats: {users_json}")
                users = [entry.get("username") for entry in users_json]
                resp = {
                    "res": {
                        "status": "ok",
                        "users": users
                    }
                }
            
            return resp
        
    
    def add_message_for_chatid(self, msg_file, chat_id, payload):
        # reads the messages from file (if needed), finds the chat entry for chat_id,
        # appends new_message, then persists the updated messages back to the file.
        with self.messages_lock:
            # If there are no messages loaded yet, load from file
            # however this should never take place 
            messages = []
            try:
                with open(msg_file, "r") as file:
                    messages = json.load(file)
            except Exception as e:
                print(f"Error reading messages file: {e}")
                return

            # find the chat entry for the given chat_id, create one if not found
            # however the chat should be already created when we enter the chat with other user
            # TODO: check if this is needed
            chat_entry = next((entry for entry in messages if entry.get("chat_id") == chat_id), None)
            if chat_entry is None:
                chat_entry = {"chat_id": chat_id, "messages": []}
                messages.append(chat_entry)

            # append the new message; 
            chat_entry["messages"].append({
                "sender": payload.get("username"), 
                "text": payload.get("message"), 
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })

            # Write the updated messages back to the file
            try:
                with open(msg_file, "w") as file:
                    json.dump(messages, file, indent=4)
                response = {
                    "res": {
                        "status": "ok",
                        "message": "Message appended successfully."
                    }
                }
                self.send_response(response)
            except Exception as e:
                response = {
                    "res": {
                        "status": "error",
                        "message": f"Failed to update messages file: "
                    }
                }
                print(f"Error writing messages file: {e}")
                self.send_response(response)

    def connect_user(self, username, users_file="users.json"):
        # here we need to check if the user is already connected
        # if yes, then we need to send a message to the client
        # only one user is able to connect at a time
        # which in real chat app would be stupid
        if username in self.active_conns:
            response = {
                "res": {
                    "status": "error",
                    "message": f"User {username} is already connected."
                }
            }
            self.send_response(response)
            return False
        else:
            # check if the username exists in the chats file
            # if not, then we need to create a new entry for the user
            with self.chats_lock:
                with open(self.users_file, 'r') as file:
                    users_json = json.load(file)
                    users_exists = any(user.get("username") == username for user in users_json)
                    if users_exists:
                        pass
                        resp = {
                            "res": {
                                "status": "ok",
                            }
                        }
                        self.send_response(resp)
                    else:
                        # create a new entry for the user
                        new_user = {
                            "username": username,
                        }
                        users_json.append(new_user)
                        print('user appended')

                        # write the new user to the file
                        with open("users.json", "w") as file:
                            json.dump(users_json, file, indent=4)
                        resp = {
                            "res": {
                                "status": "ok",
                            }
                        }
                        self.send_response(resp)
                        print(f"New user {username} created.")
            return True

    def calculate_chat_id(self, username, other_username):
        # i know this is not the best way, but I do not want to add more files
        # or duplicate the data in chats.json
        # sort the usernames to ensure the order is fixed (so "alice" with "bob" equals "bob" with "alice")
        users = sorted([username.lower(), other_username.lower()])
        combined = f"{users[0]}-{users[1]}"
        # create a sha256 hash of the combined string
        hash_obj = hashlib.sha256(combined.encode())
        chat_id = hash_obj.hexdigest()
        return chat_id

    def process_payload(self, payload):
        # process the payload, activate needed functions and locks
        # return response to the client
        print(f"process payload: {payload}")

        if payload.get("op") == "connect":
            if  payload.get("username") is not None:
                self.connect_user(payload.get("username"))
            else:
                response = {
                    "res": {
                        "status": "error",
                        "message": "Username not provided."
                    }
                }
                self.send_response(response)
                return

        if payload.get("op") == "show_users":
            # send all users to the client
            resp = self.get_usernames()
            print(f"Client {self.client_addr} requested to show users.")
            self.send_response(resp)



        elif payload.get("op") == "chat_with_user":
            # the only check here we need is to check if other_username exists in users.json
            users = self.get_usernames().get("res").get("users")
            other_username = payload.get("other_username")
            if payload.get("other_username") not in users:
                resp = {
                    "res": {
                        "status": "error",
                        "message": f"Username with {other_username} not found."
                    }
                }
                self.send_response(resp)
                return
            else: 
                print(f"Username  {other_username} found, sending confirmation")
                resp = {
                    "res": {
                        "status": "ok",
                        "message": f"Username with {other_username}  found."
                    }
                }
                self.send_response(resp)

        elif payload.get("op") == "show_messages":
            # get and send all messages for the current user
            username = payload.get("username")
            other_username = payload.get("other_username")

            chat_id = self.calculate_chat_id(username, other_username)
            resp = self.read_messages_for_chatid(chat_id)
            if resp is not None:
                self.send_response(resp)
            else:
                pass

        elif payload.get("op") == "send_message":
            # here we need to add the message to the file
            # we do not actually send the message to the other user yet
            # maybe TODO: later

            # check if the chat_id exists
            # if the other_username matches, then we already have the chat_id
            username = payload.get("username")
            other_username = payload.get("other_username")

            chat_id = self.calculate_chat_id(username, other_username)
            users = self.get_usernames().get("res").get("users")
            if payload.get("other_username") not in users:
                resp = {
                    "res": {
                        "status": "error",
                        "message": f"Username with {other_username} not found."
                    }
                }
                self.send_response(resp)
                return
            else:
                # here we need to add the message to the file
                self.add_message_for_chatid("messages.json", chat_id, payload)
        
        print(f"Client {self.client_addr} sent invalid payload: {payload}")
        return







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
                    if not self.state:
                        return
                    data = self.client_conn.recv(1024).decode()
                    # here the connection is established and client send the payload
                    payload = json.loads(data)
                    print(f"thread {thread_id} Received data from {
                          self.client_addr}: {payload}")
                    if payload.get("op") == "exit":
                        print(f"Client {self.client_addr} requested to exit.")
                        return
                    print(payload)
                    self.process_payload(payload)
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
                self.send_response(error_response)
            except Exception:
                pass
            print(f"Error in connection {self.client_addr}: {e}")
        finally:
            print(f"Thread {thread_id} finally block.")
            if self.thread_id in self.active_conns:
                self.close_connection()
                del self.active_conns[thread_id]
                print(f"Thread {thread_id}: Connection closed.")
