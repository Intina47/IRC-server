import platform
import socket
from threading import Thread

# Global variables, used to store the server's IP address and port number
# socket creation
serversocket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
host = ""
port = 6667
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    # Bind the socket to the host and port
    serversocket.bind((host, port))
    if platform.system() == "Windows":
        print("Server started on Windows")
    elif platform.system() == "Linux":
        print("Server started on Linux")
    elif platform.system() == "Darwin":
        print("Server started on Mac")
    else:
        print("Server started on unknown OS")
except socket.error as e:
    print(e)

client_list = []
channel_list = []



# The client class that handles the client's connection

class client(Thread):
    # Constructor for the client class
    def __init__(self, socket, address):
        Thread.__init__(self)
        self.sock = socket
        self.addr = address
        self.nickname = ""
        self.username = ""
        self.channel = []
        self.start()

    """
       The function checks if the nickname is admin, if it is, it asks for a password. If the password
        is correct, it sets the nickname to admin. If the password is incorrect, it sends an error
        message. If the nickname is not admin, it checks if the nickname is already in use. If it is, it
        sends an error message. If it is not, it sets the nickname to the nickname the user entered

        :return: the client object.
        """

    def join_server(self):

        # While username and nickname not set
        while self.nickname == "" and self.username == "":
            while self.username == "":
                # Read received data from the client
                message = self.sock.recv(1024).decode()
                for line in message.splitlines():
                    messageParsed = line.split(' ')
                    # Check if the client is sending a nickname parameter to the server
                    if (messageParsed[0] == "NICK"):
                        global client_list
                        if (messageParsed[1] != ""):
                            # if the nickname is admin, ask for password
                            if messageParsed[1] == "admin":
                                self.sock.send(b'Password: ')
                                # nb: 2**10 is the max size of a message
                                password = self.sock.recv(1024).decode()
                                if password == "admin":
                                    self.nickname = messageParsed[1]
                                elif password == "admin" and messageParsed[1] in client_list:
                                    self.sock.send(
                                        b'Nickname is already in use')
                                    self.sock.close()
                                    return
                                else:
                                    self.sock.send(b'Incorrect password')

                            for client in client_list:
                                # inform user if the nickname already exist
                                if messageParsed[1] == client.nickname:
                                    message = self.nickname + ' ' + \
                                        messageParsed[1] + \
                                        ':Nickname is already in exists\n'
                                    self.sock.send(message.encode())
                                    self.sock.close()
                                    return
                            self.nickname = messageParsed[1]
                        else:
                            self.sock.send(b'Error: Please enter a nickname')

                    # Check if the client is sending a username parameter
                    if (messageParsed[0] == "USER"):
                        if (messageParsed[1] != ""):
                            self.username = messageParsed[1]
                        elif (messageParsed[1] == client.username):
                            self.sock.send(b'Username is already in use')
                            self.sock.close()
                            return
                        else:
                            self.sock.send(b'Error: Please enter a username')

        print(self.username + " has joined the server" +
              " with the nickname " + self.nickname)
        if (self.nickname != "" and self.username != ""):
            print("Adding " + self.username + " to client list...")
            try:
                client_list.append(self)
                print("Client list updated")
            except:
                print("Error: Could not add client to client list")

            # Constructing and sending the initial welcome messages
            msg1 = ':' + host + ' 001 ' + self.nickname + ' :Welcome to Group_10 server!\n'
            message = msg1 + "Join test by typing /join #test\n"

            self.sock.send(message.encode())

    """
    The function checks if the channel is already in the list of channels. If it's not it adds it to the channel list
    it then broadcasts a message to all the clients in the channel that the user has joined the channel

    :param messageParsed: the message that the user sent to the server
    :param line: the message of the channel user wants to join
    """

    def join_channel(self, messageParsed, line):

        found = False
        for channel in channel_list:
            
            if (messageParsed[1] == channel):
                found = True
        channel = messageParsed[1]
        # If channel not found, create channel with name
        if (not found):
            channel_list.append(channel)
            found = True

            # If channel found, send reply codes and broadcast to everyone in channel
        if (found):
            # 200 and 300 are reply codes,to inform the user which commands were executed
            self.channel.append(channel)
            chmsg1 = ':' + host + ' 200 ' + self.nickname + \
                ' ' + channel + ' :No topic is set\n'
            chmsg2 = ':' + host + ' 300 ' + self.nickname + 'Users in ' + channel + ' :'
            inforserver = "NICK: " + self.nickname + " USERNAME: " + self.username + \
                ' @ ' + self.addr[0] + '\n' + \
                platform.node() + ' JOINED ' + channel + '\n'

            # Add every client in channel to list of users in channel
            for client in client_list:
                for clientChannel in client.channel:
                    if (clientChannel == channel):
                        chmsg2 = chmsg2 + ' ' + client.nickname
            chmsg2 = chmsg2 + '\n'

            # Send channel reply codes
            chan_list = ':' + host + ' 366 ' + self.nickname + \
                ' ' + channel + ' :End of NAMES list\n'
            REPLY = ':' + self.nickname + "!" + self.username + \
                '@' + platform.node() + ' ' + line + '\n'
            message = REPLY + chmsg1 + chmsg2 + chan_list
            servermsg = inforserver + chmsg1 + chmsg2
            print(servermsg)

            # send a message to clients in the channel
            for client in client_list:
                for clientChannel in client.channel:
                    if (clientChannel == channel):
                        client.sock.send(message.encode())

    """
        It sends a message to all the clients in the channel that the user left, and then removes the
        channel from the user's channel list
        
        :param messageParsed: the raw message by the clint
        :param line: each line of the raw message to be parsed
        """

    def leave_channel(self, messageParsed, line):

        if (self.channel):
            channel = messageParsed[1]
            message = ':' + self.nickname + "!" + self.username + \
                '@' + platform.node() + ' ' + line + '\n'
            # For each client in channel, send message that user left
            for client in client_list:
                for clientChannel in client.channel:
                    if (clientChannel == channel):
                        client.sock.send(message.encode())
            # Remove channel frm users channel list
            self.channel.remove(channel)
            print(self.nickname + " left " + channel)

    """
        The function sends a message to all clients that the user has quit, removes the user from the
        list of clients, and then closes the socket
        
        :param messageParsed: the message that the client sent to the server
        :param line: each line of the raw message to be parsed
    """

    def quit_channel(self, messageParsed, line):

        # For each client, send message that user has quit
        for client in client_list:
            message = ':' + self.nickname + "!" + self.username + \
                '@' + platform.node() + ' ' + line + '\n'
            client.sock.send(message.encode())
        # Remove user from list of clients and then close the socket
        client_list.remove(self)
        print(self.nickname + " has quit")
        self.sock.close()

    """
        If the user is an admin, then kick the user from the channel.
        
        :param messageParsed: the message that was sent to the server
        :param line: each line of the raw message to be parsed
        """
    def kick_user(self, messageParsed, line):
        
        if (self.username == "admin"):
            channel = messageParsed[1]
            for client in client_list:
                if (messageParsed[2] == client.nickname):
                    message = ':' + self.nickname + "!" + self.username + \
                        '@' + platform.node() + ' ' + line + '\n'
                    client.sock.send(message.encode())
                    print(self.nickname + " kicked " +
                          client.nickname + " from " + channel)
                    client.channel.remove(channel)
             # inform all users in channel that user was kicked
            for client in client_list:
                for clientChannel in client.channel:
                    if (clientChannel == channel):
                        message = ':' + self.nickname + "!" + self.username + \
                            '@' + platform.node() + ' ' + line + '\n'
                        client.sock.send(message.encode())
        else:
            message = ':' + host + ' 481 ' + self.nickname + \
                ' :Permission Denied- You do not have access to this command\n'
            self.sock.send(message.encode())


    """
        It sends a private message to a user if the user is in the same channel as the sender.
        
        :param messageParsed: the message that was sent to the server
        :param line: each line of the raw message to be parsed
        """
    def private_message(self, messageParsed, line):
        
        channel = messageParsed[1]
        for client in client_list:

            # Message Channel
            for clientChannel in client.channel:
                if (clientChannel == channel):
                    if (client != self):
                        message = ':' + self.nickname + "!" + self.username + \
                            '@' + platform.node() + ' ' + line + '\n'
                        client.sock.send(message.encode())

            # Message Users privately
             # correctly formats to send a private message to a user is correct format is /msg <nickname> <message>
            if (messageParsed[1] == client.nickname ) or (messageParsed[1]==client.username):
                if (messageParsed[2] != ":"):
                    if (messageParsed[1] != self.nickname) or (messageParsed[1] != self.username):
                        # Send message to user
                        message = ':' + self.nickname + "!" + self.username + \
                            '@' + platform.node() + ' ' + line + '\n'
                        client.sock.send(message.encode())
                        print(self.nickname +
                              " sent a private message to " + client.nickname)

        
        """
        It takes a list of clients, and for each client, it checks if the client is in the channel, and
        if so, it adds the client's nickname to the message
        
        :param messageParsed: The message that was sent to the server
        """
    def list_names(self, messageParsed):
       
        channel = messageParsed[1]
        message = ':' + host + ' 353 ' + self.nickname + ' = ' + channel + ' :'
        for client in client_list:
            for clientChannel in client.channel:
                if (clientChannel != channel):
                    message = "Join channel to see users!"
                if (clientChannel == channel):
                    message = message + client.nickname + ' '
        message = message + '\n' + ':' + host + ' 366 ' + \
            self.nickname + ' ' + channel + ' :End of NAMES list\n'
        print(self.nickname +
              " requested a list of users in " + channel)
        self.sock.send(message.encode())



    """
        The function runs the client's thread and ensures that all login information is received before
        continuing
        """
    def run(self):
        
        # ensure that all login information is received before continuing
        try:
            self.join_server()
            while True:

                message = self.sock.recv(1024).decode()
                for line in message.splitlines():
                    messageParsed = line.split(' ')

                  

                    if (messageParsed[0] == "JOIN"):
                        self.join_channel(messageParsed, line)

                        # Leave channel protocol
                    if (messageParsed[0] == "PART"):
                        self.leave_channel(messageParsed, line)

                        # Leave server
                    if (messageParsed[0] == "QUIT"):
                        self.quit_channel(messageParsed, line)
                        continue

                    # Message protocol
                    if (messageParsed[0] == "PRIVMSG"):
                        self.private_message(messageParsed, line)
                        # List all users in channel
                    if (messageParsed[0] == "NAMES"):
                        self.list_names(messageParsed)

                        # user priviledges protocol
                    if (messageParsed[0] == "KICK"):
                        self.kick_user(messageParsed, line)

        except:
            for client in client_list:
                if client == self:
                    client_list.remove(client)

            self.sock.close()


# Listen for client connections to server
serversocket.listen(5)
print("Server is running and listening on port " + str(port))

while True:
    try:
        clientsocket, address = serversocket.accept()
        client(clientsocket, address)
    except KeyboardInterrupt:
        print("Server is shutting down")
        serversocket.close()
        break
