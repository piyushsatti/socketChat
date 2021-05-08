import socket, threading, datetime, os
from operator import attrgetter

# attrgetter solves the problem of referencing class vars

class message:
    availMsgNum = 1

    def __init__(self, msgTimestamp, msgAuthor, msgText):
        self.msgNum = message.availMsgNum
        message.availMsgNum += 1
        self.msgTimestamp = msgTimestamp
        self.msgAuthor = msgAuthor
        self.msgText = msgText
        self.edit = False

    def msgEdit(self, msgText):
        self.edit = True
        self.msgText = msgText
        self.msgTimestamp = datetime.datetime.now()

    def __del__(self):
        print(f'Message number {self.msgNum} by author {self.msgAuthor} deleted')


class user:

    availUserNum = 1

    def __init__(self, client, timestamp, nick, add, UDPport):

        try:
            self.uNum = user.availUserNum
            user.availUserNum += 1
            self.uClient = client
            self.uTimestamp = timestamp
            self.uNick = nick
            self.uAdd = add
            self.uUDP = UDPport

        except Exception as e:
            print(f'Failed handshake error was: {e}')

    def __del__(self):
        self.uClient.close()
        print(f'User number {self.uNum} called {self.uNick} is bound to us no more D:')


def receive():
    global activeUsers
    global numTries

    while True:
        # Accept Connection
        client, address = server.accept()

        tries = numTries

        while tries != -1:
            
            # Using 0Auth topic to verify
            client.send('0Auth'.encode('ascii'))
            response = client.recv(1024).decode('ascii').split(';')

            if tries==0:
                client.send('0Auth:banned'.encode('ascii'))

            tries -= 1
            flag = False
            with open('credentials.txt', 'r') as fil:
                for line in fil:
                    l = line.replace('\n', " ").strip().split(' ')
                    if response[0] == l[0] and response[1] == l[1]:
                        client.send('0Auth:authenticated'.encode('ascii'))
                        flag = True
                    
            if flag:

                # Reading post acceptance response from client
                nick = response[0]
                UDPport = int(client.recv(1024).decode('ascii'))

                # Creating the class object and appending to list
                context = user(client, datetime.datetime.now(), nick, address, UDPport)
                activeUsers.append(context)

                # Printing the success result and breaking out of tries
                print("Connected to {} with address {}".format(nick, str(address)))
                break

            else:
                client.send('0Auth:error:'.encode('ascii'))
                continue

        # Start Handling Thread For Client
        thread = threading.Thread(target=handle, args=(context,))
        thread.start()

# Handling Messages From Clients
def handle(context):

    global msgList
    global activeUsers

    while True:

        # Recieving Messages
        mc = context.uClient.recv(1024).decode('ascii').split(" ")

        if mc[0] == 'MSG':
            temp = message(datetime.datetime.now(), context.uNick, ' '.join(mc[1:]))
            msgList.append(temp)
            print(f'{temp.msgAuthor} posted MSG #{temp.msgNum} "{temp.msgText}" at {temp.msgTimestamp.strftime("%d %b %Y %H:%M:%S")}')
            context.uClient.send(f'{temp.msgNum};{temp.msgTimestamp.strftime("%d %b %Y %H:%M:%S")}'.encode('ascii'))

        elif mc[0] == 'DLT':
            # Finds the message
            for temp in msgList:

                if temp.msgNum == int(mc[1][1]) and temp.msgTimestamp.strftime("%d %b %Y %H:%M:%S") == ' '.join(mc[2:]):

                    # Checks permission
                    if context.uNick != temp.msgAuthor:
                        print('You do not have permission to do this action!')
                        context.uClient.send('You do not have permission to do this action!'.encode('ascii'))
                        break
                    
                    print(f'{temp.msgAuthor} deleted MSG #{temp.msgNum} “{temp.msgText}” at {temp.msgTimestamp.strftime("%d %b %Y %H:%M:%S")}.')
                    context.uClient.send(f'Message #{temp.msgNum} deleted at {temp.msgTimestamp.strftime("%d %b %Y %H:%M:%S")}.'.encode('ascii'))
                    
                    msgList.remove(temp)
                    del temp

        elif mc[0] == 'EDT':

            time = ' '.join(mc[2:5])
            text = ' '.join(mc[5:])

            # Finds the message
            for temp in msgList:

                if temp.msgNum == int(mc[1][1]) and temp.msgTimestamp.strftime("%d %b %Y %H:%M:%S") == time:

                    # Checks permission
                    if context.uNick != temp.msgAuthor:
                        print('You do not have permission to do this action!')
                        context.uClient.send('You do not have permission to do this action!'.encode('ascii'))
                        break
                    
                    temp.msgEdit = True
                    temp.msgText = text
                    temp.msgTimestamp = datetime.datetime.now()

                    print(f'{temp.msgAuthor} edited MSG #{temp.msgNum} “{temp.msgText}” at {temp.msgTimestamp.strftime("%d %b %Y %H:%M:%S")}.')
                    context.uClient.send(f'Message #{temp.msgNum} edited at {temp.msgTimestamp.strftime("%d %b %Y %H:%M:%S")}.'.encode('ascii'))

        elif mc[0] == 'RDM':

            timeVar = datetime.datetime.strptime(' '.join(mc[1:]), '%d %b %Y %H:%M:%S')
            
            x = f'Return Messages:\n{getMessages(timeVar)}'
            print(f'{context.uNick} issued RDM command. {x}')
            context.uClient.send(x.encode('ascii'))
            

        elif mc[0] == 'ATU':
            x = f'Active user list:\n{getActives()}'
            print(f'{context.uNick} issued ATU command. {x}')
            context.uClient.send(x.encode('ascii'))

        elif mc[0] == 'OUT':
            print(f"{context.uNick} logout")
            activeUsers.remove(context)
            context.uClient.close()

        # Hidden Command ALT for fetching critical data
        elif mc[0] == 'UPL':
            v = ''
            for user in activeUsers:
                v += f"{user.uNick};{user.uAdd};{user.uUDP}\n"
            
            context.uClient.send(v.encode('ascii'))

        else:
            pass

# Gets and filters the needed messages form the messagelist and return the aggreagate list
def getMessages(timeVar):
    global msgList
    
    msgList_sorted = sorted(msgList, key= attrgetter('msgNum'))

    h = ''
    for msg in msgList_sorted:
        if msg.msgTimestamp >= timeVar:
            h += f'#{msg.msgNum} {msg.msgAuthor}: {msg.msgText} posted at {msg.msgTimestamp}\n'

    return h
                    

# Return string of actives for the server
def getActives():
    global activeUsers

    val = ''
    for user in activeUsers:
        val += f'{user.uNick} active since {user.uTimestamp}\n'

    return val

if __name__ == '__main__':

    # Connection Data
    host = '127.0.0.1'
    port = 55555

    while True:
        try:
            numTries = int(input('Please enter the number of tries (integer in range 1 to 5)'))
            print(f'Beginning to Listen on port {port}')

            if numTries not in range(1,6):
                print('Bad value. Not in range 1 to 5 Try again')
                continue

            break

        except Exception as e:
            print('Not an integer try again. Error message:\n{}'.format(e))

    # Starting Server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()

    activeUsers = []
    msgList = []
    receive()

    '''
    change the delete time to the current time instead of the current scheme
    '''