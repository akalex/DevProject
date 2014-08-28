import getopt
import os
import time
import urllib2
from urllib2 import Request, urlopen, URLError
import socket
import sys
import httplib
from urlparse import urlparse

# These are the sequences need to get colored output
BLUE = '\033[94m'
RED = '\033[91m'
GREEN = '\033[32m'

# Class Dir_admin : inherits from the base class object. New-style Classes
# Mandatory and optional args can be identified with the __init__ method
class Dir_admin(object):

    #Dir_admin Comment : constructor - takes one parameter. This is arguments received from main.py wrapper.
    def __init__(self, arg):
        #Dir_admin Comment :  User variables
        self.site = None
        self.dict_file = None
        self.logging = False
        self.log_file = None

        # Parse arguments.
        if self.parse_arg(arg):
            self.usage()
            return

        # Calls method, that will perform some actions.
        self.perform()

    def usage(self):
        '''
        Method that shows information about how to use this tool.
        '''

        print """
Admin command usage:
    -s <site_url>
    -f <scanning_dict_file>
    -l (logging function)
    -h (help)
"""

    def parse_arg(self, arg):
        '''
        Method parse_arg.
        :param arg: list. arguments from stdin.
        :return: 0 - success, -1 - failed
        '''

        # Check that there is no empty arg.
        if len(arg) == 0:
            return -1

        # Create exception.
        # try to parse arguments
        try:
            #The getopt is the standard python module for parsing args
            #(see python reference documentation : http://docs.python.org/lib/module-getopt.html)
            #Here we search for args beginning with s,k,f,x,d,t,c,w,e,o that need a value, and args h,v,n
            #The list(inside []), refers to the long options.
            #
            # argv[1:] returns a list that begins with element 1 of argv
            # exemple : argv = ['a','b','c']
            #           argv[1:] will be ['b','c']
            #           argv[2:] will be ['c']
            #
            #The getopt returns a tuple.
            #Here, opts is a list of tuple containing the options type and the values
            #args is the extra paramaters
            #For exemple :
            #    opts, args = getopt.getopt(['-h','-s','10','url'],"s:f:lh")
            #will return
            #    opts = [('-h',''),('-s','10')]
            #    args = ['url']
            cmd_opts = "s:f:lh"
            opts, args = getopt.getopt(arg, cmd_opts)
        # run exception if were caught any errors.
        except getopt.GetoptError:
            return -1

        # Here we check options returned in by getopt
        # we make a for statement on this list
        # o and a are iterator on option type and args values
        # for exemple if opts = [('-h',''),('-s','3')]
        # first loop : opt = '-h' and a= ''
        # second loop : opt = '-s' and a='3'
        # Options are registered in member class variables.
        for opt in opts:
            if opt[0] == "-s":
                self.site = opt[1]
            elif opt[0] == "-f":
                self.dict_file = opt[1]
            elif opt[0] == "-l":
                self.logging = True
            else:
                return -1

        return 0

    def perform(self):
        '''
        Main method of the class that perform all actions.

        '''

        socket.setdefaulttimeout(10) #  Set the default timeout in seconds (float) for new socket objects.
                                     # A value of None indicates that new socket objects have no timeout.
                                     # When the socket module is first imported, the default is None.

        # Create exception.
        try:
            # Parse a URL into six components, returning a 6-tuple.
            parse=urlparse(self.site)
            # Parse hostname in lower case.
            name=parse.netloc
            # User variables
            tot=0
            found=0

            # if self.logging
            # we use default parameters. Log file will be created in current location.
            if self.logging:
                # Get current path
                cur_path = os.path.realpath(os.path.dirname(__file__))
                # Create path to directory "logs"
                dirname = os.path.join(cur_path, 'logs')
                # Check if dir already exists
                if os.path.exists(dirname) == False:
                    # Create dir if not exists
                    os.mkdir(dirname)
                # Initialize class attribute self.log_file.
                self.log_file = dirname+"/"+name+".log"

            # Try to request URL
            try:
                print (GREEN+"\n\tChecking website " + self.site + "...")
                # Make a request
                conn = urllib2.Request(self.site)
                # Open the URL url, which can be either a string or a Request object.
                urllib2.urlopen(self.site)
                print RED+"\t[V]"+GREEN+" Yes... Server is Online."+GREEN
            # Catch HTTPError
            except (urllib2.HTTPError) as Exit:
                print(GREEN+"\t[!] Oops Error occured")
                return
            # Catch any other errors
            except:
                return

            try:
                # Create list of files
                dict_list = open(self.dict_file, "r")
            # Print error, if there is no File
            except(IOError):
                print GREEN+"File Not Found!"
                return
            # Read all the lines of a file in a list
            dirs = dict_list.readlines()
            # Iterate through list of dirs
            for dirz in dirs:
                # Replace "\n" to ""
                dirz=dirz.replace("\n","")
                # Concatenate two string
                dirz="/"+dirz
                url_z=self.site+dirz
                print(RED+"--> "+GREEN+"Checking "+ BLUE + url_z)
                # Make a request
                req=Request(url_z)
                # Suspend execution for the given number of seconds.
                time.sleep(2)
                try:
                    # Open the URL url, which can be either a string or a Request object.
                    response = urlopen(req)
                # Catch URLError with the code
                except URLError, e:
                    if hasattr(e, 'reason'):
                        print(RED+"\t[x] "+GREEN+"Not Found")
                        tot=tot+1
                    elif hasattr(e, 'code'):
                        print(RED+"\t[x] "+GREEN+"Not Found")
                        tot=tot+1
                # Write into the file all results
                else:
                    found_url=url_z
                    print(RED+"\t>>>"+GREEN+" Found "+RED+found_url)
                    if self.logging:
                        try:
                            # Open for reading and writing.  The file is created if it does not
                            # exist.  The stream is positioned at the end of the file.  Subse-
                            # quent writes to the file will always end up at the then current
                            # end of file, irrespective of any intervening fseek(3) or similar.
                            logs=open(self.log_file, "a+")
                        except(IOError):
                            print RED+"\t[x] Failed to create DirLogs.log"
                        # Write list of string into file
                        logs.writelines(found_url+"\n")
                        logs.close()
                    # Increments the counters
                    found=found+1
                    tot=tot+1
            # Next lines just print the following text
            print BLUE+"\t\nTotal scanned:",tot
            print GREEN+"\tFound:",found
            if self.logging:
                print RED+"\nFounded Logs are saved in %s.log, Read it" %(name)
            print GREEN+"\n"
        # Class whose instances are returned upon successful connection
        # Though being an exception (a subclass of URLError), an HTTPError can also function as a non-exceptional
        # file-like return value (the same thing that urlopen() returns). This is useful when handling exotic HTTP
        # errors, such as requests for authentication.
        # This exception is raised for socket-related errors.
        except (httplib.HTTPResponse, urllib2.HTTPError, socket.error):
            print "\n\t[!] Session Cancelled; Error occured. Check internet settings"
            print RED+"\n\t[!] Session cancelled"
            print BLUE+"\t\nTotal scanned:",tot
            print GREEN+"\tFound:",found
            if self.logging:
                print RED+"\nFounded Logs are saved in"+GREEN+" %s"+RED+", Read it" %(self.log_file)
            print GREEN+"\n"
        except (KeyboardInterrupt, SystemExit):
            print RED+"\n\t[!] Session cancelled"
            print BLUE+"\t\nTotal scanned:",RED,tot
            print GREEN+"\tFound:",RED,found
            if self.logging:
                print GREEN+"\nFounded Logs are saved in \""+RED+"/%s"%(self.log_file)+GREEN+"\" , Read it"
            print GREEN+"\n"