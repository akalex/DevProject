#!/usr/bin/env python
# SIPvicious password cracker - svcrack


from libs.svhelper import __version__
__prog__   = 'svcrack'
import socket
import select
import random
import logging
import base64
import time
import anydbm
import os


# Class ASipOfRedWine : inherits from the base class object. New-style Classes
# Mandatory and optional args can be identified with the __init__ method
class ASipOfRedWine(object):
    #ASipOfRedWine Comment : constructor - takes one parameter. This is arguments received from main.py wrapper
    def __init__(self,host='localhost',bindingip='',localport=5060,port=5060,
                 externalip=None,
                 username=None,crackmode=1,crackargs=None,realm=None,sessionpath=None,
                 selecttime=0.005,compact=False,reusenonce=False,extension=None,
                 maxlastrecvtime=10,domain=None):
        # Import additional module
        from libs.svhelper import dictionaryattack, numericbrute, packetcounter
        # Return a logger with the specified name or, if no name is specified, return a logger which is the root
        # logger of the hierarchy. If specified, the name is typically a dot-separated hierarchical name like "a",
        # "a.b" or "a.b.c.d". Choice of these names is entirely up to the developer who is using logging.
        self.log = logging.getLogger('ASipOfRedWine')
        # Create a new socket using the given address family, socket type and protocol number.
        # The address family should be AF_INET (the default), AF_INET6 or AF_UNIX.
        # The socket type should be SOCK_STREAM (the default), SOCK_DGRAM or perhaps one of the other SOCK_ constants.
        # The protocol number is usually zero and may be omitted in that case.
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        # Set a timeout on blocking socket operations. The value argument can be a nonnegative float expressing seconds, or None.
        self.sock.settimeout(10)
        self.sessionpath = sessionpath
        self.maxlastrecvtime = maxlastrecvtime
        self.lastrecvtime = time.time()
        self.dbsyncs = False
        if self.sessionpath is not  None:
            # Open the database file filename and return a corresponding object.
            self.resultpasswd = anydbm.open(
                os.path.join(self.sessionpath,'resultpasswd'),'c'
                )
            try:
                # When the database has been opened in fast mode, this method forces any unwritten data to be
                # written to the disk.
                self.resultpasswd.sync()
                self.dbsyncs = True
                # Print log string
                self.log.info("Db does sync")
            # Raised when an attribute reference (see Attribute references) or assignment fails.
            except AttributeError:
                self.log.info("Db does not sync")
                pass
        else:
            self.resultpasswd = dict()
        self.nomore = False
        self.passwordcracked = False
        self.rlist = [self.sock]
        self.wlist = list()
        self.xlist = list()
        self.challenges = list()        
        self.crackmode = crackmode
        self.crackargs = crackargs
        self.dsthost,self.dstport =host,int(port)
        self.domain = self.dsthost
        if domain:
            self.domain = domain
        # Create generator
        if crackmode == 1:
            self.passwdgen = numericbrute(*crackargs)
        elif crackmode == 2:
            self.passwdgen = dictionaryattack(crackargs)        
            
        self.username = username
        self.realm = realm
        self.selecttime = selecttime
        self.dstisproxy = None
        self.ignorenewnonce = True
        self.noauth = False
        self.auth = dict()
        self.previouspassword = str()
        self.compact=compact
        self.reusenonce = reusenonce
        self.staticnonce = None
        self.staticcid = None
        if extension is not None:
            self.extension = extension
        else:
            self.extension = username
        self.bindingip = bindingip
        self.localport = localport
        self.originallocalport = localport
        if self.sessionpath is not None:
            self.packetcount = packetcounter(50)
        if externalip is None:
            self.log.debug("external ip was not set")
            if (self.bindingip != '0.0.0.0') and (len(self.bindingip) > 0):
                self.log.debug("but bindingip was set! we'll set it to the binding ip")
                self.externalip = self.bindingip
            else:
                try:
                    self.log.info("trying to get self ip .. might take a while")
                    self.externalip = socket.gethostbyname(socket.gethostname())
                except socket.error:
                    self.externalip = '127.0.0.1'
        else:
            self.log.debug("external ip was set")
            self.externalip = externalip

    # Set default parameter for SIP
    PROXYAUTHREQ = 'SIP/2.0 407 '
    AUTHREQ = 'SIP/2.0 401 '
    OKEY = 'SIP/2.0 200 '
    NOTFOUND = 'SIP/2.0 404 '
    INVALIDPASS = 'SIP/2.0 403 '
    TRYING = 'SIP/2.0 100 '
    
        

    def Register(self,extension,remotehost,auth=None,cid=None):
        '''
        Method for registration
        :param extension: string
        :param remotehost: string
        :param auth: string, default = None
        :param cid: string, default = None
        :return object
        '''
        from libs.svhelper import makeRequest
        from libs.svhelper import createTag
        m = 'REGISTER'
        # Generate new cid, by default it not set
        # Returns a python long int with k random bits.
        if cid is None:
            cid='%s' % str(random.getrandbits(32))
        # Do the same thing for variable branchunique
        branchunique = '%s' % random.getrandbits(32)
        cseq = 1
        localtag=str(random.getrandbits(32))
        contact = 'sip:%s@%s' % (extension,remotehost)
        if auth is not None:
            cseq = 2
            localtag=createTag('%s:%s' % (self.auth['username'],self.auth['password']))
        # Make a registration request.
        # More about SIP registration http://tools.ietf.org/search/rfc3261#page-56
        register = makeRequest(
                                    m,
                                    '"%s" <sip:%s@%s>' % (extension,extension,self.domain),
                                    '"%s" <sip:%s@%s>' % (extension,extension,self.domain),
                                    self.domain,
                                    self.dstport,
                                    callid=cid,
                                    srchost=self.externalip,
                                    branchunique=branchunique,
                                    cseq=cseq,
                                    auth=auth,
                                    localtag=localtag,
                                    compact=self.compact,
                                    localport=self.localport
                                  )
        return register

    def getResponse(self):
        """
        Method that get Response from server

        :return:
        """
        from libs.svhelper import getNonce,getCredentials,getRealm,getCID
        # we got stuff to read off the socket              
        buff,srcaddr = self.sock.recvfrom(8192)
        if buff.startswith(self.PROXYAUTHREQ):
            self.dstisproxy = True
        elif buff.startswith(self.AUTHREQ):
            self.dstisproxy = False
        if buff.startswith(self.PROXYAUTHREQ) or buff.startswith(self.AUTHREQ):
            nonce = getNonce(buff)
            cid  = getCID(buff)
            if self.realm is None:
                self.realm = getRealm(buff)
            if None not in (nonce,self.realm):
                if self.reusenonce:
                    if len(self.challenges) > 0:
                        return
                    else:
                        self.staticnonce = nonce
                        self.staticcid = cid
                self.challenges.append([nonce,cid])
        elif buff.startswith(self.OKEY):
            self.passwordcracked = True
            _tmp = getCredentials(buff)            
            if (_tmp is not None) and (len(_tmp) == 2): 
                crackeduser,crackedpasswd = _tmp
                self.log.info("The password for %s is %s" % (crackeduser,crackedpasswd))
                self.resultpasswd[crackeduser] = crackedpasswd
                if self.sessionpath is not None and self.dbsyncs:
                    self.resultpasswd.sync()
            else:
                self.log.info("Does not seem to require authentication")
                self.noauth = True
                self.resultpasswd[self.username] = '[no password]'
        elif buff.startswith(self.NOTFOUND):
            self.log.warn("User not found")
            self.noauth = True
        elif buff.startswith(self.INVALIDPASS):
            pass
        elif buff.startswith(self.TRYING):
            pass
        else:
            self.log.error("We got an unknown response")
            self.log.debug(`buff`)
            self.nomore = True

    def start(self):
        """
        Method that start perfom some actions.

        :return:
        """
        #from libs.svhelper import ,getCredentials,getRealm,getCID
        import socket, pickle
        from libs.svhelper import mysendto
        if self.bindingip == '':
            bindingip = 'any'
        else:
            bindingip = self.bindingip
        self.log.debug("binding to %s:%s" % (bindingip,self.localport))
        while 1:
            # Check if there any ports are available, print error message if not.
            if self.localport > 65535:
                self.log.critical("Could not bind to any port")
                return
            try:
                # Bind the socket to address. The socket must not already be bound.
                self.sock.bind((self.bindingip,self.localport))
                break
            # This exception is raised for socket-related errors. The accompanying value is either a string telling
            # what went wrong or a pair (errno, string) representing an error returned by a system call, similar
            # to the value accompanying os.error.
            except socket.error:
                self.log.debug("could not bind to %s" % self.localport)
                self.localport += 1            
        if self.originallocalport != self.localport:
            self.log.warn("could not bind to %s:%s - some process might already be listening on this port. Listening on port %s instead" % (self.bindingip,self.originallocalport, self.localport))
            self.log.info("Make use of the -P option to specify a port to bind to yourself")

        # perform a test 1st ..
        # and try to register
        data = self.Register(self.extension,self.domain)
        try:
            mysendto(self.sock,data,(self.dsthost,self.dstport))
        except socket.error,err:
            self.log.error("socket error: %s" % err)
            return
        try:
            self.getResponse()
            self.lastrecvtime = time.time()
        except socket.timeout:
            self.log.error("no server response")
            return
        except socket.error,err:
            self.log.error("socket error:%s" % err)
            return
        if self.noauth is True:
            return
        while 1:
            r, w, e = select.select(
                self.rlist,
                self.wlist,
                self.xlist,
                self.selecttime
                )
            if r:
                if self.passwordcracked:
                    break                
                # we got stuff to read off the socket
                try:
                    self.getResponse()
                    self.lastrecvtime = time.time()
                except socket.error,err:
                    self.log.warn("socket error: %s" % err)
            else:
                # check if its been a while since we had a response to prevent
                # flooding - otherwise stop
                timediff = time.time() - self.lastrecvtime
                if timediff > self.maxlastrecvtime:
                    self.nomore = True
                    self.log.warn('It has been %s seconds since we last received a response - stopping' % timediff)
                    continue
                if self.passwordcracked:
                    break
                if self.nomore is True:
                    try:
                        while not self.passwordcracked:
                                self.getResponse()
                    except socket.timeout:
                        break
                # no stuff to read .. its our turn to send back something
                if len(self.challenges) > 0:
                    # we have challenges to take care of
                    self.auth = dict()
                    self.auth['username'] = self.username
                    self.auth['realm'] = self.realm
                    if self.reusenonce:
                        self.auth['nonce'] = self.staticnonce
                        cid = self.staticcid
                    else:
                        self.auth['nonce'],cid = self.challenges.pop()
                    self.auth['proxy'] = self.dstisproxy 
                    try:                        
                        self.auth['password'] = self.passwdgen.next()
                        self.previouspassword = self.auth['password']
                        self.log.debug('trying %s' % self.auth['password'])
                    except StopIteration:
                        self.log.info("no more passwords")
                        self.nomore = True
                        continue
                else:
                    self.auth = None
                    cid = None
                data = self.Register(self.extension,self.domain,self.auth,cid)                
                try:
                    mysendto(self.sock,data,(self.dsthost,self.dstport))
                    #self.sock.sendto(data,(self.dsthost,self.dstport))
                    if self.sessionpath is not None:
                        if self.packetcount.next():                    
                            try:                                    
                                if self.crackmode == 1:
                                    pickle.dump(self.previouspassword,open(os.path.join(self.sessionpath,'lastpasswd.pkl'),'w'))
                                    self.log.debug('logged last extension %s' % self.previouspassword)
                                elif self.crackmode == 2:
                                    pickle.dump(self.crackargs.tell(),open(os.path.join(self.sessionpath,'lastpasswd.pkl'),'w'))
                                    self.log.debug('logged last position %s' % self.crackargs.tell())
                            except IOError:
                                self.log.warn('could not log the last extension scanned')                    
                except socket.error,err:
                    self.log.error("socket error: %s" % err)
                    break

# Class SVCRACK : inherits from the base class object. New-style Classes
# Mandatory and optional args can be identified with the __init__ method
class SVCRACK(object):

    #SVCRACK Comment :  beware if you change anything below - execution starts here
    def main(self):
        #Here is the main function of the class.
        #Note that it's just a name unlike java...
        #See below for the entry point of the program.

        from optparse import OptionParser
        from datetime import datetime
        from libs.svhelper import getRange, resumeFrom,calcloglevel
        from sys import exit
        import logging
        import pickle
        from libs.svhelper import standardoptions, standardscanneroptions

        usage = "usage: %prog -u username [options] target\r\n"
        usage += "examples:\r\n"
        usage += "%prog svcrack -u100 -d dictionary.txt 10.0.0.1\r\n"
        usage += "%prog svcrack -u100 -r1-9999 -z4 10.0.0.1\r\n"
        # Parse arguments.
        # The OptionParser constructor has no required arguments, but a number of optional keyword arguments.
        # You should always pass them as keyword arguments, i.e. do not rely on the order in which the arguments are declared.
        # More about this method of parsing, see there http://docs.python.org/2/library/optparse.html#optparse.OptionParser
        parser = OptionParser(usage,version="%prog v"+str(__version__))
        parser = standardoptions(parser)
        parser = standardscanneroptions(parser)
        parser.add_option("-u", "--username", dest="username",
                      help="username to try crack", metavar="USERNAME")
        parser.add_option("-d", "--dictionary", dest="dictionary", type="string",
                      help="specify a dictionary file with passwords",
                      metavar="DICTIONARY")
        parser.add_option("-r", "--range", dest="range", default="100-999",
                      help="specify a range of numbers. example: 100-200,300-310,400",
                      metavar="RANGE")
        parser.add_option("-e", "--extension", dest="extension",
                      help="Extension to crack. Only specify this when the extension is different from the username.",
                      metavar="EXTENSION")
        parser.add_option("-z", "--zeropadding", dest="zeropadding", type="int", default=0,
                      help="""the number of zeros used to padd the password.
                      the options "-r 1-9999 -z 4" would give 0001 0002 0003 ... 9999""",
                      metavar="PADDING")
        parser.add_option("-n", "--reusenonce", dest="reusenonce", default=False,
                      help="Reuse nonce. Some SIP devices don't mind you reusing the nonce (making them vulnerable to replay attacks). Speeds up the cracking.",
                      action="store_true",
                      )
        parser.add_option('--template', '-T', action="store", dest="template",
                      help="""A format string which allows us to specify a template for the extensions
                      example svwar.py -e 1-999 --template="123%#04i999" would scan between 1230001999 to 1230999999"
                      """)
        parser.add_option('--maximumtime', action='store', dest='maximumtime', type="int",
                      default=10,
                      help="""Maximum time in seconds to keep sending requests without
                      receiving a response back""")
        parser.add_option('--enabledefaults', '-D', action="store_true", dest="defaults",
                      default=False, help="""Scan for default / typical passwords such as
                      1000,2000,3000 ... 1100, etc. This option is off by default.
                      Use --enabledefaults to enable this functionality""")
        parser.add_option('--domain', dest="domain",
                      help="force a specific domain name for the SIP message, eg. -d example.org")
        (options, args) = parser.parse_args()
        exportpath = None
        # Does basic configuration for the logging system by creating a StreamHandler with a default
        # Formatter and adding it to the root logger. The functions debug(), info(), warning(), error() and
        # critical() will call basicConfig() automatically if no handlers are defined for the root logger.
        logging.basicConfig(level=calcloglevel(options))
        logging.debug('started logging')

        if options.resume is not None:
            exportpath = os.path.join('.sipvicious',__prog__,options.resume)
            if os.path.exists(os.path.join(exportpath,'closed')):
                # Logs a message with level ERROR on the root logger.
                logging.error("Cannot resume a session that is complete")
                exit(1)
            if not os.path.exists(exportpath):
                # Logs a message with level CRITICAL on the root logger.
                logging.critical('A session with the name %s was not found'% options.resume)
                exit(1)
            optionssrc = os.path.join(exportpath,'options.pkl')
            previousresume = options.resume
            previousverbose = options.verbose
            # Read a string from the open file object file and interpret it as a pickle data stream,
            # reconstructing and returning the original object hierarchy. This is equivalent to Unpickler(file).load().
            # More about pickle http://docs.python.org/2/library/pickle.html
            options,args = pickle.load(open(optionssrc,'r'))
            options.resume = previousresume
            options.verbose = previousverbose
        elif options.save is not None:
            exportpath = os.path.join('.sipvicious',__prog__,options.save)
            logging.debug('Session path: %s' % exportpath)
    
        if options.resume is not None:
            exportpath = os.path.join('.sipvicious',__prog__,options.resume)
            if not os.path.exists(exportpath):
                logging.critical('A session with the name %s was not found'% options.resume)
                exit(1)
            optionssrc = os.path.join(exportpath,'options.pkl')
            previousresume = options.resume
            previousverbose = options.verbose
            options,args = pickle.load(open(optionssrc,'r'))
            options.resume = previousresume
            options.verbose = previousverbose
        elif options.save is not None:
            exportpath = os.path.join('.sipvicious',__prog__,options.save)
        # Check that there is no empty arg.
        if len(args) == 1:
            parser.error("provide one hostname")
        else:
            host=args[1]
        
        if options.username is None:
            parser.error("provide one username to crack")

        if options.dictionary is not None:
            crackmode=2
            try:
                dictionary = open(options.dictionary,'r')
            except IOError:
                # Logs a message with level ERROR on the root logger.
                logging.error("could not open %s" % options.dictionary)
            if options.resume is not None:
                lastpasswdsrc = os.path.join(exportpath,'lastpasswd.pkl')
                previousposition = pickle.load(open(lastpasswdsrc,'r'))
                dictionary.seek(previousposition)
            crackargs = dictionary
        else:
            crackmode = 1
            if options.resume is not None:
                lastpasswdsrc = os.path.join(exportpath,'lastpasswd.pkl')
                try:
                    previouspasswd = pickle.load(open(lastpasswdsrc,'r'))
                except IOError:
                    logging.critical('Could not read from %s' % lastpasswdsrc)
                    exit(1)
                # Logs a message with level DEBUG on the root logger.
                logging.debug('Previous range: %s' % options.range)
                options.range = resumeFrom(previouspasswd,options.range)
                logging.debug('New range: %s' % options.range)
                # Logs a message with level INFO on the root logger.
                logging.info('Resuming from %s' % previouspasswd)
            rangelist = getRange(options.range)
            crackargs = (rangelist,options.zeropadding,options.template,options.defaults,[options.username])
        if options.save is not None:
            if options.resume is None:
                exportpath = os.path.join('.sipvicious',__prog__,options.save)
                if os.path.exists(exportpath):
                    logging.warn('we found a previous scan with the same name. Please choose a new session name')
                    exit(1)
                logging.debug('creating an export location %s' % exportpath)
                try:
                    # Change permission for directory
                    os.makedirs(exportpath,mode=0700)
                except OSError:
                    logging.critical('could not create the export location %s' % exportpath)
                    exit(1)
                optionsdst = os.path.join(exportpath,'options.pkl')
                logging.debug('saving options to %s' % optionsdst)
                # Write a pickled representation of obj to the open file object file.
                pickle.dump([options,args],open(optionsdst,'w'))
        if options.autogetip:
            # Create a new socket using the given address family, socket type and protocol number.
            # The address family should be AF_INET (the default), AF_INET6 or AF_UNIX. The socket type should be
            # SOCK_STREAM (the default), SOCK_DGRAM or perhaps one of the other SOCK_ constants. The protocol number
            # is usually zero and may be omitted in that case.
            tmpsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Connect to a remote socket at address.
            tmpsocket.connect(("msn.com",80))
            # Return the socket's own address. This is useful to find out the port number of an IPv4/v6 socket, for instance.
            options.externalip=tmpsocket.getsockname()[0]
            # Close the socket. All future operations on the socket object will fail.
            tmpsocket.close()
        #We call an instance of the class ASipOfRedWine defined above
        sipvicious = ASipOfRedWine(
                        host,
                        username=options.username,
                        selecttime=options.selecttime,
                        compact=options.enablecompact,
                        crackmode=crackmode,
                        crackargs=crackargs,
                        reusenonce=options.reusenonce,
                        extension=options.extension,
                        sessionpath=exportpath,
                        port=options.port,
                        externalip=options.externalip,
                        maxlastrecvtime=options.maximumtime,
                        localport=options.localport,
                        domain=options.domain
                        )
        # Get current date and time
        start_time = datetime.now()
        logging.info("scan started at %s" % str(start_time))
        try:
            # Call method start. That will start perform crack operations
            sipvicious.start()
            if exportpath is not None:
                open(os.path.join(exportpath,'closed'),'w').close()
        except KeyboardInterrupt:
            logging.warn('caught your control^c - quiting')
        except Exception, err:
            logging.exception( "Exception" )
        if options.save is not None and sipvicious.previouspassword is not None:
            lastextensiondst = os.path.join(exportpath,'lastpasswd.pkl')
            logging.debug('saving state to %s' % lastextensiondst)
            try:
                if crackmode == 1:
                    pickle.dump(sipvicious.previouspassword,open(os.path.join(exportpath,'lastpasswd.pkl'),'w'))
                    logging.debug('logged last password %s' % sipvicious.previouspassword)
                elif crackmode == 2:
                    pickle.dump(sipvicious.crackargs.tell(),open(os.path.join(exportpath,'lastpasswd.pkl'),'w'))
                    logging.debug('logged last position %s' % sipvicious.crackargs.tell())
            except IOError:
                logging.warn('could not log the last tried password')
        # display results
        if not options.quiet:
            lenres = len(sipvicious.resultpasswd)
            if lenres > 0:
                logging.info("we have %s cracked users" % lenres)
                if (lenres < 400 and options.save is not None) or options.save is None:
                    from libs.pptable import indent,wrap_onspace
                    width = 60
                    labels = ('Extension','Password')
                    rows = list()
                    for k in sipvicious.resultpasswd.keys():
                        rows.append((k,sipvicious.resultpasswd[k]))
                    print indent([labels]+rows,hasHeader=True,
                        prefix='| ', postfix=' |',wrapfunc=lambda x: wrap_onspace(x,width))
                else:
                    logging.warn("too many to print - use svreport for this")
            else:
                logging.warn("found nothing")
        end_time = datetime.now()
        total_time = end_time - start_time
        logging.info("Total time: %s" % total_time)
