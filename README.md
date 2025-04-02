# so2 - proj2
## Overview
This projects is an chat-app based on a client-server architecture.  
Base project assumptions:  

- Every client connection to the server is handled with it's own thread
- Server keeps synchronization of the threads
- Messages are saved to the chat.json as json
- On every server bootup, the messages are loaded
- Client is able to see it's messages with different clients
- Client is able to send a message to other client
- Client needs to receive new messsages



## Before start
Both clients and server are as a docker container, run by docker-compose.  
Change in the directory is immediately reflected in the container,  
Because the folders are mounted to the container (the same is with  
changes inside the container, they are reflected on your file system).  
There are no security constraints on the mounting, as this is only for develop.  

## How to run
To spin up the containers, simply run (for first run, add --build):  
```
docker-compose up
```
### How to run only the client
If your server is already running and you want to spin up client once again, run:  
```
docker-compose up client
```


### How to restart python process
Because the python process is not being run directly (there is run.sh wrapper),  
You can restart the process without need to restart the container.
Kill the process (where the <PID> is taken from the first container output, usually it is 9):  
```
# if want to restart the server
docker-compose exec  server kill -USR1 <PID>

# if want to restart the client
docker-compose exec  client kill -USR1 <PID>
```

However, keep in mind, because of how TCP works, the socket needs 60s before closing,  
and you cannot reuse it before, therefore for quick reloads, you can change the port.
