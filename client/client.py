import socket, os, threading
from time import sleep

# Listening to Server and Sending Nickname
def receive():

    global username
    global UDPport

    while True:
        try:
            # Receive Message From Server
            # If '0Auth' Send username:password
            message = client.recv(1024).decode('ascii')
            if '0Auth' in message:
                try:
                    username = input('Enter your username:')
                    password = input('Enter your password:')

                    client.send(f"{username};{password}".encode('ascii'))
                except:
                    print('Client side error during 0Auth initial')
                
                authResponse = client.recv(1024).decode('ascii')

                if ':error:' in authResponse:
                    continue

                elif 'authenticated' in authResponse:
                    print('You have been authenticated')
                    
                    # Send the port to server for storage
                    client.send(f'{UDPport}'.encode('ascii'))
                    
                    write()

                elif 'banned' in authResponse:
                    sleep(10)
                    continue

                else:
                    print('Unexpected error while connecting to client')

            else:
                break

        except Exception as e:
            # Close Connection When Error
            print(f"An error occured!\n {e}")
            client.close()
            break

# Sending Messages To Server
def write():

    while True:

        try:
            message = '{}'.format(input('Enter one of the following commands (MSG, DLT, EDT, RDM, ATU, OUT):'))

            # Checking if code is valid and sending the command
            msgCode = message.split(" ")[0]
            if msgCode not in ['MSG', 'DLT', 'EDT', 'RDM', 'ATU', 'OUT', 'UPL']:
                print('Error. Invalid command!')
                continue

            else:
                client.send(message.encode('ascii'))

            # Command based segregation for the response
            if msgCode == 'MSG':
                response = client.recv(1024).decode('ascii').split(";")
                print(f'Message #{response[0]} posted at {response[1]}')
            
            elif msgCode == 'DLT':
                print(client.recv(1024).decode('ascii'))
            
            elif msgCode == 'EDT':
                print(client.recv(1024).decode('ascii'))

            elif msgCode == 'RDM':
                print(client.recv(1024).decode('ascii'))

            elif msgCode == 'ATU':
                print(client.recv(1024).decode('ascii'))

            elif msgCode == 'OUT':
                print(f"Bye {username}!")
                quit()

            elif msgCode == 'UPL':

                # Target filename
                filename = f"{username}_{message.split(' ')[-1]}"

                # last task of the server
                data = client.recv(1024).decode('ascii')

                response = [dat.split(';') for dat in data.split('\n')]

                for resp in response:
                    if resp[0] == message.split(' ')[1]:
                        p2pStart(resp, filename)
                        break
            
        except Exception as e:
            print(e)

def p2pStart(resp, filename):

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    oriName = filename.split('_')[1]

    sock.sendto(filename.encode('ascii'), ('127.0.0.1', int(resp[2])))

    data = ''
    with open(oriName , 'r') as f:
        for line in f:
            data += line
    try: 
        sock.sendto(data.encode('ascii'), ('127.0.0.1', int(resp[2])))
        print("File transferred")

    except Exception as e:
        print('Porblem in p2pStart')
        print(e)

def p2pCallback():
    global UDPport

    while True:

        # UDP Socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(('127.0.0.1', UDPport))

        filename, _ = s.recvfrom(1024)
        filename =filename.decode('ascii')
        data, _ = s.recvfrom(1024)
        with open(filename, 'wb') as f:
            f.write(data)

        print("File has been received successfully.")


if __name__ == '__main__':

    # TCP port for chat
    myPort = 55555 #input('Enter TCP port number')

    # UDP Port for p2p sharing
    UDPport = int(input('Enter UDP port number'))

    # Connecting To Server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('127.0.0.1', myPort))
    username = None

    # Starting Threads For UDP
    rThread = threading.Thread(target=p2pCallback)
    rThread.start()

    receive()