# -*- coding: utf-8
# Copyright 2015 Kurt Momberg <kurtqm (at) yahoo(dot)com(dot)ar>
# > Based on work by Klimenko Artyem <aklim007(at)gmail(dot)com>
# >> Based on work by Rob Cherry <zsend(at)lxrb(dot)com>
# >>> Based on work by Enrico Tröger <enrico(dot)troeger(at)uvena(dot)de>
# License: GNU GPLv2

import socket
import struct
import time
import sys
import re

# If you're using an old version of python that don't have json available,
# you can use simplejson instead: https://simplejson.readthedocs.org/en/latest/
#import simplejson as json
import json


class pyZabbixSender:
    '''
    This class allows you to send data to a Zabbix server, using the same
    protocol used by the zabbix_server binary distributed by Zabbix.
    '''
    ZABBIX_SERVER = "127.0.0.1"
    ZABBIX_PORT   = 10051

    # Return codes when sending data:
    RC_OK            =   0  # Everything ok
    RC_ERR_FAIL_SEND =   1  # Error reported by zabbix when sending data
    RC_ERR_PARS_RESP =   2  # Error parsing server response
    RC_ERR_CONN      = 255  # Error talking to the server
    RC_ERR_INV_RESP  = 254  # Invalid response from server

    
    def __init__(self, server=ZABBIX_SERVER, port=ZABBIX_PORT, verbose=False):
        '''
        #####Description:
        This is the constructor, to obtain an object of type pyZabbixSender, linked to work with a specific server/port.
        #####Parameters:
        * **server**: [in] [string] [optional] This is the server domain name or IP. *Default value: "127.0.0.1"*
        * **port**: [in] [integer] [optional] This is the port open in the server to receive zabbix traps. *Default value: 10051*
        * **verbose**: [in] [boolean] [optional] This is to allow the library to write some output to stderr when finds an error. *Default value: False*
        **Note: The "verbose" parameter will be revisited and could be removed/replaced in the future**
        #####Return:
        It returns a pyZabbixSender object.
        '''
        self.zserver = server
        self.zport   = port
        self.verbose = verbose
        self.timeout = 5         # Socket connection timeout.
        self.__data = []         # This is to store data to be sent later.

        
    def __str__(self):
        '''
        This allows you to obtain a string representation of the internal data
        '''
        return str(self.__data)
        
        
    def __createDataPoint(self, host, key, value, clock=None):
        '''
        Creates a dictionary using provided parameters, as needed for sending this data.
        '''
        obj = {
            'host': host,
            'key': key,
            'value': value,
        }
        if clock:
            obj['clock'] = clock
        return obj

        
    def __send(self, mydata):
        '''
        This is the method that actually sends the data to the zabbix server.
        '''
        socket.setdefaulttimeout(self.timeout)
        data_length = len(mydata)
        data_header = str(struct.pack('q', data_length))
        data_to_send = 'ZBXD\1' + str(data_header) + str(mydata)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.zserver, self.zport))
            sock.send(data_to_send)
        except Exception, err:
            err_message = u'Error talking to server: %s\n' %str(err)
            sys.stderr.write(err_message)
            return self.RC_ERR_CONN, err_message

        response_header = sock.recv(5)
        if not response_header == 'ZBXD\1':
            err_message = u'Invalid response from server. Malformed data?\n---\n%s\n---\n' % str(mydata)
            sys.stderr.write(err_message)
            return self.RC_ERR_INV_RESP, err_message

        response_data_header = sock.recv(8)
        response_data_header = response_data_header[:4]
        response_len = struct.unpack('i', response_data_header)[0]
        response_raw = sock.recv(response_len)
        sock.close()
        response = json.loads(response_raw)
        match = re.match('^.*failed.+?(\d+).*$', response['info'].lower() if 'info' in response else '')
        if match is None:
            err_message = u'Unable to parse server response - \n%s\n' % str(response)
            sys.stderr.write(err_message)
            return self.RC_ERR_PARS_RESP, response
        else:
            fails = int(match.group(1))
            if fails > 0:
                if self.verbose is True:
                    err_message = u'Failures reported by zabbix when sending:\n%s\n' % str(mydata)
                    sys.stderr.write(err_message)
                return self.RC_ERR_FAIL_SEND, response
        return self.RC_OK, response


    def addData(self, host, key, value, clock=None):
        '''
        #####Description:
        Adds host, key, value and optionally clock to the internal list of data to be sent later, when calling one of the methods to actually send the data to the server.
        #####Parameters:
        * **host**: [in] [string] [mandatory] The host which the data is associated to.
        * **key**: [in] [string] [mandatory] The name of the trap associated to the host in the Zabbix server.
        * **value**: [in] [any] [mandatory] The value you want to send. Please note that you need to take care about the type, as it needs to match key definition in the Zabbix server. Numeric types can be specified as number (for example: 12) or text (for example: "12").
        * **clock**: [in] [integer] [optional] Here you can specify the Unix timestamp associated to your measurement. For example, you can process a log or a data file produced an hour ago, and you want to send the data with the timestamp when the data was produced, not when it was processed by you. If you don't specify this parameter, zabbix server will assign a timestamp when it receives the data.
            You can create a timestamp compatible with "clock" parameter using this code:
              int(round(time.time()))
              
            *Default value: None*
        #####Return:
        This method doesn't have a return.
        '''
        obj = self.__createDataPoint(host, key, value, clock)
        self.__data.append(obj)

        
    def clearData(self):
        '''
        #####Description:
        This method removes all data from internal storage. You need to specify when it's done, as it's not automatically done after a data send operation.
        #####Parameters:
        None
        #####Return:
        None
        '''
        self.__data = []
        
    
    def getData(self):
        '''
        #####Description:
        This method is used to obtain a copy of the internal data stored in the object.
        Please note you will **NOT** get the internal data object, but a copy of it, so no matter what you do with your copy, internal data will remain safe.
        #####Parameters:
        None
        #####Return:
        A copy of the internal data you added using the method *addData* (an array of dicts).
        '''
        copy_of_data = []
        for data_point in self.__data:
            copy_of_data.append(data_point.copy())    
        return copy_of_data
        
        
    def printData(self):
        '''
        #####Description:
        Print stored data (to stdout), so you can see what will be sent if "sendData" is called. This is useful for debugging purposes.
        #####Parameters:
        None
        #####Return:
        None
        '''
        for elem in self.__data:
            print str(elem)
        print 'Count: %d' % len(self.__data)


    def removeDataPoint(self, data_point):
        '''
        #####Description:
        This method delete one data point from the internal stored data. 
        It's main purpose is to narrow the internal data to keep only those failed data points (those that were not received/processed by the server) so you can identify/retry them. Data points can be obtained from *sendDataOneByOne* return, or from *getData* return.
        #####Parameters:
        * **data_point**: [in] [dict] [mandatory] This is a dictionary as returned by *sendDataOneByOne()* or *getData* methods.
        #####Return:
        It returns True if data_point was found and deleted, and False if not.
        '''
        if data_point in self.__data:
            self.__data.remove(data_point)
            return True
        
        return False
        
        
    def sendData(self, packet_clock=None, max_data_per_conn=None):
        '''
        #####Description:
        Sends data stored using *addData* method, to the Zabbix server.
        #####Parameters:
        * **packet_clock**: [in] [integer] [optional] Zabbix server uses the "clock" parameter in the packet to associate that timestamp to all data values not containing their own clock timestamp. Then:
            * If packet_clock is specified, zabbix server will associate it to all data values not containing their own clock.
            * If packet_clock is **NOT** specified, zabbix server will use the time when it received the packet as packet clock.
         You can create a timestamp compatible with "clock" or "packet_clock" parameters using this code:
              int(round(time.time()))
         *Default value: None*
              
        * **max_data_per_conn**: [in] [integer] [optional] Allows the user to limit the number of data points sent in one single connection, as some times a too big number can produce problems over slow connections. 
            Several "sends" will be automatically performed until all data is sent.
            If omitted, all data points will be sent in one single connection. *Default value: None*
         
        Please note that **internal data is not deleted after *sendData* is executed**. You need to call *clearData* after sending it, if you want to remove currently stored data.
        #####Return:
        A list of *(return_code, msg_from_server)* associated to each "send" operation.
        '''
        if not max_data_per_conn or max_data_per_conn > len(self.__data):
            max_data_per_conn = len(self.__data)

        responses = []
        i = 0
        while i*max_data_per_conn < len(self.__data):

            sender_data = {
                "request": "sender data",
                "data": [],
            }
            if packet_clock:
                sender_data['clock'] = packet_clock

            sender_data['data'] = self.__data[i*max_data_per_conn:(i+1)*max_data_per_conn]
            to_send = json.dumps(sender_data)

            response = self.__send(to_send)
            responses.append(response)
            i += 1

        return responses


    def sendDataOneByOne(self):
        '''
        #####Description:
        You can use this method to send all stored data, one by one, to determine which traps are not being handled correctly by the server.
        Using this method you'll be able to detect things like:
        * hosts not defined in the server
        * traps not defined in some particular host
        This is primarily intended for debugging purposes.
        #####Parameters:
        None
        #####Return:
        It returns an array of return codes (one for each individual "send") and the data sent: \[\[code\_1, data\_point\_1], \[code\_2, data\_point\_2\]\]
        '''
        retarray = []
        for i in self.__data:
            if 'clock' in i:
                (retcode, retstring) = self.sendSingle(i['host'], i['key'], i['value'], i['clock'])
            else:
                (retcode, retstring) = self.sendSingle(i['host'], i['key'], i['value'])

            retarray.append((retcode, i))
        return retarray


    def sendSingle(self, host, key, value, clock=None):
        '''
        #####Description:
        Instead of storing data for sending later, you can use this method to send specific values right now.
        #####Parameters:
        It shares the same parameters as the *addData* method.
        * **host**: [in] [string] [mandatory] The host which the data is associated to.
        * **key**: [in] [string] [mandatory] The name of the trap associated to the host in the Zabbix server.
        * **value**: [in] [any] [mandatory] The value you want to send. Please note that you need to take care about the type, as it needs to match key definition in the Zabbix server. Numeric types can be specified as number (for example: 12) or text (for example: "12").
        * **clock**: [in] [integer] [optional] Here you can specify the Unix timestamp associated to your measurement. For example, you can process a log or a data file produced an hour ago, and you want to send the data with the timestamp when the data was produced, not when it was processed by you. If you don't specify this parameter, zabbix server will assign a timestamp when it receives the data.
            You can create a timestamp compatible with "clock" parameter using this code:
              int(round(time.time()))
              
            *Default value: None*
        #####Return:
        A list containing the return code and the message returned by the server.
        '''
        sender_data = {
            "request": "sender data",
            "data": [],
        }

        obj = self.__createDataPoint(host, key, value, clock)
        sender_data['data'].append(obj)
        to_send = json.dumps(sender_data)
        return self.__send(to_send)


        
#####################################
# --- Examples of usage ---
#####################################
#
# Initiating a pyZabbixSender object -
# z = pyZabbixSender() # Defaults to using ZABBIX_SERVER,ZABBIX_PORT
# z = pyZabbixSender(verbose=True) # Prints all sending failures to stderr
# z = pyZabbixSender(server="172.0.0.100",verbose=True)
# z = pyZabbixSender(server="zabbix-server",port=10051)
# z = pyZabbixSender("zabbix-server", 10051)

# --- Adding data to send later ---
# Host, Key, Value are all necessary
# z.addData("test_host","test_trap","12")
#
# Optionally you can provide a specific timestamp for the sample
# z.addData("test_host","test_trap","13",1365787627)
#
# If you provide no timestamp, you still can assign one when sending, or let
# zabbix server to put the timestamp when the message is received.

# --- Printing values ---
# Not that useful, but if you would like to see your data in tuple form:
# z.printData()

# --- Sending data ---
#
# Just sending a single data point (you don't need to call add_value for this
# to work):
# z.sendSingle("test_host","test_trap","12")
#
# Sending everything at once, with no concern about
# individual item failure -
#
# result = z.sendData()
# for r in result:
#     print "Result: %s -> %s" % (str(r[0]), r[1])
#
# If you're ok with the result, you can delete the data inside the sender, to
# allow a new round of data feed/send.
# z.clearData()
#
# If you want to specify a timestamp to all values without one, you can specify
# the packet_clock parameter:
# z.sendData(packet_clock=1365787627)
#
# When you're sending data over a slow connection, you may find useful the
# possibility to send data in packets with no more than max_data_per_conn
# data points on it.
# All the data will be sent, but in smaller packets.
# For example, if you want to send 4000 data points in packets containing no
# more than 200 of them:
#
# results = z.sendData(max_data_per_conn=200)
# for partial_result in results:
#     print partial_result
#
# Sending every item individually so that we can capture
# success or failure
#
# results = z.sendDataOneByOne()
# for (code,data) in results:
#   if code != z.RC_OK:
#      print "Failed to send: %s" % str(data)
#
#
#####################################
# Mini example of a working program #
#####################################
#
# import sys
# sys.path.append("/path/to/pyZabbixSender.py")
# from pyZabbixSender import pyZabbixSender
#
# z = pyZabbixSender() # Defaults to using ZABBIX_SERVER, ZABBIX_PORT
# z.addData("test_host","test_trap_1","12")
# z.addData("test_host","test_trap_2","13",1366033479)
# 
# Two ways of printing internal data
# z.printData()
# print z
#
# results = z.sendDataOneByOne()
# for (code,data) in results:
#   if code != z.RC_OK:
#      print "Failed to send: %s" % str(data)
# z.clearData()
#####################################
