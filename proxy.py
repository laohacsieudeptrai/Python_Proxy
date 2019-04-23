import socket
import sys
import _thread
import datetime

def Block(connection, address):
    date_time = datetime.datetime.utcnow()  # get current GMT time
    __date = str(date_time).split(' ')[0]  # get date from date_time
    __date = datetime.datetime.strptime(__date, '%Y-%m-%d').strftime('%d %b %Y')  # yyyy-mm-dd -> dd mon yyyy
    __time = str(date_time).split(' ')[1]  # get time from date_time
    __time = str(__time).split('.')[0]  # remove miliseconds from time
    day_in_week = datetime.datetime.strptime(__date, '%d %b %Y').strftime('%a')  # dd mon yyyy -> day in week

    # construct http headers
    __header = 'HTTP/1.1 403 Forbidden\r\n'
    __content_type = 'Content-Type: text/html; charset=UTF-8\r\n'
    __content_length = 'Content-Length: 170'
    __date_time = 'Date: ' + day_in_week + ', ' + __date + ' ' + __time + ' GMT\r\n'
    __connection = 'Connection: Closed\r\n'
    
    # construct http message and body
    http_403 = __header + __date_time + __connection + '\r\n'
    http_body = '<!DOCTYPE HTML>\r\n<html>\r\n<head>\r\n<title>403 Forbidden</title>\r\n</head>\r\n<body>\r\n<h1>Forbidden</h1>\r\n<p>The proxy has blocked your request.</p>\r\n</body>\r\n</html>\r\n\r\n'

    return(http_403.encode('utf-8')+http_body.encode('utf-8'))


def SocketThread(connection, address):
    print('Started new thread for', address)
    req = connection.recv(1024)
    req_decoded = req.decode('utf-8')  # decode bytestring to string
    webaddress = req_decoded.split('\n')[0]  # get first line
    http_method = req_decoded.split(' ')[0]  # get http method

    # get requested website
    webaddress = webaddress.split(' ')[1]
    webaddress = webaddress.split(' ')[0]

    # split 'http://'
    http_header = webaddress.find('://')
    if http_header is not -1:
        webaddress = webaddress.split('://')[1]

    # get port
    webport = 80  # default http port
    port_position = webaddress.find(':')
    if port_position is not -1:
        webport = int(webaddress.split(':')[1])
        webaddress = webaddress.split(':')[0]
    

    try:
        Client_Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # construct socket to webserver

    except socket.error:
        if Client_Socket:
            Client_Socket.close()
            print('Client Socket Error:', socket.error)
        elif connection:
            connection.close()
            print('Connection Error:', socket.error)
        sys.exit(1)

    
    print('Connecting to', webaddress, 'at', webport)
    Client_Socket.connect((webaddress,webport))
    Client_Socket.send(req)

    while True:
        response = Client_Socket.recv(1024)
        if response.__len__():
            connection.send(response)
        else:
            break
        
    Client_Socket.close()
    connection.close()


class ProxyServer:
    def __init__(self,LOCALIP,PORT):
        print('Initializing Proxy Socket...')
        try:
            self.Server_Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # construct socket to browser
        except socket.error:
            if self.Server_Socket:
                self.Server_Socket.close()
            print('Socket Init Error:', socket.error)
            sys.exit(1)

        self.Server_Socket.bind((LOCALIP,PORT))  # bind socket to localhost at 8888
        print('Proxy socket initialized at', LOCALIP, PORT)

    def StartServer(self):
        print('Listening for connections...')
        self.Server_Socket.listen(20)  # wait for 20 connections before executing
        while True:
            (self.Connections, self.Address) = self.Server_Socket.accept()  # accept incoming connections
            print('Connected to', self.Address)
            _thread.start_new_thread(SocketThread, (self.Connections, self.Address))  # create new threads for each connection
        self.Server_Socket.close()
    

def main():
    proxy = ProxyServer('127.0.0.1', 8888)
    proxy.StartServer()

if __name__ == '__main__':
    main()