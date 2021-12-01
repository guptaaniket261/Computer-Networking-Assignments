import socket
from threading import Thread


# thread class for sending messages to other clients
class cliSendingThread(Thread):
    def __init__(self, mySocket, username):
        Thread.__init__(self)
        self.mySocket = mySocket
        self.username = username

    # function at the sender client side to check the format of message being sent
    def parse(self, msg):
        temp = msg.strip().split()
        flag = False
        if (len(temp)<2):
            return (flag, "", "")
        if(len(temp[0])<2 or not(temp[0][0] == '@')):
            return (flag, "", "")
        mesg = ""
        for i in range(1, len(temp)):
            if(not(mesg == "")):
                mesg += " "
            mesg += temp[i]
        return (True, temp[0][1:], mesg)

    # function called when the thread starts executing
    def run(self):
        while True:
            try:
                # take input msg from user
                msg = input()
                # process the msg at the sender side 
                flag, recipient, msg = self.parse(msg)
                if(flag == False):
                    print("INVALID MESSAGE FORMAT... TRY AGAIN...")
                    print("\n")
                    continue
                # create the packet for the message being sent
                packet = "SEND {0}\nContent-length: {1}\n\n{2}".format(recipient,len(msg.encode('utf-8')), msg)
                
                ###################################
                # instead send this packet to see an example of ERROR 103
                #packet = "SEND {0}\nContent-length: {1}\n\n{2}".format(recipient,4, msg)
                #################################

                self.mySocket.send(bytes(packet, 'utf-8'))

                # waiting for response
                response = self.mySocket.recv(1024)
                if(response.decode('utf-8') == "ERROR 103 Header Incomplete\n\n"):
                    print(response.decode('utf-8'))
                    self.mySocket.close()
                    print("Closing TOSEND socket")
                    print("\n")
                    return
                print(response.decode('utf-8'))
                
            except socket.error as e:
                self.mySocket.close()
                print("LOST CONNECTION...tosend")
                print("\n")
                return
            except EOFError as e1:
                self.mySocket.close()
                print("Leaving...")
                print("\n")
                exit(0)
            

# thread class for receiving messages at the recipient client
class cliReceivingThread(Thread):
    def __init__(self, mySocket, username):
        Thread.__init__(self)
        self.mySocket = mySocket
        self.username = username

    # analysing the packet received for error
    def checkError103(self, msg):
        temp = msg.strip().split('\n')
        if(len(temp)<4):
            return False
        l = temp[0].strip().split()
        if(not(len(l)==2 and l[0]=="FORWARD") or len(temp[1])<17):
            return False
        if(not(temp[1][:15] == "Content-length:" and temp[1][16:] == str(len(temp[3].strip())))):
            return False
        return True

    # main function called when recieve thread starts executing
    def run(self):
        while True:
            try:
                data = self.mySocket.recv(1024)
                #closing the socket in case of error
                if not data:
                    self.mySocket.close()
                    print("Closing TORECV Socket")
                    print("\n")
                    return
                t = data.decode('utf-8')

                # check that the packet is well-formed
                flag = self.checkError103(t)
                # errorenous packet received
                if(flag == False):
                    print(data.decode('utf-8'))
                    print("\n\n")
                    packet = "ERROR 103 Header Incomplete\n\n"
                    self.mySocket.send(bytes(packet, 'utf-8'))
                    continue
                
                temp = t.strip().split('\n')
                msgType, sender = temp[0].strip().split()
                header = temp[1]
                msg = temp[3]
                print(data.decode('utf-8'))
                print("\n\n")
                # send response for the packet received
                packet = "RECEIVED {0}\n\n".format(sender)
                self.mySocket.send(bytes(packet, 'utf-8'))
            except socket.error as e:
                self.mySocket.close()
                print("LOST CONNECTION...torecv")
                print("\n")
                return

# function to create TOSEND socket
def createSendSocket(ip_addr, port, username):
    success = False
    sendThread = ""
    sendSocket = socket.socket()
    sendSocket.bind(('127.0.0.1', port))
    sendSocket.connect(('127.0.0.1', 2000))
    count = 0
    while(not(success)):
        ############
        #send message before registering from here to check error101
        '''if count <2:
            msg = "hello dear"
            sendSocket.send(bytes(msg, 'utf-8'))
        else:
            msg = "REGISTER TOSEND {}\n\n".format(username)
            sendSocket.send(bytes(msg, 'utf-8'))'''
        ###########
        count +=1
        msg = "REGISTER TOSEND {0}\n\n".format(username)
        sendSocket.send(bytes(msg, 'utf-8'))
        # now, wait for response from server
        data = sendSocket.recv(1024)
        expectedResponse = "REGISTERED TOSEND {0}\n\n".format(username)
        error100 = "ERROR 100 Malformed username\n\n"
        # successfully connected
        if (data.decode('utf-8') == expectedResponse):
            print(data.decode('utf-8'))
            sendThread = cliSendingThread(sendSocket, username)
            sendThread.start()
            success = True
        # error 100 for malformed username
        elif (data.decode('utf-8') == error100):
            print(data.decode('utf-8'))
            sendSocket.close()
            break
        # error 101 for sending msg before registration
        else:
            print(data.decode('utf-8'))
    return success, sendThread
    

def createRecvSocket(ip_addr, port, username):
    success = False
    recvThread = ""
    recvSocket = socket.socket()
    recvSocket.bind((ip_addr, port))
    recvSocket.connect(('127.0.0.1', 2000))
    count = 0
    while(not(success)):
        ############
        #send message before registering from here to chech error101
        '''if count == 0:
            msg = "hello dear"
            recvSocket.send(bytes(msg, 'utf-8'))
        else:
            msg = "REGISTER TORECV {}\n\n".format(username)
            recvSocket.send(bytes(msg, 'utf-8'))'''
        ###########
        count +=1
        msg = "REGISTER TORECV {}\n\n".format(username)
        recvSocket.send(bytes(msg, 'utf-8'))
        data = recvSocket.recv(1024)
        expectedResponse = "REGISTERED TORECV {0}\n\n".format(username)
        error100 = "ERROR 100 Malformed username\n\n"
         # successfully connected
        if (data.decode('utf-8') == expectedResponse):
            print(data.decode('utf-8'))
            recvThread = cliReceivingThread(recvSocket, username)
            recvThread.start()
            success = True
        # error 100 for malformed username
        elif (data.decode('utf-8') == error100):
            print(data.decode('utf-8'))
            recvSocket.close()
            break
        # error 101 for sending msg before registration
        else:
            print(data.decode('utf-8'))
    return success, recvThread


# take username, ip_address, port numbers as input here
print("Enter Username: ")
username = input()
print("Enter IP address: ")
ipaddr = input()
print("Enter sending port: ")
sport = int(input())
print("Enter receiving port: ")
rport = int(input())
print("\n")

# create sending and receiving sockets and threads
sthreadSuccess, sendThread = createSendSocket(ipaddr, sport, username)
if sthreadSuccess == False:
    print("TOSEND REGISTRATION FAILED\n\n")

rthreadSuccess, recvThread = createRecvSocket(ipaddr, rport, username)
if rthreadSuccess == False:
    print("TORECV REGISTRATION FAILED\n\n")




