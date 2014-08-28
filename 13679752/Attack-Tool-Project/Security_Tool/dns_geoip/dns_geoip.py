import getopt
from pygeoip import GeoIP
import dns.resolver

import simplekml
import os

# Class Dns : inherits from the base class object. New-style Classes
# Mandatory and optional args can be identified with the __init__ method
class Dns(object):

    #Dns Comment : constructor - takes one parameter. This is arguments received from main.py wrapper.
    def __init__(self, arg):
        #Dns Comment :  User variables
        self.domain = None
        self.dict_file = None
        self.dat_file = None
        cur_path = os.path.realpath(os.path.dirname(__file__))
        self.output_file = os.path.join(cur_path, 'output.xml')

        # Parse arguments.
        if self.parse_arg(arg):
            self.usage()
            return

        # With simplekml everything starts with creating an instance of the simplekml.Kml class
        self.kml = simplekml.Kml()

        # Calls method, that will perform some actions.
        self.perform()

    def usage(self):
        '''
        Method for shows information about how to use this tool.
        '''

        print """
Dns command usage:
    -d <domain>
    -w <dns_dict_file>
    -x <geoip_dat_file>
    -o <output_file>
    -h (help)
"""

    def parse_arg(self, arg):
        '''

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
            #    opts, args = getopt.getopt(['-h','-o','log.txt'],"d:w:x:o:h")
            #will return
            #    opts = [('-h',''),('-o','log,txt')]
            #    args = ['log.txt']
            cmd_opts = "d:w:x:o:h"
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
            if opt[0] == "-d":
                self.domain = opt[1]
            elif opt[0] == "-w":
                self.dict_file = opt[1]
            elif opt[0] == "-x":
                self.dat_file = opt[1]
            elif opt[0] == "-o":
                self.output_file = opt[1]
            else:
                return -1

        return 0

    def to_kml(self, coords):
        '''
        Method that generating, parsing, and modifying KML.
        Keyhole Markup Language (KML) is an XML notation for expressing geographic annotation and visualization
        within Internet-based, two-dimensional maps and three-dimensional Earth browsers.

        :param coords: List. Contains coordinates
        '''

        # Iterate through list
        for coord in coords:
            # The simplekml newpoint method requires that we send it a NAME and a COORDS
            self.kml.newpoint(name=coord[0], coords=[coord[1]])
        # File into which to write our results
        self.kml.save(self.output_file)

    def perform(self):
        '''
        Main method of the class that perform all actions.

        '''

        # Define list of coordinates
        coords = []
        # Open file for reading
        with open(self.dict_file, "r") as lines:
            try:
                for line in lines.readlines():
                    fulldomain = line.rstrip() + "." + self.domain
                    try:
                        # Get the A target and preference of a name
                        answers = dns.resolver.query(fulldomain, 'A')
                        if type(answers) == dns.resolver.Answer:
                            # Iterate through answers and getting data.
                            for rdata in answers:
                                ip = rdata.address
                                # Create instance of GeoIP class
                                gi = GeoIP(self.dat_file)
                                # Call method record_by_addr
                                go = gi.record_by_addr(ip)
                                # Get latitude and longitude from DNS answer
                                coord = (go['latitude'], go['longitude'])
                                coords.append([fulldomain, coord])
                    except:
                        pass
            # The query name does not exist.
            except (dns.exception.DNSException):
                pass

        # Call method for generate KML file
        self.to_kml(coords)
