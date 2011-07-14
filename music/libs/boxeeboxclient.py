'''
Boxee Box Python Client
A Python client module for the Boxee Box JSON RPC API.
http://developer.boxee.tv/JSON_RPC

Written by /rob, 21 April 2011

Usage:

'''

import socket
import asyncore
import sys
import logging
import simplejson
'''
Logging Configuration
'''
logging_level = logging.DEBUG
log_handler = logging.StreamHandler(sys.stdout)
log_handler.setLevel(logging_level) 
log_formatter = logging.Formatter('%(asctime)s::%(name)s::%(levelname)s::%(message)s')
log_handler.setFormatter(log_formatter)

class BoxeeBoxClient:
    def __init__(self, device_id, host, port=9090, application_id="pythonclient", application_label="Music Player"):
        self.device_id = device_id
        self.host = host
        self.port = port
        self.application_id = application_id
        self.application_label = application_label       
        self.log = logging.getLogger("BoxeeBoxPythonClient")
        self.log.setLevel(logging_level)
        self.log.addHandler(log_handler)
        self.log.debug("Initialized Boxee Box Python Client.")
        self.id = 100

    def Pair(self):
        try:
            self.callMethod("JSONRPC.Introspect", {}, True)
        except:
            code = self.config.GetValue('paircode')
            method = "Device.PairChallenge"
            params = {"deviceid": self.device_id, "applicationid": self.application_id, "label": self.application_label, "icon": "http://boxee.bartsidee.nl/apps/music/thumb.png", "type": "other"}
            self.callMethod(method, params, False)
            import xbmc
            import xbmcgui
            xbmc.sleep(3000)
            dialog = xbmcgui.Dialog()
            code = dialog.numeric(0, 'Input Pairing Code')
            self.PairResponse(code)

    def PairResponse(self, code):
        method = "Device.PairResponse"
        params = {"deviceid": self.device_id, "code": str(code)}
        self.callMethod(method, params, False)


    def callMethod(self, method, params=None, auth=None):
        connection = self.openConnection()
        if connection:
            if auth:
                auth_call = self.createCall("Device.Connect", {'deviceid': self.device_id})
                try:
                    self.socket.send(auth_call)
                except Exception, e:
                    raise BoxeeClientException("Unable to authenticate device id to client: %s  Make sure it is paired." % self.device_id)
                response = self.readResponse()
            try:
                call = self.createCall(method, params)
                self.socket.send(call)
            except Exception, e:
                raise BoxeeClientException("Unable to send method %s to client." % method, e)
            response = self.readResponse()
            if response:
                self.closeConnection()
                return response
            else:
                self.closeConnection()
                raise BoxeeClientException("Did not receive response for method %s." % method, e)
        else:  
            raise BoxeeClientException("Unable to connect to host %s:%s" % (self.host, self.port))
        
    
    def createCall(self, method, params=None):
        self.log.debug("Creating call for %s." % method)
        data = {
                'method': method,
                'id': self.id,
                'jsonrpc': "2.0"
                }
        if params:
            data['params'] = params
        self.log.debug("Call created with id: %i" % self.id)
        self.log.debug("Call created: %s" % (str(data)))
        self.id = self.id + 1
        return simplejson.dumps(data)        
    
    def readResponse(self):
        self.log.debug("Reading response...")
        data = ""
        while True:
            chunk = self.socket.recv(1024)
            if not chunk:
                break
            data += chunk
            if data.find("\n") >= 0:
                break            
        self.log.debug("Decoding response...")
        self.log.debug(str(data))
        json = simplejson.loads(data)
        if json.has_key("error"):
            raise BoxeeClientException("Found error code %i in response: %s" % (json['error']['code'], json['error']['message']), "APIError")
        else:
            self.log.debug("No error found in response.")
            self.log.debug("Response: %s" % str(json))
            return json
        
    def openConnection(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   
        try:
            self.socket.connect((self.host, self.port))
            return True
        except Exception, e:
            self.closeConnection()
            raise BoxeeClientException("Could not connect to host %s:%s" % (self.host, str(self.port)), e)
    
    def closeConnection(self):
        try:
            self.socket.close()
        except Exception, e:
            raise BoxeeClientException("Error closing connection to host %s:%s" % (self.host, str(self.port)), e)
          

class BoxeeBoxStreamClient(asyncore.dispatcher):
    def __init__(self, device_id, host, port=9090, application_id="pythonclient", application_label="Boxee Box Python Client"):
        asyncore.dispatcher.__init__ (self)
        self.device_id = device_id
        self.host = host
        self.port = port
        self.application_id = application_id
        self.application_label = application_label     
        self.create_socket (socket.AF_INET, socket.SOCK_STREAM)       
        self.log = logging.getLogger("BoxeeBoxStreamPythonClient")
        self.log.setLevel(logging_level)
        self.log.addHandler(log_handler)
        self.log.debug("Initialized Boxee Box Stream Python Client.")
        self.id = 100
        
    def callMethod(self, method, params=None):
        self.log.info("Calling method %s." % method)
        data = {
                'method': method,
                'id': self.id,
                'jsonrpc': "2.0"
                }
        if params:
            data['params'] = params
        self.buffer = simplejson.dumps(data)
        self.id = self.id + 1
    
    def handleResponse(self, data):
        self.log.debug("Received response.")
        json = simplejson.loads(data)
        if "error" in data:
            raise BoxeeClientException("Method %s failed: %s" % (json['data']['method'], json['data']['message']), "APIError")
        else:
            self.log.debug("No error found in response.")
            self.response = data
        
    def openConnection(self):
        try:
            self.connect((self.host, self.port))
        except Exception, e:
            raise BoxeeClientException("Could not connect to host %s:%s" % (self.host, str(self.port)), e)
    
    def closeConnection(self):
        try:
            self.close()
        except Exception, e:
            raise BoxeeClientException("Error closing connection to host %s:%s" % (self.host, str(self.port)), e)
    
    def handle_connect(self):
        self.log.debug("Connected!")
        
    def handle_close(self):
        self.log.debug("Disconnected!")
        
    def handle_read(self):
        data = self.recv(8192)
        self.log.debug("Data: %s" % str[data])
        return self.handleResponse(data)
        
    def writable (self):
        return (len(self.buffer) > 0)

    def handle_write (self):
        self.log.debug("Sending %s... " % self.buffer)
        sent = self.send(self.buffer)
        self.buffer = self.buffer[sent:]
        
    
class BoxeeClientException(Exception):
    def __init__(self, message, e):
        Exception.__init__(self, message, e)
        self.log = self.setLogger("Exception")
        self.identifyException(message, e)
    
    def setLogger(self, label):
        log = logging.getLogger(label)
        log.addHandler(log_handler)
        return log
    
    def identifyException(self, message, e):
        if "Bad client permission" in message:
            raise BoxeeClientPermissionsException(message, e)
        elif "APIError" in e:
            raise BoxeeClientAPIException(message, e)
        else:
            self.logError(message, e)
    
    def logError(self, message, e):
        return self.log.critical("%s: %s" % (message, e))
    
class BoxeeClientPermissionsException(BoxeeClientException):
    def __init__(self, message, e):
        Exception.__init__(self, message, e)
        self.log = self.setLogger("PermissionsException")
        self.logError(message, e)

class BoxeeClientAPIException(BoxeeClientException):
    def __init__(self, message, e):
        Exception.__init__(self, message, e)
        self.log = self.setLogger("APIException")
        self.logError(message, e)