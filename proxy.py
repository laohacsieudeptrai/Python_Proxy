import socket
import sys
import _thread
import datetime
import os

path = os.path.dirname(os.path.abspath(__file__))
path = path + '/.cache/'

def Get_Block_MSG():
	# HTTP/1.1 403 Forbidden
	# Date: DiW, dd mon yyyy hh:mm:ss GMT  (DiW = Day in Week: Mon, Tue, Wed,...)
	# Connection: Closed
	# 
	# <!DOCTYPE HTML>
	# <html>\
	# <head>\
	# <title>403 Forbidden</title>
	# </head>
	# <body>
	# <h1>Forbidden</h1>
	# <p>The proxy has blocked your request.</p>
	# </body>
	# </html>
	# 

	date_time = datetime.datetime.utcnow()				# get current GMT time
	__date = str(date_time).split(' ')[0]				# get date from date_time
	__date = datetime.datetime.strptime(
		__date, '%Y-%m-%d').strftime('%d %b %Y')		# yyyy-mm-dd -> dd mon yyyy
	__time = str(date_time).split(' ')[1]				# get time from date_time
	# remove miliseconds from time
	__time = str(__time).split('.')[0]
	day_in_week = datetime.datetime.strptime(
		__date, '%d %b %Y').strftime('%a')				# dd mon yyyy -> day in week

	# construct http headers
	__header = 'HTTP/1.1 403 Forbidden\r\n'
	__date_time = 'Date: ' + day_in_week + ', ' + __date + ' ' + __time + ' GMT\r\n'
	__connection = 'Connection: Closed\r\n'

	# construct http message and body
	http_403 = __header + __date_time + __connection + '\r\n'
	http_body = '<!DOCTYPE HTML>\r\n<html>\r\n<head>\r\n<title>403 Forbidden</title>\r\n</head>\r\n<body>\r\n<h1>Forbidden</h1>\r\n<p>The proxy has blocked your request.</p>\r\n</body>\r\n</html>\r\n\r\n'

	return(http_403.encode('utf-8') + http_body.encode('utf-8'))


# read cache
def Read_Cache(webaddress):
	if os.path.exists(path):
		if os.path.exists(path + webaddress):
			cache_file = open(path + webaddress, 'r')
			cache = cache_file.read()
			cache_file.close()
			return (cache)
		else:
			return(None)
	else:
		os.makedirs(path)
		return(None)


# write cache
def Write_Cache(webaddress, response):
	if not os.path.exists(path):
		os.makedirs(path)
	
	cache_file = open(path + webaddress, 'a')
	cache_file.write(str(response, errors='ignore'))
	cache_file.close()


# handle each socket thread
def SocketThread(connection, address, blacklist):
	print('Started new thread for', address)
	req = connection.recv(1024)
	# decode bytestring to string
	req_decoded = str(req, errors='ignore')

	webaddress = req_decoded.split('\n')[0]				# get first line
	http_method = req_decoded.split(' ')[0]				# get http method
	# block https requests
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
	webport = 80										# default http port 80
	port_position = webaddress.find(':')
	if port_position is not -1:
		webport = int(webaddress.split(':')[1])
		webaddress = webaddress.split(':')[0]

	# block blacklisted requests
	if webaddress in blacklist:
		response = Get_Block_MSG()
		connection.send(response)
		connection.close()
		return

	# check cached data
	cache = Read_Cache(webaddress)
	if cache is not None:
		connection.send(cache.encode('utf-8'))
		connection.close()
		return

	try:
		# construct socket to webserver
		Client_Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		print('Connecting to', webaddress, 'at', webport)
		Client_Socket.connect((webaddress, webport))
		Client_Socket.send(req)

		while True:
			response = Client_Socket.recv(1024)
			if response.__len__():
				Write_Cache(webaddress, response)
				connection.send(response)
			else:
				break

		Client_Socket.close()
		connection.close()

	except socket.error as err:
		if Client_Socket:
			Client_Socket.close()
			print(f'Client Socket Error: {err}')
		elif connection:
			connection.close()
			print(f'Connection Error: {err}')
		sys.exit(1)


class ProxyServer:
	# initialize socket to browser
	def __init__(self, IP, PORT):
		print('Initializing Proxy Socket...')
		try:
			# construct socket to browser
			self.Server_Socket = socket.socket(
				socket.AF_INET, socket.SOCK_STREAM)
			# bind socket to localhost at 8888
			self.Server_Socket.bind((IP, PORT))
		except socket.error as err:
			if self.Server_Socket:
				self.Server_Socket.close()
			print(f'Socket Init Error: {err}')
			sys.exit(1)

		print('Proxy socket initialized at', IP, PORT)

		self.blacklist = self.Read_Blacklist()


	# start proxy server
	def StartServer(self):
		print('Listening for connections...')
		# wait for 5 connections before executing
		self.Server_Socket.listen()
		while True:
			# accept incoming connections
			(self.Connections, self.Address) = self.Server_Socket.accept()
			print('Connected to', self.Address)
			# create new thread for each connection
			_thread.start_new_thread(
				SocketThread, (self.Connections, self.Address, self.blacklist))
		self.Server_Socket.close()


	# read blacklist
	def Read_Blacklist(self):
		file = open('blacklist.conf', 'r')
		blacklist = file.read()
		blacklist = blacklist.splitlines()
		file.close()
		return (blacklist)


def main():
	proxy = ProxyServer('127.0.0.1', 8888)
	proxy.StartServer()


if __name__ == '__main__':
	main()
