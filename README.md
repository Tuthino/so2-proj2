# so2 - proj2
## Overview
This projects is an chat-app based on a client-server architecture.  
Base project assumptions:  

- Every client connection to the server is handled with it's own thread
- Every read / save of users or messages is done on the file, and it is the only
source of truth, the server does not users / chats state in the variables
- Server keeps synchronization of the threads
- If one of the sides wants to close the connection, it notifies another before closing the socket
- On closing the server application, it needs to notify all active users and close threads.
- There is a wrapper, when user presses `Ctrl-c`, application needs to send information to other side
before closing the socket.
- Users are saved to users.json, and user can chat only with user that is in the database
- If user authenticates with username, that is not in the database, it is automatically created.
- Messages are saved to the messages.json as json
- Client is able to see it's messages with different clients
- Client is able to send a message to other client
- When the user sends a message to online user, he receives the notification about a message 
- No client authentication is required, just username




## Implementation information
### Closing the connection
Both client and sever have wrappers for ctrl-c shortcut, to close the connection
sending packet to another node.  
Server closes all connections and deletes all threads, after deletion, the app shutdown  

There is a `state` variable that indicates if the connection has been closed
If server closed the connection to client, client prints a message that it is not connected to the server.  

### New message notification
If userA wants to send a message to userB and userB is logged in to application, userB will receive
notification about new message.  
It is possible thanks to `listening` thread that checks if there are any responses from server.
The notification is simple, looking like this:
```
*** NEW MESSAGE RECEIVED ***
From: alice, Message: helloo thereee!
```

### Client menu
Client has a simple TUI, when the client starts, it asks user for the username and tries to connect to the server.
If it establishes the connection, user has the following main menu:

```
Logged as: <username>, Main Menu:
1. Show all users
2. Chat with user
9. Close application
```

It can either press `1` to get a list of users, or enter a chat with other user.
After presing `2`, users needs to enter the username with whom to open a chat.
If the other username is not in the database, we go back to the main menu.
If the other username valid, then the following menu appears:

```
Logged as: <username>, Chat with <other_username>:
1. Send message
2. Show all messages
9. Exit chat
```

When choosing `1.` user is asked for the text and message is sent to the server, which appends to the messages.json and notifies the user
When choosing `2.` all messages from the chat are displayed, our messages are on the left, other user messages are on the right.
Width of the terminal is read before showing the messages, to make proper string formatting
Example(formating in readme.md is not the best):

```
Choose an option: 2
Displaying chat messages:
2025-04-07T18:57:28.151163Z alice:
helloo thereee!
                                                                                                             2025-04-07T18:58:50.627035Z bob:
                                                                                                                                 Bye thereeee

```

### Communication
Communication is done via json objects.  
#### Client requests payloads
Every payload has a field `username` and `op` indicating what operation they want to perform.
Possible client operations:

- `show_users`  -- asks for list of users in the app
- `chat_with_user` -- requires additional field `other_username`
- `send_message` -- requires additional field `other_username`, `message`
- `show_messages` -- requires additional field `other_username`
- `exit` -- indicates that we are closing the socket

#### Server responses
Server response with the following format:
```
{
  "res": {
      "status": <response_status>,
      "body": {} -- optional, contains message to the client and additional fields if needed
    }
}
```

When there is an error, the status is always `error`, in other cases, it responds with name of the operation.
Possible status values:

- `error` -- indicates error, the request was not fulfield
- `ok` -- operation succeeded, no need to send body in the response
- `show_messages` -- requires body with messages for the chat
- `show_users` -- requires body with list of users
- `new_message` -- used to notify user about new message for him, requires body with the message







#### Client closes the connection
When client closes the connection, it sends payload `{"op": "exit"}`, closes the socket.
Then server closes the socket as well and terminates the thread for this client

#### Server closes the connection
When server closes the connectin, it sends payload `{"res": {"status": "exit"}}`, closes the socket and terminates the thread.
Client receiving this payload, closes the socket to server 

### Preventing race conditions
#### Server side
Since every client is being served by different thread and our "database" is as a json file, it is crucial to use locks
Every thread shares the same two `threading.Lock()` for users file and for messsages file.
Every operation that could affect state of users or messsages is being executed with `with self.users_lock` `with self.messages_lock`
to make sure that they do not interfere with each other.  
#### Client side
Since there are 2 threads running at the same time, `main` and `listening` additionaly,
`main` after sending the payload cannot continue before `listening` thread receives and processes the response.  
I've used the `threading.Condition()` to make sure this requirements is met.

### How to run
#### Setting the IP and PORT
Both, client and server has the following:
```
    host = os.environ.get('SERVER_HOST', '0.0.0.0')
    port = int(os.environ.get('SERVER_PORT', 5003))
```
meaning that you can either set the IP and port in the code, or use env variable

#### Running the app
We do not to install any requirements, just plain python3.  
To start the server:
`python3 server.py`


To start the client:
`python3 client.py`


