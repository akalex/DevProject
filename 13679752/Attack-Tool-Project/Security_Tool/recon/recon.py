import httplib
from random import randint
import re
import getopt
import socket
import urllib2
import httplib2
from time import sleep
from lib import socks
from lib.cymruwhois import Client as WhoisClient
from lib import google

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

# XFN -  is an HTML microformat developed by Global Multimedia Protocols Group that provides a simple way to represent
# human relationships using links. XFN enables web authors to indicate relationships to the people in their blogrolls
# by adding one or more keywords as the rel attribute to their links.
xfn = [
    "friend", "acquaintance", "contact", "met", "co-worker", "colleague",
    "co-resident", "neighbor", "child", "parent", "sibling", "spouse",
    "kin", "muse", "crush", "date", "sweetheart", "me"
]


# noinspection PyUnresolvedReferences,PyTypeChecker
# Class Recon : inherits from the base class object. New-style Classes
# Mandatory and optional args can be identified with the __init__ method
class Recon(object):

    #Recon Comment : constructor - takes one parameter. This is arguments received from main.py wrapper.
    def __init__(self, arg):
        #Dir_admin Comment :  User variables
        self.base_url = ""
        self.start_ip = None
        self.stop_ip = None
        self.web_proxy = None
        self.web_port = 80
        self.web_user = None
        self.web_pass = None
        self.proxy_user = None
        self.proxy_pass = None
        self.dict_files = None
        self.domains = None
        self.delay = 0
        self.email_lookup = False
        self.name_lookup = False
        self.salt = False
        self.google_dict_search = False
        self.google_query_dict = False
        self.urlencode = False
        self.shut_up = False
        self.web_lookup = False
        self.blog_site = None
        self.whois = False
        self.find_relation = False
        self.zone_trans = False

        # Create instance of additional Class WhoisClient()
        self.whois_client = WhoisClient()
        # The class that represents a client HTTP interface.
        self.web_client = httplib2.Http()
        # This module implements a file-like class, StringIO, that reads and writes a string buffer
        # Create a buffer.
        self.buffer = StringIO()

        # Parse arguments.
        if self.parse_arg(arg):
            self.usage()
            return

        # Calls method, that will perform some actions.
        self.perform()

    def usage(self):
        '''
        Method for shows information about how to use this tool.
        '''

        print """
Recon command usage:
    -b <base_url>
    -c <web_user:password>
    -C <proxy_user:password>
    -d <domain>
    -D <delay_in_sec>
    -e (email_search)
    -f <dict_file>
    -g (google_dict_search)
	-G (Google_only)
    -h (help)
    -i <start_ip>-<stop_ip>
    -n (name_lookup)
    -p <webserver_port>
    -P <proxy_ip:port>
    -q (quiet)
    -Q (input in dict are google hack queries)
    -s (salt)
    -u (urlencode)
    -w (web lookup)
    -W (whois)
    -r <blog_site> (Find Human Relationships)
    -z <domain> (Zone Transfer)
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
            #    opts, args = getopt.getopt(['-h','-D','10','ip'],"b:c:C:d:D:ef:gi:np:P:qQsuvwWr:z")
            #will return
            #    opts = [('-h',''),('-D','10')]
            #    args = ['ip']
            cmd_opts = "b:c:C:d:D:ef:gi:np:P:qQsuvwWr:z"
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
            if opt[0] == "-b":
                self.base_url = opt[1]
            elif opt[0] == "-c":
                self.web_user, self.web_pass = opt[1].split(':')
            elif opt[0] == "-d":
                self.domains = opt[1]
            elif opt[0] == "-D":
                self.delay = int(opt[1])
            elif opt[0] == "-e":
                self.email_lookup = True
            elif opt[0] == "-f":
                self.dict_files = opt[1]
            elif opt[0] == "-g":
                self.google_dict_search = True
            elif opt[0] == "-i":
                self.start_ip, self.stop_ip = opt[1].split('-')
            elif opt[0] == "-n":
                self.name_lookup = True
            elif opt[0] == "-p":
                self.web_port = opt[1]
            elif opt[0] == "-P":
                self.web_proxy = opt[1]
            elif opt[0] == "-q":
                self.shut_up = True
            elif opt[0] == "-Q":
                self.google_query_dict = True
            elif opt[0] == "-s":
                self.salt = True
            elif opt[0] == "-u":
                self.urlencode = True
            elif opt[0] == "-w":
                self.web_lookup = True
            elif opt[0] == "-W":
                self.whois = True
            elif opt[0] == "-r":
                self.find_relation = True
                self.blog_site = opt[1]
            elif opt[0] == "z":
                self.zone_trans = True
                self.domains = opt[1]
            else:
                return -1
        return 0

    def get_ips(self, start_ip, stop_ip):
        """
        Method that generate list of IPs for the specified range.
        :param start_ip: string
        :param stop_ip: string
        :return a list all ip addresses from start_ip to stop_ip
        """

        ips = []
        # Convert start_ip and stop_ip into variables with type long
        start_dec = long(''.join(["%02X" % long(i) for i in start_ip.split('.')]), 16)
        stop_dec = long(''.join(["%02X" % long(i) for i in stop_ip.split('.')]), 16)

        while(start_dec < stop_dec + 1):
            bytes = []
            bytes.append(str(int(start_dec / 16777216)))
            rem = start_dec % 16777216
            bytes.append(str(int(rem / 65536)))
            rem = rem % 65536
            bytes.append(str(int(rem / 256)))
            rem = rem % 256
            bytes.append(str(rem))
            ips.append(".".join(bytes))
            start_dec += 1
        return ips

    def dns_reverse_lookup(self):
        """
        Method that determine of domain name that is associated with a given IP address using the
        Domain Name System (DNS) of the Internet.
        """

        # Get List of IPs
        ips = self.get_ips(self.start_ip, self.stop_ip)

        while len(ips) > 0:
            # Return a random integer N such that a <= N <= b.
            i = randint(0, len(ips) - 1)
            # Get i-element
            lookup_ip = str(ips[i])
            try:
                # Return a triple (hostname, aliaslist, ipaddrlist) where hostname is the primary host name
                # responding to the given ip_address, aliaslist is a (possibly empty) list of alternative host names
                # for the same address, and ipaddrlist is a list of IPv4/v6 addresses for the same interface on
                # the same host (most likely containing only a single address)
                print lookup_ip + ": " + str(socket.gethostbyaddr(lookup_ip)[0])
            # This exception is raised for address-related errors
            except socket.herror, e:
                print lookup_ip + ": " + str(e)
            # This exception is raised for socket-related errors.
            except socket.error, e:
                print lookup_ip + ": " + str(e)

            # If self.whois is True, make a WHOIS request for lookup_ip
            if self.whois:
                info = self.whois_client.lookup(lookup_ip)
                print info.owner

            # Suspend execution for the given number of seconds.
            if self.delay > 0:
                sleep(self.delay)

            # Remove an item from a list by given index
            del ips[i]

    def do_url_encoding(self, path):
        '''
        Method that encodes url
        :param path: string
        :return string
        '''

        hex = '%'.join(["%02x" % ord(x) for x in path])
        return '%' + hex

    def do_web_lookup(self, host, path):
        """
        Method that do the actual web lookup, maybe mixin salt and
        search the path on host with google, print the result
        :param host: string
        :praram path: string
        """

        url = ""
        got_google_result = False
        chars = ["/"]

        # If self.salt is True, reinitialize variable chars
        if self.salt == True:
            chars = ["/", "//", "/mooh/../", "/./"]

        # If self.google_dict_search is True, make a Google Search
        if self.google_dict_search:
            if not self.shut_up:
                print "Google dict search " + path + " on " + host
            # Create Google Search String
            google_search_string = "+site:" + host + " inurl:" + self.base_url + "/" + path

            if self.google_query_dict:
                google_search_string = "+site:" + host + " " + path
            # Create instance of class Search and pass the params
            # google_search_string - Query string. Must NOT be url-encoded.
            # domain - Top level domain
            # stop - Last result to retrieve.
            results = google.search(google_search_string, tld = 'com', stop = 3)

            try:
                for link in results:
                    # if pattern match string "^https?://" + host, print result
                    if re.match("^https?://" + host, link):
                        print "FOUND with Google:" + link
                        got_google_result = True
                        break
            except KeyError:
                pass
            # Though being an exception (a subclass of URLError), an HTTPError can also function as a non-exceptional
            # file-like return value
            except urllib2.HTTPError, e:
                print "Google search failed: " + str(e)

            # If variables got_google_result and self.shut_up are not set, print "No result"
            if not got_google_result:
                if not self.shut_up:
                    print "No result"

        if self.web_lookup == True and \
                (self.google_dict_search == False or \
                     (self.google_dict_search == True and got_google_result == False)):
            for char in chars:
                # Generate url regarding to port and chars
                if self.web_port == "80":
                    url = "http://" + host + char + self.base_url + path
                elif self.web_port == "443":
                    url = "https://" + host + char + self.base_url + path
                else:
                    url = "http://" + host + ":" + str(self.web_port) + char + self.base_url + path

                try:
                    if not self.shut_up:
                        print "GET " + url
                    # Performs a single HTTP request.
                    response, content = self.web_client.request(url)

                    # Check HTTP Error code that was returned from HTTP request
                    if response.status == 200:
                        print "FOUND " + url + " got " + response['content-location']

                    if delay > 0:
                        # Suspend execution for the given number of seconds.
                        sleep(delay)
                # Unable to resolve the host name given
                except httplib2.ServerNotFoundError:
                    print "Got error for " + url + ": Server not found"
                except:
                    print "Got error for " + url

    def scan_webserver(self):
        """
        Method that scan a web server for hidden paths based on a dictionary
        """
        for file in self.dict_files.split(","):
            try:
                # Open file for reading
                fh = open(file, "r")

                for word in fh.readlines():
                    # Return a copy of the string with the leading and trailing characters removed
                    path = word.strip()

                    if self.urlencode:
                        # Call method self.do_url_encoding and pass the param
                        path = self.do_url_encoding(path)

                    if self.domains != None:
                        for domain in self.domains.split(","):
                            # Call method do_web_lookup and pass the param
                            self.do_web_lookup(domain, path)
                    else:
                        ips = self.get_ips(self.start_ip, self.stop_ip)

                        while len(ips) > 0:
                            i = randint(0, len(ips) - 1)
                            lookup_ip = str(ips[i])
                            # Remove an item from a list by given index
                            del ips[i]
                            # Call method do_web_lookup and pass the param
                            self.do_web_lookup(lookup_ip, path)
                # Close file
                fh.close()
            except IOError:
                print "Cannot read dictionary " + file

    def do_dns_lookup(self, lookup_name):
        """
        Method that do the actual dns lookup or print error.
        :param lookup_name: string
        """

        try:
            # Translate a host name to IPv4 address format. The IPv4 address is returned as a string,
            # such as '100.50.200.5'. If the host name is an IPv4 address itself it is returned unchanged
            print lookup_name + ": " + socket.gethostbyname(lookup_name)
        # This exception is raised for address-related errors, for getaddrinfo() and getnameinfo().
        except socket.gaierror, e:
            print lookup_name + ": " + str(e)

    def dns_dict_lookup(self):
        """
        Mathod that make a dns dictionay lookups
        if salt is true construct names like www2 www-2 www02
        """

        for file in self.dict_files.split(","):
            try:
                # Open file for reading
                fh = open(file, "r")
                salted_dns = []
                salt_chars = []
                if self.salt == True:
                    salt_chars = ["", "0", "-", "-0", "_", "_0"]

                for word in fh.readlines():
                    for domain in self.domains.split(","):
                        # Call method do_dns_lookup and pass the param
                        self.do_dns_lookup(word.strip() + "." + domain)

                        for chars in salt_chars:
                            for i in range(1, 9):
                                salted_dns.append(word.strip() + chars + str(i) + "." + domain)

                        while len(salted_dns) > 0:
                            i = randint(0, len(salted_dns) - 1)
                            # Call method do_dns_lookup and pass the param
                            self.do_dns_lookup(salted_dns[i])
                            # Remove an item from a list by given index
                            del salted_dns[i]

                            if self.delay > 0:
                                # Suspend execution for the given number of seconds.
                                sleep(self.delay)
                # Close
                fh.close()
            except IOError:
                print "Cannot read dictionary " + file

    def do_google_mail_search(self, site):
        """
        Method that search google for site and parse a list of emails.
        :param site: string
        """

        emails = set()
        if not self.shut_up:
            print "Google search for emails on " + site
        # Create instance of class Search and pass the params
        # google_search_string - Query string. Must NOT be url-encoded.
        # domain - Top level domain
        # num - Number of results per page
        # stop - Last result to retrieve.
        results = google.search("+site:" + site, tld = 'com', num = 100, stop = 23)

        try:
            for link in results:
                if link.find("youtube") > 0 or re.search("[html?|phtml|php|asp|jsp|txt|/][\\?$]", link) == None:
                    continue

                if not self.shut_up:
                    print "GET " + link
                # Performs a single HTTP request.
                response, content = self.web_client.request(link)

                # Check HTTP Error code that was returned from HTTP request
                if response.status == 200:
                    # Return all non-overlapping matches of pattern in string, as a list of strings.
                    # The string is scanned left-to-right, and matches are returned in the order found
                    matches = re.findall(".*?([a-zA-Z0-9\\._\\-\\+]+@.+?\\.\w{2,4})", content)

                    # Add matches into set
                    if matches != None:
                        for match in matches:
                            emails.add(match)
        except KeyError:
            pass
        # Though being an exception (a subclass of URLError), an HTTPError can also function as a non-exceptional
        # file-like return value
        except urllib2.HTTPError, e:
            print "Google search failed: " + str(e)

        if len(emails) == 0:
            if not self.shut_up:
                print "No emails found for " + site
        else:
            print "Emails found for " + site + ":"
            for email in emails:
                print email

    def perform(self):
        '''
        Main method of the class that perform all actions.

        '''

        if self.web_proxy != None:
            self.proxy_ip, self.proxy_port = self.web_proxy.split(":")

            # httplib2 can use a SOCKS proxy if the third-party socks module is installed.
            # proxytype - The type of the proxy server. This can be one of three possible
            # choices: PROXY_TYPE_SOCKS4, PROXY_TYPE_SOCKS5 and PROXY_TYPE_HTTP for Socks4,
            # Socks5 and HTTP servers respectively. We use socks.PROXY_TYPE_HTTP
            # self.proxy_ip - The IP address or DNS name of the proxy server
            # self.proxy_port - The port of the proxy server. Defaults to 1080 for socks and 8080 for http.
            # self.proxy_user - For Socks5 servers, this allows simple username / password authentication
            # with the server. For Socks4 servers, this parameter will be sent as the userid.
            # This parameter is ignored if an HTTP server is being used. If it is not provided,
            # authentication will not be used (servers may accept unauthentication requests).
            # self.proxy_pass - This parameter is valid only for Socks5 servers and specifies the
            # respective password for the username provided.
            if self.proxy_ip != "" and self.proxy_port != "":
                proxy_info = httplib2.ProxyInfo(
                    proxy_type = socks.PROXY_TYPE_HTTP,
                    proxy_host = self.proxy_ip,
                    proxy_port = int(self.proxy_port),
                    proxy_rdns = True,
                    proxy_user = self.proxy_user,
                    proxy_pass = self.proxy_pass
                )
                # The class that represents a client HTTP interface
                self.web_client = httplib2.Http(proxy_info = proxy_info)
            # Print error message if settings are incorrect
            else:
                print "Proxy settings should be proxy_ip:port"
                return

        if self.web_user != None and self.web_pass != None:
            # Adds a name and password that will be used when a request requires authentication.
            # Supplying the optional domain name will restrict these credentials to only be sent to the specified domain.
            #  If domain is not specified then the given credentials will be used to try to satisfy every HTTP 401 challenge.
            self.web_client.add_credentials(self.web_user, self.web_pass)

        if(self.start_ip != None and self.stop_ip != None):
            if self.name_lookup:
                # Call method self.dns_reverse_lookup()
                self.dns_reverse_lookup()
            elif self.web_lookup == True and self.dict_files != None:
                # Call method self.scan_webserver()
                self.scan_webserver()
            else:
                print "You need to either specify -n for dns or -w for web server mapping"
        elif(self.domains != None and self.dict_files != None):
            if self.name_lookup:
                # Call method self.dns_dict_lookup()
                self.dns_dict_lookup()
            elif self.web_lookup:
                # Call method self.scan_webserver()
                self.scan_webserver()
            elif self.google_dict_search:
                # Call method self.scan_webserver()
                self.scan_webserver()
            else:
                print "You need to either specify -n for dns or -w for web server mapping"
        elif(self.domains != None and self.email_lookup):
            for domain in self.domains.split(","):
                # Call method self.do_google_mail_search and pass params
                self.do_google_mail_search(self.domains)
        else:
            # Print how to use
            self.usage()

    def findHumanRelationships(self):
        """
        Method that parse saved HTML. Uses two modules HTMLParser and BeautifulSoup

        :return:
        """
        # import module HTMLParser
        # This module defines a class HTMLParser which serves as the basis for parsing text files formatted in HTML and XHTML.
        import HTMLParser
        try:
            # Try to import module BeautifulSoup.
            # More about this module http://www.crummy.com/software/BeautifulSoup/bs4/doc/
            from BeautifulSoup import BeautifulSoup
        except ImportError:
            print "Please install \'BeautifulSoup\' from http://www.crummy.com/software/BeautifulSoup/."
            return

        results = {}
        try:
            # Open the URL url, which can be either a string or a Request object.
            response = urllib2.urlopen(self.blog_site)
        except:
            print "Connection problem. Try again."
            return

        try:
            # To parse a document, pass it into the BeautifulSoup constructor
            # First, the document is converted to Unicode, and HTML entities are converted to Unicode characters
            # Beautiful Soup then parses the document using the best available parser.
            # It will use an HTML parser unless you specifically tell it to use an XML parser.
            rawData = BeautifulSoup(response)
        # HTMLParser is able to handle broken markup, but in some cases it might raise this exception when it
        # encounters an error while parsing.
        except HTMLParser.HTMLParseError:
            print "Error while reading data. Try again."
            return

        data = rawData.findAll("a")
        for item in data:
            for value in xfn:
                if item.has_key("rel") and re.search(value, item["rel"]) is not None:
                    results[item.string] = item["href"], item["rel"]

        for key, values in results.items():
            self.buffer.write("NAME :  " + key + "\n")
            self.buffer.write("URL :  " + values[0] + "\n")
            self.buffer.write("RELATIONSHIP :  " + re.sub(" ", ", ", values[1]) + "\n\n")

        if not results:
            print "Nothing found."
            return
        else:
            self.showOutput()

    def zoneTransfer(self):
        """
        Method that transfer a zone from a server and print it with the names sorted in DNSSEC order

        :return:
        """
        # Try to import necessary modules
        try:
            import dns.resolver
            import dns.query
            import dns.zone
        except ImportError:
            print "Please install \'dnspython\' from http://www.dnspython.org/."
            return

        results = []
        NS = []
        try:
            # Get the NS target and preference of a name:
            servers = dns.resolver.query(self.domain_url, "NS")
        except dns.resolver.NXDOMAIN:
            print "Non-Existent Domain response."
            return

        for server in servers:
            NS.append(str(server))

        for target in NS:
            try:
                # Transfer a zone from a server and print it with the names sorted in DNSSEC order
                zoneTransfer = dns.zone.from_xfr(dns.query.xfr(target.rstrip("."), self.domain_url))
                names = zoneTransfer.nodes.keys()
                names.sort()
                for name in names:
                    results.append(zoneTransfer[name].to_text(name))
                    self.buffer.write(re.sub(" ", "   ", zoneTransfer[name].to_text(name)) + "\n")
            except:
                pass

        if not results:
            print "Zone transfer is not possible."
            return
        else:
            self.showOutput()