import socket
from threading import Thread

# global hash-table to store the TOSEND and TORECV sockets
toSendSockets = {}
toRecvSockets = {}

# thread specially used at the time of broadcasting
class BroadcastThread(Thread):
    def __init__(self, sender, socket, packet):
        Thread.__init__(self)
        self.sender = sender
        self.mySocket = socket
        self.packet = packet
        self.success = False
    # main function called at time of broadcasting
    def run(self):
        self.mySocket.send(bytes(self.packet, 'utf-8'))
        responseFromRecipient = self.mySocket.recv(1024).decode('utf-8')
        if(responseFromRecipient == "RECEIVED {0}\n\n".format(self.sender)):
            self.success = True
        return

# class for threads created for each TORECV and TOSEND sockets
class ServerThread(Thread):
    def __init__(self, mySocket):
        Thread.__init__(self)
        self.mySocket = mySocket
        self.username = ""
        self.registered = False

    # check if the msg received is a valid registration request
    def isRegistrationRequest(self,msg):
        temp = msg.strip().split()
        if(len(temp)<3):
            return False
        if(temp[0] == "REGISTER" and (temp[1] == "TOSEND" or temp[1] == "TORECV") and len(temp[2])>=1):
            return True
        else:
            return False

    # check if the username is valid
    def chkValidUsrName(self,usr):
        if(usr == "ALL"):
            return False
        for i in range(len(usr)):
            if(not((usr[i]>='0' and usr[i]<='9') or (usr[i]>='a' and usr[i]<='z') or (usr[i]>='A' and usr[i]<='Z'))):
                return False
        return True

    # extract information from packets received
    def getUser(self,packet):
        temp =  packet.strip().split()
        usr = temp[2]
        correctUsrName = self.chkValidUsrName(usr)
        return (correctUsrName, temp[2], temp[1])

    # check if the packet received is well-formed
    def checkError103(self, msg):
        temp = msg.strip().split('\n')
        if(len(temp)<4):
            return False
        l = temp[0].strip().split()
        if(not(len(l)==2 and l[0]=="SEND") or len(temp[1])<17):
            return False
        if(not(temp[1][:15] == "Content-length:" and temp[1][16:] == str(len(temp[3].strip())))):
            return False
        return True
    
    # function used to broadcast msg to all the clients
    def broadcast(self, packet):
        lThread = []
        broadcasted = True
        for recipient in toRecvSockets:
            if(recipient == self.username):
                continue
            broadcastThread = BroadcastThread(self.username, toRecvSockets[recipient], packet)
            broadcastThread.start()
            lThread.append(broadcastThread)
        for th in lThread:
            th.join()
            if(th.success == False):
                broadcasted = False
        return broadcasted

    # main function called when the execution of the thread starts
    def run(self):
        # registration of the client
        while(not(self.registered)):
            data = self.mySocket.recv(1024)

            if not data:
                self.mySocket.close()
                return
            data = data.decode('utf-8')
            # valid registration request
            if(self.isRegistrationRequest(data)):
                correctUsrName, userName, connType = self.getUser(data)
                # invalid user name - return error 100
                if(correctUsrName == False):
                    msg = "ERROR 100 Malformed username\n\n"
                    print(data)
                    print("\n")
                    self.mySocket.send(bytes(msg, 'utf-8'))
                    self.mySocket.close()
                    return
                # valid registration request for TOSEND socket
                elif(connType == 'TOSEND'):
                    toSendSockets[userName] = mySocket
                    print(data)
                    print("\n")
                    msg = "REGISTERED TOSEND {0}\n\n".format(userName)
                    self.mySocket.send(bytes(msg, 'utf-8'))
                    self.registered = True
                    self.username = userName
                # valid registration request for TORECV socket
                elif(connType == 'TORECV'):
                    toRecvSockets[userName] = mySocket
                    print(data)
                    print("\n")
                    msg = "REGISTERED TORECV {0}\n\n".format(userName)
                    self.mySocket.send(bytes(msg, 'utf-8'))
                    self.registered = True
                    self.username = userName
                    return
            # trying to communicate before registering
            else:
                print(data)
                print("\n")
                msg = "ERROR 101 No user registered\n\n"
                mySocket.send(bytes(msg, 'utf-8'))

        # registration completed ... waiting for messages
        while True:
            try:
                data = self.mySocket.recv(1024)
                t = data.decode('utf-8')
                #client left
                if not data:
                    self.mySocket.close()
                    toRecvSockets[self.username].close()
                    toSendSockets.pop(self.username)
                    toRecvSockets.pop(self.username)
                    print("{0} LEFT".format(self.username))
                    print("\n")
                    return
                # check if the packet received is well-formed
                flag = self.checkError103(t)
                print(t)
                print("\n")
                if(flag == False):
                    forSender = "ERROR 103 Header Incomplete\n\n"
                    self.mySocket.send(bytes(forSender, 'utf-8'))
                    self.mySocket.close()
                    toRecvSockets[self.username].close()
                    toSendSockets.pop(self.username)
                    toRecvSockets.pop(self.username)
                    return

                temp = t.strip().split('\n')
                msgType, recipient = temp[0].strip().split()
                
                # check if the username is valid
                if(not(recipient == "ALL") and (recipient not in toRecvSockets.keys())):
                    forSender = "ERROR 102 Unable to send\n\n"
                    self.mySocket.send(bytes(forSender, 'utf-8'))
                    continue
                header = temp[1]
                msg = temp[3]

                # if client requested for broadcasting
                if(recipient == "ALL"):
                    packet = "FORWARD {0}\n{1}\n\n{2}".format(self.username, header, msg)
                    success = self.broadcast(packet)
                    if(success):
                        forSender = "SENT ALL\n\n"
                        self.mySocket.send(bytes(forSender, 'utf-8'))
                    else:
                        forSender = "ERROR 102 Unable to send\n\n"
                        self.mySocket.send(bytes(forSender, 'utf-8'))
                    continue
                
                # request to send msg to a particular recipient
                if(msgType == 'SEND'):
                    recvSocket = toRecvSockets[recipient]
                    packet = "FORWARD {0}\n{1}\n\n{2}".format(self.username, header, msg)

                    #########################
                    #instead send the below ill-formed messages to get error 103 from recipient
                    #packet = "FORWARD {0}\n{1}\n\n{2}".format(self.username, "Content-length: 10", msg)
                    #packet = "how are you"
                    
                    recvSocket.send(bytes(packet, 'utf-8'))
                    responseFromRecipient = recvSocket.recv(1024).decode('utf-8')
                    #successfully sent
                    print(responseFromRecipient)
                    print("\n")
                    if(responseFromRecipient == "RECEIVED {0}\n\n".format(self.username)):
                        forSender = "SENT {0}\n\n".format(recipient)
                        self.mySocket.send(bytes(forSender, 'utf-8'))
                    # error 103 found
                    else:
                        forSender = "ERROR 103 Header Incomplete\n\n"
                        self.mySocket.send(bytes(forSender, 'utf-8'))
                        self.mySocket.close()
                        toRecvSockets[self.username].close()
                        toSendSockets.pop(self.username)
                        toRecvSockets.pop(self.username)
                        return
            except socket.error as e:
                # need to close this socket and thread as well
                self.mySocket.close()
                toRecvSockets[self.username].close()
                toSendSockets.pop(self.username)
                toRecvSockets.pop(self.username)
                print("{0} LEFT".format(self.username))
                print("\n")
                return
                

# create socket
serverSocket = socket.socket()
serverSocket.bind(('127.0.0.1', 2000))


# listening for clients and creating threads for registration
while True:
    serverSocket.listen()
    mySocket, clientSocket = serverSocket.accept()
    serverThread = ServerThread(mySocket)
    serverThread.start()
    
    
    




