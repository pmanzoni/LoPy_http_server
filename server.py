#!/usr/bin/python

# PM: based on http://blog.wachowicz.eu/?p=256
# PM: added POST handling
# import signal  # Signal support (server shutdown on signal receive)

import socket  # Networking support
import time    # Current time

import posthandler # PM: code to be executed to handle a POST

WEB_PAGES_HOME_DIR = '.' # Directory where webpage files are stored

class Server:
 """ Class describing a simple HTTP server objects."""

 def __init__(self, port = 80):
     """ Constructor """
     self.host = ''   # <-- works on all avaivable network interfaces
     self.port = port
     self.www_dir =  WEB_PAGES_HOME_DIR

 def activate_server(self):
     """ Attempts to aquire the socket and launch the server """
     self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
     try: # user provided in the __init__() port may be unavaivable
         print("Launching HTTP server on ", self.host, ":",self.port)
         self.socket.bind((self.host, self.port))

     except Exception as e:
         print ("Warning: Could not acquire port:",self.port,"\n")
         print ("I will try a higher port")
         # store to user provided port locally for later (in case 8080 fails)
         user_port = self.port
         self.port = 8080

         try:
             print("Launching HTTP server on ", self.host, ":",self.port)
             self.socket.bind((self.host, self.port))

         except Exception as e:
             print("ERROR: Failed to acquire sockets for ports ", user_port, " and 8080. ")
             print("Try running the Server in a privileged user mode.")
             self.shutdown()
             import sys
             sys.exit(1)

     print ("Server successfully acquired the socket with port:", self.port)
     print ("Press Ctrl+C to shut down the server and exit.")
     self._wait_for_connections()

 def shutdown(self):
     """ Shut down the server """
     try:
         print("Shutting down the server")
         s.socket.shutdown(socket.SHUT_RDWR)

     except Exception as e:
         print("Warning: could not shut down the socket. Maybe it was already closed...", e)


 def _gen_headers(self,  code):
     """ Generates HTTP response Headers. """

     # determine response code
     h = ''
     if (code == 200):
        h = 'HTTP/1.1 200 OK\n'
     elif(code == 404):
        h = 'HTTP/1.1 404 Not Found\n'

     # write further headers
#     current_date = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
# PM: should find an alternative for LoPys
     current_date = '4 Agosto 1965'
     h += 'Date: ' + current_date +'\n'
     h += 'Server: Simple-Python-HTTP-Server\n'
     h += 'Connection: close\n\n'  # signal that the conection will be closed after completing the request

     return h

 def _wait_for_connections(self):
     """ Main loop awaiting connections """
     while True:
         print ("Awaiting New connection")
         self.socket.listen(3) # maximum number of queued connections

         conn, addr = self.socket.accept()
         # conn - socket to client
         # addr - clients address

         print("Got connection from:", addr)

         data = conn.recv(1024) #receive data from client
         treq = bytes.decode(data) #decode it to treq

         #determine request method  (HEAD and GET are supported) (PM: added support to POST )
         request_method = treq.split(' ')[0]
         print ("Method: ", request_method)
         print ("Full HTTP message: -->")
         print (treq)
         print ("<--")

         treqhead = treq.split("\r\n\r\n")[0]
         treqbody = treq[len(treqhead):].lstrip() # PM: makes easier to handle various types of newlines
         print ("only the HTTP body: -->")
         print (treqbody)
         print ("<--")

         if (request_method == 'GET') | (request_method == 'HEAD'):

             # split on space "GET /file.html" -into-> ('GET','file.html',...)
             file_requested = treq.split(' ')
             file_requested = file_requested[1] # get 2nd element

             #Check for URL arguments. Disregard them
             file_requested = file_requested.split('?')[0]  # disregard anything after '?'

             if (file_requested == '/'):  # in case no file is specified by the browser
                 file_requested = '/index.html' # load index.html by default
             elif (file_requested == '/favicon.ico'):  # most browsers ask for this file...
                 file_requested = '/index.html' # ...giving them index.html instead

             file_requested = self.www_dir + file_requested
             print ("Serving web page [",file_requested,"]")

             ## Load file content
             try:
                 file_handler = open(file_requested,'rb')
                 if (request_method == 'GET'):  #only read the file when GET
                     response_content = file_handler.read() # read file content
                 file_handler.close()

                 response_headers = self._gen_headers( 200)

             except Exception as e: #in case file was not found, generate 404 page
                 print ("Warning, file not found. Serving response code 404\n", e)
                 response_headers = self._gen_headers( 404)

                 if (request_method == 'GET'):
                    response_content = b"<html><body><p>Error 404: File not found</p><p>Python HTTP server</p></body></html>"


             server_response =  response_headers.encode() # return headers for GET and HEAD
             if (request_method == 'GET'):
                 server_response +=  response_content  # return additional conten for GET only


             conn.send(server_response)
             print ("Closing connection with client")
             conn.close()

         elif (request_method == 'POST'):

             # split on space "GET /file.html" -into-> ('GET','file.html',...)
             file_requested = treq.split(' ')
             file_requested = file_requested[1] # get 2nd element

             #Check for URL arguments. Disregard them
             file_requested = file_requested.split('?')[0]  # disregard anything after '?'

             if (file_requested == '/'):  # in case no file is specified by the browser
                 file_requested = '/index.html' # load index.html by default

             file_requested = self.www_dir + file_requested
             print ("Serving web page [",file_requested,"]")

             ## Load file content
             try:
                 if (file_requested.find("execposthandler") != -1):
                     print("... PM: running python code")
                     response_content = posthandler.run(treqbody)
                 else:
                     file_handler = open(file_requested,'rb')
                     response_content = file_handler.read() # read file content
                     file_handler.close()

                 response_headers = self._gen_headers( 200)

             except Exception as e: #in case file was not found, generate 404 page
                 print ("Warning, file not found. Serving response code 404\n", e)
                 response_headers = self._gen_headers( 404)
                 response_content = b"<html><body><p>Error 404: File not found</p><p>Python HTTP server</p></body></html>"


             server_response =  response_headers.encode() # return headers
             server_response +=  response_content  # return additional content

             conn.send(server_response)
             print ("Closing connection with client")
             conn.close()

         else:
             print("Unknown HTTP request method:", request_method)



def graceful_shutdown(sig, dummy):
    """ This function shuts down the server. It's triggered
    by SIGINT signal """
    s.shutdown() #shut down the server
    import sys
    sys.exit(1)



###########################################################

print ("Starting web server")
s = Server(80)  # construct server object
s.activate_server() # acquire the socket
