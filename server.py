import socket
import time
import os
from datetime import datetime

HOST_IP = "192.168.43.144"
HOST_PORT = 12346
RECIVE_BUFFER = 1024
TIMEOUT = 60
INTERVAL = 40
COUNT = 4 
MAX_CLIENT_COUNT = 1


class Server:
  def __init__(self, hostIp, hostPort): 
    self.__HOST_PORT = hostPort
    self.__HOST_IP = hostIp
    self.__SERVER_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
 

  def bindServerSocket(self):
    self.__SERVER_SOCKET.bind((self.__HOST_IP, self.__HOST_PORT))
  

  def listenServerSocket(self, maxClientNumber):
    self.__SERVER_SOCKET.listen(maxClientNumber)
    print("Server is waiting for clients.\n")


  def acceptServerSocket(self):
    (clientSocket, address) = self.__SERVER_SOCKET.accept()
    self.__CLIENT_SOCKET = clientSocket
    self.__address = address
    print(f"Client connected: {address}\n")
  
  
  def setClientSocketSettings(self, timeout, interval, count):
    self.__CLIENT_SOCKET.settimeout(timeout)
    self.__CLIENT_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    self.__CLIENT_SOCKET.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, interval)
    self.__CLIENT_SOCKET.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, int(interval / 8))
    self.__CLIENT_SOCKET.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, count)


  def __reconnect(self):
    print("Connection have been lost. Reconnecting.\n")
    self.__CLIENT_SOCKET.close()
    self.acceptServerSocket()
    self.setClientSocketSettings(TIMEOUT, INTERVAL, COUNT)


  def closeServerSocket(self):
    self.__SERVER_SOCKET.close()


  def __reciveMessageFromClient(self, bufferSize):
    return str(self.__CLIENT_SOCKET.recv(bufferSize).decode('utf-8'))
  

  def __sendMessageToClient(self, message):
    self.__CLIENT_SOCKET.send(str(message).encode('utf-8'))


  def __sendFile(self, fileName, offset):
    with open(fileName, 'rb') as file:
      file.seek(int(offset), 0)
      startTime = time.time()
      while True:
        data = file.read(RECIVE_BUFFER)
        if not data:
          break
        self.__CLIENT_SOCKET.send(data)
      endTime = time.time()
    return (endTime - startTime)
  

  def __reciveFile(self, fileName, mode, fileSize):
    with open(fileName, mode) as file:
      file.seek(0, os.SEEK_END)
      offset = os.path.getsize(fileName)
      while fileSize > offset:
        data = self.__CLIENT_SOCKET.recv(RECIVE_BUFFER)
        offset += len(data)
        if not data:
          break
        file.write(data)   


  def __echoCommand(self, message):  
    self.__sendMessageToClient(message)
    print("Command from client: ECHO")
    print(f"Response for client: {message}\n")

  
  def __timeCommand(self):
    currentTime = datetime.now().strftime("%H:%M:%S")
    self.__sendMessageToClient(currentTime)
    print("Command from client: TIME")
    print(f"Response for client: {currentTime}\n")


  def __exitCommand(self):
    self.__isHandling = False
    self.__sendMessageToClient("Good bye!")
    print("Command from client: EXIT")
    print("Response for client: Good bye!\n")


  def __uploadCommand(self, fileName):
    print("Command from client: UPLOAD")
    if os.path.exists(fileName):
      mode = 'ab'
      offset = os.path.getsize(fileName)
    else:
      mode = 'wb+'
      offset = 0  
    self.__sendMessageToClient(offset)
    fileSize = int(self.__reciveMessageFromClient(RECIVE_BUFFER))
    if fileSize > offset:
      self.__sendMessageToClient("OK")
      self.__reciveFile(fileName, mode, fileSize)
      print("File uploaded successfully\n")
    else:
      self.__sendMessageToClient("Error. Offset not correct")
      print("Error. Offset not correctn")


  def __downloadCommand(self, fileName): 
    print("Command from client: DOWNLOAD")
    if not os.path.exists(fileName):
      self.__sendMessageToClient("File does not exist")
    else:
      fileSize = int(os.path.getsize(fileName))
      self.__sendMessageToClient(fileSize)
      offset = int(self.__reciveMessageFromClient(RECIVE_BUFFER))
      sendTime = self.__sendFile(fileName, offset)
      speed = "{:.2f}".format((fileSize - offset) / sendTime / 1024)
      print("Download Speed: {} KB/s".format(speed))


  def __notExistingCommand(self, command):
    self.__sendMessageToClient("Unknown command: " + command)
    print(f"Command from client: {command}")
    print(f"Response for client: Unknown command ({command})\n")


  def __parseCommand(self, request):
    command = request.split()

    if request.startswith("ECHO"):
      self.__echoCommand(request[5:])

    elif request == "TIME":
      self.__timeCommand()

    elif request == "QUIT":
      self.__exitCommand()
    
    elif command[0] == "UPLOAD":
      self.__uploadCommand(command[1])

    elif command[0] == "DOWNLOAD":
      self.__downloadCommand(command[1])
    
    else:
      self.__notExistingCommand(request)
    

  def startHandlingClientCommands(self):
    self.__isHandling = True
    while self.__isHandling:
      try:
        request = self.__reciveMessageFromClient(RECIVE_BUFFER)
        if len(request):
          self.__parseCommand(request)
        else:
          self.__reconnect()
      except socket.error as exception:
        self.__reconnect()
    self.__CLIENT_SOCKET.close()


server = Server(HOST_IP, HOST_PORT)
server.bindServerSocket()
server.listenServerSocket(MAX_CLIENT_COUNT)
server.acceptServerSocket()
server.setClientSocketSettings(TIMEOUT, INTERVAL, COUNT)
server.startHandlingClientCommands()
server.closeServerSocket()
