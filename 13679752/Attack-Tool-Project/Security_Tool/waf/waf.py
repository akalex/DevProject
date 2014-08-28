import getopt
import os
from urllib import quote
import logging
import sys
import random
from libs.evillib import *

class myengine(waftoolsengine):
    """
    WAF detection tool
    """

    AdminFolder = '/Admin_Files/'
    xssstring = '<script>alert(1)</script>'
    dirtravstring = '../../../../etc/passwd'
    cleanhtmlstring = '<invalid>hello'
    isaservermatch = 'Forbidden ( The server denied the specified Uniform Resource Locator (URL). ' \
                     'Contact the server administrator.  )'

    def __init__(self,target='www.microsoft.com',port=80,ssl=False,
                 debuglevel=0,path='/',followredirect=True):
        """
        target: the hostname or ip of the target server
        port: defaults to 80
        ssl: defaults to false
        """
        waftoolsengine.__init__(self,target,port,ssl,debuglevel,path,followredirect)
        self.log = logging.getLogger('myengine')
        self.knowledge = dict(generic=dict(found=False,reason=''),wafname=list())

    def normalrequest(self,usecache=True,cacheresponse=True,headers=None):
        return self.request(usecache=usecache,cacheresponse=cacheresponse,headers=headers)

    def normalnonexistentfile(self,usecache=True,cacheresponse=True):
        path = self.path + str(random.randrange(1000,9999)) + '.html'
        return self.request(path=path,usecache=usecache,cacheresponse=cacheresponse)

    def unknownmethod(self,usecache=True,cacheresponse=True):
        return self.request(method='OHYEA',usecache=usecache,cacheresponse=cacheresponse)

    def directorytraversal(self,usecache=True,cacheresponse=True):
        return self.request(path=self.path+self.dirtravstring,usecache=usecache,cacheresponse=cacheresponse)

    def invalidhost(self,usecache=True,cacheresponse=True):
        randomnumber = random.randrange(100000,999999)
        return self.request(headers={'Host':str(randomnumber)})

    def cleanhtmlencoded(self,usecache=True,cacheresponse=True):
        string = self.path + quote(self.cleanhtmlstring) + '.html'
        return self.request(path=string,usecache=usecache,cacheresponse=cacheresponse)

    def cleanhtml(self,usecache=True,cacheresponse=True):
        string = self.path + self.cleanhtmlstring + '.html'
        return self.request(path=string,usecache=usecache,cacheresponse=cacheresponse)

    def xssstandard(self,usecache=True,cacheresponse=True):
        xssstringa = self.path + self.xssstring + '.html'
        return self.request(path=xssstringa,usecache=usecache,cacheresponse=cacheresponse)

    def protectedfolder(self,usecache=True,cacheresponse=True):
        pfstring = self.path + self.AdminFolder
        return self.request(path=pfstring,usecache=usecache,cacheresponse=cacheresponse)

    def xssstandardencoded(self,usecache=True,cacheresponse=True):
        xssstringa = self.path + quote(self.xssstring) + '.html'
        return self.request(path=xssstringa,usecache=usecache,cacheresponse=cacheresponse)

    def cmddotexe(self,usecache=True,cacheresponse=True):
        # thanks j0e
        string = self.path + 'cmd.exe'
        return self.request(path=string,usecache=usecache,cacheresponse=cacheresponse)

    attacks = [cmddotexe,directorytraversal,xssstandard,protectedfolder,xssstandardencoded]

    def genericdetect(self,usecache=True,cacheresponse=True):
        reason = ''
        reasons = ['Blocking is being done at connection/packet level.',
                   'The server header is different when an attack is detected.',
                   'The server returned a different response code when a string trigged the blacklist.',
                   'It closed the connection for a normal request.',
                   'The connection header was scrambled.'
                   ]
        # test if response for a path containing html tags with known evil strings
        # gives a different response from another containing invalid html tags
        r = self.cleanhtml()
        if r is None:
            self.knowledge['generic']['reason'] = reasons[0]
            self.knowledge['generic']['found'] = True
            return True
        cleanresponse,_tmp =r
        r = self.xssstandard()
        if r is None:
            self.knowledge['generic']['reason'] = reasons[0]
            self.knowledge['generic']['found'] = True
            return True
        xssresponse,_tmp = r
        if xssresponse.status != cleanresponse.status:
            self.log.info('Server returned a different response when a script tag was tried')
            reason = reasons[2]
            reason += '\r\n'
            reason += 'Normal response code is "%s",' % cleanresponse.status
            reason += ' while the response code to an attack is "%s"' % xssresponse.status
            self.knowledge['generic']['reason'] = reason
            self.knowledge['generic']['found'] = True
            return True
        r = self.cleanhtmlencoded()
        cleanresponse,_tmp = r
        r = self.xssstandardencoded()
        if r is None:
            self.knowledge['generic']['reason'] = reasons[0]
            self.knowledge['generic']['found'] = True
            return True
        xssresponse,_tmp = r
        if xssresponse.status != cleanresponse.status:
            self.log.info('Server returned a different response when a script tag was tried')
            reason = reasons[2]
            reason += '\r\n'
            reason += 'Normal response code is "%s",' % cleanresponse.status
            reason += ' while the response code to an attack is "%s"' % xssresponse.status
            self.knowledge['generic']['reason'] = reason
            self.knowledge['generic']['found'] = True
            return True
        response, responsebody = self.normalrequest()
        normalserver = response.getheader('Server')
        for attack in self.attacks:
            r = attack(self)
            if r is None:
                self.knowledge['generic']['reason'] = reasons[0]
                self.knowledge['generic']['found'] = True
                return True
            response, responsebody = r
            attackresponse_server = response.getheader('Server')
            if attackresponse_server:
                if attackresponse_server != normalserver:
                    self.log.info('Server header changed, WAF possibly detected')
                    self.log.debug('attack response: %s' % attackresponse_server)
                    self.log.debug('normal response: %s' % normalserver)
                    reason = reasons[1]
                    reason += '\r\nThe server header for a normal response is "%s",' % normalserver
                    reason += ' while the server header a response to an attack is "%s.",' % attackresponse_server
                    self.knowledge['generic']['reason'] = reason
                    self.knowledge['generic']['found'] = True
                    return True
        for attack in self.wafdetectionsprio:
            if self.wafdetections[attack](self) is None:
                self.knowledge['generic']['reason'] = reasons[0]
                self.knowledge['generic']['found'] = True
                return True
        for attack in self.attacks:
            r = attack(self)
            if r is None:
                self.knowledge['generic']['reason'] = reasons[0]
                self.knowledge['generic']['found'] = True
                return True
            response, responsebody = r
            for h,v in response.getheaders():
                if scrambledheader(h):
                    self.knowledge['generic']['reason'] = reasons[4]
                    self.knowledge['generic']['found'] = True
                    return True
        return False

    def matchheader(self,headermatch,attack=False,ignorecase=True):
        import re
        detected = False
        header,match = headermatch
        if attack:
            requests = self.attacks
        else:
            requests = [self.normalrequest]
        for request in requests:
            r = request(self)
            if r is None:
                return
            response,responsebody = r
            headerval = response.getheader(header)
            if headerval:
                # set-cookie can have multiple headers, python gives it to us
                # concatinated with a comma
                if header == 'set-cookie':
                    headervals = headerval.split(', ')
                else:
                    headervals = [headerval]
                for headerval in headervals:
                    if ignorecase:
                        if re.match(match,headerval,re.IGNORECASE):
                            detected = True
                            break
                    else:
                        if re.match(match,headerval):
                            detected = True
                            break
                if detected:
                    break
        return detected

    def isbigip(self):
        return self.matchheader(('X-Cnection','^close$'), attack=True)

    def iswebknight(self):
        detected = False
        for attack in self.attacks:
            r = attack(self)
            if r is None:
                return
            response, responsebody = r
            if response.status == 999:
                detected = True
                break
        return detected

    def ismodsecurity(self):
        detected = False
        for attack in self.attacks:
            r = attack(self)
            if r is None:
                return
            response, responsebody = r
            if response.status == 501:
                detected = True
                break
        return detected

    def isisaserver(self):
        detected = False
        r = self.invalidhost()
        if r is None:
            return
        response,responsebody = r
        if response.reason == self.isaservermatch:
            detected = True
        return detected

    def issecureiis(self):
        # credit goes to W3AF
        detected = False
        headers = dict()
        headers['Transfer-Encoding'] = 'z' * 1025
        r = self.normalrequest(headers=headers)
        if r is None:
            return
        response,responsebody = r
        if response.status == 404:
            detected = True
        return detected

    def matchcookie(self,match):
        """
        a convenience function which calls matchheader
        """
        return self.matchheader(('set-cookie',match))

    def isairlock(self):
        # credit goes to W3AF
        return self.matchcookie('^AL[_-]?(SESS|LB)=')

    def isbarracuda(self):
        # credit goes to W3AF
        return self.matchcookie('^barra_counter_session=')

    def isdenyall(self):
        # credit goes to W3AF
        if self.matchcookie('^sessioncookie='):
            return True
        # credit goes to Sebastien Gioria
        #   Tested against a Rweb 3.8
        # and modified by sandro gauci and someone else
        for attack in self.attacks:
            r = attack(self)
            if r is None:
                return
            response, responsebody = r
            if response.status == 200:
                if response.reason == 'Condition Intercepted':
                    return True
        return False

    def isbeeware(self):
        # disabled cause it was giving way too many false positives
        # credit goes to Sebastien Gioria
        detected = False
        r = self.xssstandard()
        if r is None:
            return
        response, responsebody = r
        if (response.status != 200) or (response.reason == 'Forbidden'):
            r = self.directorytraversal()
            if r is None:
                return
            response, responsebody = r
            if response.status == 403:
                if response.reason == "Forbidden":
                    detected = True
        return detected

    def isf5asm(self):
        # credit goes to W3AF
        return self.matchcookie('^TS[a-zA-Z0-9]{3,6}=')

    def isf5trafficshield(self):
        for hv in [['cookie','^ASINFO='],['server','F5-TrafficShield']]:
            r = self.matchheader(hv)
            if r is None:
                return
            elif r:
                return r
        return False

    def isteros(self):
        # credit goes to W3AF
        return self.matchcookie('^st8id=')

    def isnetcontinuum(self):
        # credit goes to W3AF
        return self.matchcookie('^NCI__SessionId=')

    def isbinarysec(self):
        # credit goes to W3AF
        return self.matchheader(('server','BinarySec'))

    def ishyperguard(self):
        # credit goes to W3AF
        return self.matchcookie('^WODSESSION=')

    def isprofense(self):

        """
        Checks for server headers containing "profense"
        """
        return self.matchheader(('server','profense'))

    def isnetscaler(self):
        """
        First checks if a cookie associated with Netscaler is present,
        if not it will try to find if a "Cneonction" or "nnCoection" is returned
        for any of the attacks sent
        """
        # NSC_ and citrix_ns_id come from David S. Langlands <dsl 'at' surfstar.com>
        if self.matchcookie('^(ns_af=|citrix_ns_id|NSC_)'):
            return True
        if self.matchheader(('Cneonction','close'),attack=True):
            return True
        if self.matchheader(('nnCoection','close'),attack=True):
            return True
        return False

    def isurlscan(self):
        detected = False
        testheaders = dict()
        testheaders['Translate'] = 'z'*10
        testheaders['If'] = 'z'*10
        testheaders['Lock-Token'] = 'z'*10
        testheaders['Transfer-Encoding'] = 'z'*10
        r = self.normalrequest()
        if r is None:
            return
        response,_tmp = r
        r = self.normalrequest(headers=testheaders)
        if r is None:
            return
        response2,_tmp = r
        if response.status != response2.status:
            if response2.status == 404:
                detected = True
        return detected

    def iswebscurity(self):
        detected = False
        r = self.normalrequest()
        if r is None:
            return
        response,responsebody=r
        if response.status == 403:
            return detected
        newpath = self.path + '?nx=@@'
        r = self.request(path=newpath)
        if r is None:
            return
        response,responsebody = r
        if response.status == 403:
            detected = True
        return detected

    def isdotdefender(self):
        # thanks to j0e
        return self.matchheader(['X-dotDefender-denied', '^1$'],attack=True)

    def isimperva(self):
        # thanks to Mathieu Dessus <mathieu.dessus(a)verizonbusiness.com> for this
        # might lead to false positives so please report back to sandro@enablesecurity.com
        for attack in self.attacks:
            r = attack(self)
            if r is None:
                return
            response, responsebody = r
            if response.version == 10:
                return True
        return False

    def ismodsecuritypositive(self):
        import random
        detected = False
        self.normalrequest(usecache=False,cacheresponse=False)
        randomfn = self.path + str(random.randrange(1000,9999)) + '.html'
        r = self.request(path=randomfn)
        if r is None:
            return
        response,responsebody = r
        if response.status != 302:
            return False
        randomfnnull = randomfn+'%00'
        r = self.request(path=randomfnnull)
        if r is None:
            return
        response,responsebody = r
        if response.status == 404:
            detected = True
        return detected

    def isibmdatapower(self):
        # Added by Mathieu Dessus <mathieu.dessus(a)verizonbusiness.com>
        detected = False
        if self.matchheader(('X-Backside-Transport', '^(OK|FAIL)')):
                detected = True
        return detected


    def isibm(self):
        detected = False
        r = self.protectedfolder()
        if r is None:
            detected = True
        return detected


    wafdetections = dict()
    # easy ones
    wafdetections['IBM Web Application Security'] = isibm
    wafdetections['IBM DataPower'] = isibmdatapower
    wafdetections['Profense'] = isprofense
    wafdetections['ModSecurity'] = ismodsecurity
    wafdetections['ISA Server'] = isisaserver
    wafdetections['NetContinuum'] = isnetcontinuum
    wafdetections['HyperGuard'] = ishyperguard
    wafdetections['Barracuda'] = isbarracuda
    wafdetections['Airlock'] = isairlock
    wafdetections['BinarySec'] = isbinarysec
    wafdetections['F5 Trafficshield'] = isf5trafficshield
    wafdetections['F5 ASM'] = isf5asm
    wafdetections['Teros'] = isteros
    wafdetections['DenyALL'] = isdenyall
    wafdetections['BIG-IP'] = isbigip
    wafdetections['Citrix NetScaler'] = isnetscaler
    # lil bit more complex
    wafdetections['webApp.secure'] = iswebscurity
    wafdetections['WebKnight'] = iswebknight
    wafdetections['URLScan'] = isurlscan
    wafdetections['SecureIIS'] = issecureiis
    wafdetections['dotDefender'] = isdotdefender
    #wafdetections['BeeWare'] = isbeeware
    # wafdetections['ModSecurity (positive model)'] = ismodsecuritypositive removed for now
    wafdetections['Imperva'] = isimperva
    wafdetectionsprio = ['Profense','NetContinuum',
                         'Barracuda','HyperGuard','BinarySec','Teros',
                         'F5 Trafficshield','F5 ASM','Airlock','Citrix NetScaler',
                         'ModSecurity', 'IBM Web Application Security', 'IBM DataPower', 'DenyALL',
                         'dotDefender','webApp.secure', # removed for now 'ModSecurity (positive model)',
                         'BIG-IP','URLScan','WebKnight',
                         'SecureIIS','Imperva','ISA Server']

    def identwaf(self,findall=False):
        detected = list()
        for wafvendor in self.wafdetectionsprio:
            self.log.info('Checking for %s' % wafvendor)
            if self.wafdetections[wafvendor](self):
                detected.append(wafvendor)
                if not findall:
                    break
        self.knowledge['wafname'] = detected
        return detected

# Class waf_api : inherits from the base class object. New-style Classes
# Mandatory and optional args can be identified with the __init__ method
class waf_api(object):

    #waf_api Comment : constructor - takes one parameter. This is arguments received from main.py wrapper.
    def __init__(self):
        #Dir_admin Comment :  User variables
        self.cache = dict()

    def vendordetect(self,url,findall=False):
        '''
        Method that detect vendor of fireall
        '''

        if self.cache.has_key(url):
            attacker = self.cache[url]
        else:
            r = oururlparse(url)
            if r is None:
                return ['']
            (hostname,port,path,query,ssl) = r
            attacker = myengine(target=hostname,port=port,path=path,ssl=ssl)
            self.cache[url] = attacker
        return attacker.identwaf(findall=findall)

    def genericdetect(self,url):
        if self.cache.has_key(url):
            attacker = self.cache[url]
        else:
            r = oururlparse(url)
            if r is None:
                return {}
            (hostname,port,path,query,ssl) = r
            attacker = myengine(target=hostname,port=port,path=path,ssl=ssl)
            self.cache[url] = attacker
        attacker.genericdetect()
        return attacker.knowledge['generic']

    def alltests(self,url,findall=False):
        if self.cache.has_key(url):
            attacker = self.cache[url]
        else:
            r = oururlparse(url)
            if r is None:
                return {}
            (hostname,port,path,query,ssl)  = r
            attacker = myengine(target=hostname,port=port,path=path,ssl=ssl)
            self.cache[url] = attacker
        attacker.identwaf(findall=findall)
        if (len(attacker.knowledge['wafname']) == 0) or (findall):
            attacker.genericdetect()
        return attacker.knowledge

# Class WAF : inherits from the base class object. New-style Classes
# Mandatory and optional args can be identified with the __init__ method
class WAF(object):

    #WAF Comment : constructor - takes one parameter. This is arguments received from main.py wrapper.
    def __init__(self, arg):
        #WAF Comment :  User variables
        self.sites = None
        self.verbose = 0
        self.findall = False
        self.followredirect = True
        self.test = False
        self.list = False
        self.xmlrpc = False
        self.xmlrpcport = 8001
        self.log = None

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
WAF command usage:
    -s <site_url>
    -v (verbose)
    -a (find all WAFs, do not stop testing on the first one)
    -r (do not follow redirections given by 3xx responses)
    -t (test for one specific WAF)
    -l (list all WAFs that we are able to detect)
    -p (switch on the XML-RPC interface instead of CUI)
    -P <port> (specify an alternative port to listen on, default 8001)
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
            #    opts, args = getopt.getopt(['-h','-s','10','url'],"s:vartlpP:h")
            #will return
            #    opts = [('-h',''),('-s','10')]
            #    args = ['url']
            cmd_opts = "s:vartlpP:h"
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
                self.sites = opt[1:]
            elif opt[0] == "-v":
                self.verbose+=1
            elif opt[0] == "-a":
                self.findall = True
            elif opt[0] == "-r":
                self.followredirect = False
            elif opt[0] == "-t":
                self.test = True
            elif opt[0] == "-l":
                self.list = True
            elif opt[0] == "-p":
                self.xmlrpc = True
            elif opt[0] == "-P":
                try:
                    self.xmlrpcport = int(opt[1])
                except:
                    print "Please enter the number of port"
                    return -1
            else:
                return -1

        return 0

    def calclogginglevel(self,verbosity):
        '''
        Method that set level of verbosity.
        :param verbosity: integer
        :return level: integer

        '''

        default = 40 # errors are printed out
        # If verbosity level is not set, use default value
        level = default - (verbosity*10)
        if level < 0:
            level = 0
        return level

    def xmlrpc_interface(self, bindaddr=('localhost',8001)):
        '''
        Method that create XML-RPC interface.
        :param binaddr: tuple

        '''

        from SimpleXMLRPCServer import SimpleXMLRPCServer
        from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

        # Class RequestHandler : inherits from the base class SimpleXMLRPCRequestHandler
        # For more details: http://docs.python.org/2/library/simplexmlrpcserver.html
        # The SimpleXMLRPCServer module provides a basic server framework for XML-RPC servers written in Python.
        # Create a new request handler instance. This request handler supports POST requests and modifies logging
        # so that the logRequests parameter to the SimpleXMLRPCServer constructor parameter is honored.
        # Restrict to a particular path.
        class RequestHandler(SimpleXMLRPCRequestHandler):
            rpc_paths = ('/RPC2',)

        # Create server
        server = SimpleXMLRPCServer(bindaddr,
                                requestHandler=RequestHandler)
        # Registers the XML-RPC introspection functions system.listMethods, system.methodHelp and system.methodSignature.
        server.register_introspection_functions()
        # Register an instance; all the methods of the instance are
        # published as XML-RPC methods
        server.register_instance(waf_api())
        try:
            # Run the server's main loop
            server.serve_forever()
        except KeyboardInterrupt:
            print "bye!"
            return

    def oururlparse(self, target):
        '''
        Method that parse URL.
        :param target: string
        :return tuple:

        '''

        # We don't use SSL by default
        ssl = False
        o = urlparse(target)
        # Get protocol
        if o[0] not in ['http','https','']:
            self.log.error('scheme %s not supported' % o[0])
            return
        # If https has found set ssl flag to True
        if o[0] == 'https':
            ssl = True
        if len(o[2]) > 0:
            path = o[2]
        else:
            path = '/'
        tmp = o[1].split(':')
        if len(tmp) > 1:
            port = tmp[1]
        else:
            port = None
        # Get hostname
        hostname = tmp[0]
        # Get request
        query = o[4]
        # Return tuple with parameters
        return (hostname,port,path,query,ssl)

    def perform(self):
        '''
        Main method of the class that perform all actions.

        '''

        # Initialize value for level of verbosity
        logging.basicConfig(level=self.calclogginglevel(self.verbose))

        # Return a logger with the specified name or, if no name is specified, return a logger which is the root
        # logger of the hierarchy. If specified, the name is typically a dot-separated hierarchical name like "a",
        # "a.b" or "a.b.c.d". Choice of these names is entirely up to the developer who is using logging.
        self.log = logging.getLogger("WAF")
        # Check if we you list
        if self.list:
            print "Can test for these WAFs:\r\n"
            # Create an instance of class myengine
            attacker = myengine(None)
            # We call the wafdetectionsprio method of the attacker object.
            # In main, we instanciate attacker as a myengine object.
            # So we call here the wafdetectionsprio method of the myengine class
            print '\r\n'.join(attacker.wafdetectionsprio)
            return
        # Else, create XML-RPC INterface with default parameters.
        elif self.xmlrpc:
            print "Starting XML-RPC interface"
            self.xmlrpc_interface(bindaddr=('localhost',self.xmlrpcport))
            return

        for target in self.sites:
            if not (target.startswith('http://') or target.startswith('https://')):
                self.log.info('The url %s should start with http:// or https:// .. fixing (might make this unusable)' % target)
                target = 'http://' + target
            print "Checking %s" % target
            # We call the oururlparse method.
            # The method returns parsed url (tuple)
            pret = self.oururlparse(target)
            # If pret is empty we create logs a message with level CRITICAL on this logger.
            if pret is None:
                self.log.critical('The url %s is not well formed' % target)
                return
            # The results is a tuple.
            (hostname,port,path,query,ssl) = pret
            # Logs a message with level INFO on this logger.
            self.log.info('starting WAF on %s' % target)
            #We call an instance of the class myengine defined above
            attacker = myengine(hostname,port=port,ssl=ssl,
                               debuglevel=self.verbose,path=path,
                               followredirect=self.followredirect)
            # We check that we have normal URL request.
            if attacker.normalrequest() is None:
                self.log.error('Site %s appears to be down' % target)
                return
            # Check if self.test is not None
            if self.test:
                if attacker.wafdetections.has_key(self.test):
                    # Get value from dict wafdetections that has key self.test and
                    # assigns the value of the variable waf
                    # This allow us to get information about firewall
                    waf = attacker.wafdetections[self.test](attacker)
                    if waf:
                        print "The site %s is behind a %s" % (target, self.test)
                    else:
                        print "WAF %s was not detected on %s" % (self.test,target)
                else:
                    print "WAF %s was not found in our list\r\nUse the --list option to see what is available" % self.test
                return
            # Call method identwaf
            waf = attacker.identwaf(self.findall)
            # Logs a message with level INFO on this logger.
            self.log.info('Ident WAF: %s' % waf)
            if len(waf) > 0:
                print 'The site %s is behind a %s' % (target, ' and/or '.join(waf))
            if (self.findall) or len(waf) == 0:
                print 'Generic Detection results:'
                if attacker.genericdetect():
                    # Logs a message with level INFO on this logger.
                    self.log.info('Generic Detection: %s' % attacker.knowledge['generic']['reason'])
                    print 'The site %s seems to be behind a WAF ' % target
                    print 'Reason: %s' % attacker.knowledge['generic']['reason']
                else:
                    print 'No WAF detected by the generic detection'
            print 'Number of requests: %s' % attacker.requestnumber

