import socket
import os 
import threading
from client_handler import ClientHandler


# TODO: reading and saving  data from chats.json to some struct // read done
# reading and saving  data from messages.json to some struct // read done
# maybe overwrite the ctrl-c for graceful shutdown with sving data, or some other kill number /done
# create a logic for handling the user connection (username could be in the thread variable) /done
# create thread for every connectino to the server /done
# sending all messages to the client from the chat /missing automatic synchro
# all data needs to be received, sent and saved as json /done

# TODO: OPTIONAL perform saving procedure after X seconds/minutes or call

# possible input for messages: username, chat-id, message


# global variables
# it is a list, under the active_conns[thread_id] we have the ClientHandler
active_conns = {}
# create locks for chats and messages
chats_lock = threading.Lock()
messages_lock = threading.Lock()
chats_file = 'users.json'
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
                chats_lock, messages_lock, chats_file, msg_file)
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
    # test_main()

# def test_main():
#     chats_file = 'chats.json'
#     msg_file = 'messages.json'
#     # chats = read_chats(chats_file)

#     # filered entries for username
#     filtered_entries = [entry for entry in chats if entry.get(
#         "username") == 'alice']  # this creates a list
#     # to have a json from the list:
#     f_json = json.dumps(filtered_entries, indent=4)

#     # to filter a json and still have a json
#     user_entry = next((user for user in filtered_entries if user.get(
#         "username") == 'alice'), None)

#     print(chats)
#     print(f"alice's chats {user_entry.get('chats')}")
#     print(read_messages(msg_file, 'cshat123'))

