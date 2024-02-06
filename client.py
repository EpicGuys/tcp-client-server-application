import socket
import os
import time

BUFFER_SIZE = 1024
COUNT_OF_PACKAGES = 3
TIMEOUT = 20
processFlag = True

server_address = ('192.168.43.144', 65435)

def sendSocket(clientSocket, data):
    clientSocket.send(str(data).encode('utf-8'))


def recvSocket(clientSocket, size):
    return clientSocket.recv(size).decode('utf-8')


def quitCommand(clientSocket):
    global processFlag
    processFlag = False
    sendSocket(clientSocket, "QUIT")
    response = recvSocket(clientSocket, BUFFER_SIZE)
    print(response)


def timeCommand(clientSocket):
    sendSocket(clientSocket, "TIME")
    response = recvSocket(clientSocket, BUFFER_SIZE)
    print(response)


def echo(clientSocket, request):
    sendSocket(clientSocket, request)
    response = recvSocket(clientSocket, BUFFER_SIZE)
    print(response)


def isFileExist(clientSocket):
    response = recvSocket(clientSocket, BUFFER_SIZE)
    if response == "File does not exist":
        return 0
    else:
        return int(response)

def sendPropertiesDownloading(clientSocket, filename, filesize):
    offset = os.path.getsize(filename)
    sendSocket(clientSocket, offset)
    formatedResponseData = "{:.2f}".format(offset / BUFFER_SIZE)
    formatedFilesize = "{:.2f}".format(filesize / BUFFER_SIZE)
    print("Current size of {}: {} KB  of {} KB".format(filename, formatedResponseData, formatedFilesize))
    return offset


def downloadFile(clientSocket, filename, filesize):
    mode  = 'ab' if os.path.exists(filename) else 'wb+'

    with open(filename, mode) as file:
        offset = sendPropertiesDownloading(clientSocket, filename, filesize)

        file.seek(0, os.SEEK_END)

        while filesize > offset:
            data = clientSocket.recv(BUFFER_SIZE)
            offset = offset + len(data)
            file.write(data)

        print("File {} downloaded successful".format(filename))


def download(clientSocket, request):
    sendSocket(clientSocket, request)

    filesize = isFileExist(clientSocket)
    
    if(filesize == 0):
        print("File does not exist")
        return
    
    downloadFile(clientSocket, request.split()[1], filesize)


def uploadFile(clientSocket, filename):
    with open(filename, 'rb') as file:
        offset = int(recvSocket(clientSocket, BUFFER_SIZE))
        sendSocket(clientSocket, os.path.getsize(filename))
        response = recvSocket(clientSocket, BUFFER_SIZE);
        if response == "OK":
            file.seek(offset, 0)
            while True:
                data = file.read(BUFFER_SIZE)
                if not data:
                    break
                clientSocket.send(data)
            return (offset, os.path.getsize(filename))
        else:
            return (0,0)


def upload(clientSocket, data):
    if not os.path.exists(data.split()[1]):
        print("File {} does not exist".format(data.split()[1]))
        return
    
    sendSocket(clientSocket, data)

    startTime = time.time()
    offset, filesize = uploadFile(clientSocket, data.split()[1])
    endTime = time.time()
    if filesize > 0:
        elapsedTime = endTime - startTime
        formattedValue = "{:.2f}".format((filesize - offset) / elapsedTime / 1024)
        print("Upload Speed: {} KB/s".format(formattedValue))
    else:
        print("Offset is not correct")

def commandProcessing(request, clientSocket):
    command = request.split()[0].upper()
    request = request.split()
    request = ' '.join([request[0].upper()] + request[1:])

    if command == "QUIT":
        quitCommand(clientSocket)

    elif command == "ECHO":
        if len(request.split()) > 1:
            echo(clientSocket, request)

    elif command == "TIME":
        timeCommand(clientSocket)

    elif command == "DOWNLOAD":
        if len(request.split()) > 1:
            download(clientSocket, request)

    elif command == "UPLOAD":
        if len(request.split()) > 1:
            upload(clientSocket, request)

    else:
        print("{} is not command".format(command))


def reconnect():
    print("Connection lost... Reconnect?(Y/N)")

    user_input = input("-> ").split()
    if user_input[0].upper() == 'Y':
        return True
    else:
        return False

def connection(interval, countOfPackages):
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.settimeout(interval * countOfPackages)
    clientSocket.connect(server_address)
    clientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    clientSocket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, interval)
    clientSocket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, int(interval/5))
    clientSocket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, countOfPackages)

    return clientSocket


def main():
    global processFlag
    clientSocket = None
    while True:
        try:
            clientSocket = connection(TIMEOUT, COUNT_OF_PACKAGES)
            while processFlag:
                arguments = input("-> ")
                if not arguments:
                    continue
                commandProcessing(arguments, clientSocket)
            
        except socket.error:
            if(reconnect() != True):
                break
        finally:
            if clientSocket is not None:
                clientSocket.close()       


if __name__ == "__main__":
    main()
