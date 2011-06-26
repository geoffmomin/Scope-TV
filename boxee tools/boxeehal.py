"""
BOXEE BOX SYSTEN COMMUNICATIONS MODULE
This module can be used to communicate with the boxee box and alter system configuration.

Boxee HAL is like DBUS and makes communication from boxee to system configuration possible without a root account.
It is actually used by boxee to setup ethernet, wireless, clock,
power, input, storage, host, led, thermal ansystem configuration / status from the boxee os.

For more information regarding HAL please read the manual at:
http://tinyurl.com/boxeehal


Written by bartsidee
"""


try: import json
except: import simplejson as json
import socket

def get(CLASS, METHOD, DICT=None):
    HOST = '127.0.0.1'
    PORT = 5700
    if len(DICT) > 0:   PARAMS = buildParams(DICT)
    else:               PARAMS = None

    try:
      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error, msg:
      print "[ERROR] %s\n" % msg[1]
      return ''

    try:
      sock.connect((HOST, PORT))
    except socket.error, msg:
      print "[ERROR] %s\n" % msg[1]
      return ''

    sock.send("GET /%s.%s?%s HTTP/1.1\r\n\r\n" % (CLASS, METHOD, PARAMS) )
    
    string = ""
    data = sock.recv(1024)
    while True:
        data = sock.recv(1024)
        if not data: break
        string = "".join([string, data])

    sock.close()
    result = HalRead(string)
    return result

def HalRead(string):
    string = strstr(string, "Content-Length: ")
    if len(string) < 1:
        print "[ERROR] Result has no data"
        return {}
    string = strstr(string, "\r\n\r\n")
    try:    obj = json.loads(string)
    except: obj = {}
    return obj

def buildParams(dict):
    return "&".join( "=".join([str(k), str(v)]) for k,v in dict.items() )

def strstr(haystack, needle, offset=0):
    pos = haystack.find(needle, offset)
    if pos == -1:   return None
    else:           return haystack[pos:]
