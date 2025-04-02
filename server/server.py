import socket
import json


# TODO: reading and saving  data from chats.json to some struct // read done
# reading and saving  data from messages.json to some struct // read done
# maybe overwrite the ctrl-c for graceful shutdown with sving data, or some other kill number
# create a logic for handling the user connection (username could be in the thread variable)
# create thread for every connectino to the server
# sending all messages to the client from the chat
# all data needs to be received, sent and saved as json

# TODO: OPTIONAL perform saving procedure after X seconds/minutes or call

# possible input for messages: username, chat-id, message


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


def test_main():
    chats_file = 'chats.json'
    msg_file = 'messages.json'
    chats = read_chats(chats_file)

    # filered entries for username
    filtered_entries = [entry for entry in chats if entry.get(
        "username") == 'alice']  # this creates a list
    # to have a json from the list:
    f_json = json.dumps(filtered_entries, indent=4)

    # to filter a json and still have a json
    user_entry = next((user for user in filtered_entries if user.get(
        "username") == 'alice'), None)

    print(chats)
    print(f"alice's chats {user_entry.get('chats')}")
    print(read_messages(msg_file, 'cshat123'))


if __name__ == "__main__":
    # main()
    test_main()
