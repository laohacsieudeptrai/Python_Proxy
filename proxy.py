import socket
import sys
import _thread
import datetime


def Get_Block_MSG():
    # HTTP/1.1 403 Forbidden\r\n
    # Date: DiW, dd mon yyyy hh:mm:ss GMT\n\n
    # Connection: Closed\r\n
    # \r\n
    # <!DOCTYPE HTML>\r\n
    # <html>\r\n
    # <head>\r\n
    # <title>403 Forbidden</title>\r\n
    # </head>\r\n
    # <body>\r\n
    # <h1>Forbidden</h1>\r\n
    # <p>The proxy has blocked your request.</p>\r\n
    # </body>\r\n
    # </html>\r\n
    # \r\n

    date_time = datetime.datetime.utcnow()  # get current GMT time
    __date = str(date_time).split(' ')[0]  # get date from date_time
    __date = datetime.datetime.strptime(
        __date, '%Y-%m-%d').strftime('%d %b %Y')  # yyyy-mm-dd -> dd mon yyyy
    __time = str(date_time).split(' ')[1]  # get time from date_time
    __time = str(__time).split('.')[0]  # remove miliseconds from time
    day_in_week = datetime.datetime.strptime(
        __date, '%d %b %Y').strftime('%a')  # dd mon yyyy -> day in week

    # construct http headers
    __header = 'HTTP/1.1 403 Forbidden\r\n'
    __date_time = 'Date: ' + day_in_week + ', ' + __date + ' ' + __time + ' GMT\r\n'
    __connection = 'Connection: Closed\r\n'

    # construct http message and body
    http_403 = __header + __date_time + __connection + '\r\n'
    http_body = '<!DOCTYPE HTML>\r\n<html>\r\n<head>\r\n<title>403 Forbidden</title>\r\n</head>\r\n<body>\r\n<h1>Forbidden</h1>\r\n<p>The proxy has blocked your request.</p>\r\n</body>\r\n</html>\r\n\r\n'

    return(http_403.encode('utf-8') + http_body.encode('utf-8'))


def SocketThread(connection, address):
    print('Started new thread for', address)
    req = connection.recv(1024)
    req_decoded = str(req, errors='ignore')  # decode bytestring to string

    webaddress = req_decoded.split('\n')[0]  # get first line
    http_method = req_decoded.split(' ')[0]  # get http method
    if http_method in ('CONNECT'):
        response = Get_Block_MSG()
        connection.send(response)
        connection.close()
        return

    # split request by headers
    req_headers = req_decoded.splitlines()
    host_pos = 0
    for i in range(req_headers.__len__()):
        if 'Host: ' in req_headers[i]:
            host_pos = i

    # get requested website
    webaddress = req_headers[host_pos]
    webaddress = webaddress.split(' ')[1]

    # get port
    webport = 80  # default http port
    port_position = webaddress.find(':')
    if port_position is not -1:
        webport = int(webaddress.split(':')[1])
        webaddress = webaddress.split(':')[0]

    try:
        # construct socket to webserver
        Client_Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    except socket.error as err:
        if Client_Socket:
            Client_Socket.close()
            print(f'Client Socket Error: {err}')
        elif connection:
            connection.close()
            print(f'Connection Error: {err}')
        sys.exit(1)

    print('Connecting to', webaddress, 'at', webport)
    Client_Socket.connect((webaddress, webport))
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
    def __init__(self, IP, PORT):
        print('Initializing Proxy Socket...')
        try:
            self.Server_Socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)  # construct socket to browser
        except socket.error as err:
            if self.Server_Socket:
                self.Server_Socket.close()
            print(f'Socket Init Error: {err}')
            sys.exit(1)

        self.Server_Socket.bind((IP, PORT))  # bind socket to localhost at 8888
        print('Proxy socket initialized at', IP, PORT)

    def StartServer(self):
        print('Listening for connections...')
        # wait for 20 connections before executing
        self.Server_Socket.listen(20)
        while True:
            # accept incoming connections
            (self.Connections, self.Address) = self.Server_Socket.accept()
            print('Connected to', self.Address)
            # create new threads for each connection
            _thread.start_new_thread(
                SocketThread, (self.Connections, self.Address))
        self.Server_Socket.close()

    def Read_Blacklist(self):
        file = open('blacklist.conf', 'r+')
        blacklist = file.read()
        blacklist = blacklist.splitlines()
        print(blacklist)


def main():
    proxy = ProxyServer('127.0.0.1', 8888)
    # proxy.StartServer()
    proxy.Read_Blacklist()


if __name__ == '__main__':
    main()
