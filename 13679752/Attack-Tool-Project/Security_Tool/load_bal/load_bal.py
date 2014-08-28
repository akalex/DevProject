import sys
import getopt
# Import module Halbert.
# Halberd discovers HTTP load balancers. It is useful for web application security auditing and for load balancer
# configuration testing.
# For more details http://pydoc.net/Python/halberd/0.2.4/
import Halberd.shell
import Halberd.logger
import Halberd.ScanTask

# Class Loadbal : inherits from the base class object. New-style Classes
# Mandatory and optional args can be identified with the __init__ method
class Loadbal(object):

    #Loadbal Comment : constructor - takes one parameter. This is arguments received from main.py wrapper.
    def __init__(self, arg):
        #Dir_admin Comment :  User variables
        self.url = None
        self.verbose = False
        self.debug = False
        # Time to spend probing the target expressed in seconds.
        self.scantime = Halberd.ScanTask.default_scantime
        # Number of parallel threads to launch for the scan.
        self.parallelism = Halberd.ScanTask.default_parallelism
        self.urlfile = None
        self.out = None
        self.addr = None
        self.cluefile = None
        self.save = None
        # Name of the default configuration file for halberd
        self.confname = Halberd.ScanTask.default_conf_file

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
    -v (verbose)
    -q (quiet)
    -d (debug)
    -t <time> (time in seconds to spend scanning the target)
    -p <thread_cnt> (specify the number of parallel threads to use)
    -u <url_dict_file> (read target URLs from file)
    -s <url> (specify the target url)
    -o <output_file>
    -a <address> (specify address to scan)
    -r <name> (load clues from the specified file)
    -w <name> (save clues to the specified directory)
    -c <conf_file> (use alternative configuration file)
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
            #    opts, args = getopt.getopt(['-h','-s','10','url'],"s:vqdt:p:u:o:a:r:w:c:h")
            #will return
            #    opts = [('-h',''),('-s','10')]
            #    args = ['url']
            cmd_opts = "s:vqdt:p:u:o:a:r:w:c:h"
            opts, args = getopt.getopt(arg, cmd_opts)
        # catch exception if were caught any errors.
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
                self.url = opt[1]
            elif opt[0] == "-v" or opt[0] == "-q":
                self.verbose = True
            elif opt[0] == "-d":
                self.debug = True
            elif opt[0] == "-t":
                try:
                    self.scantime = int(opt[1])
                except:
                    print "Specify the correct number of time in seconds"
                    return -1
            elif opt[0] == "-p":
                try:
                    self.parallelism = opt[1]
                except:
                    print "Specify the correct number of thread count"
                    return -1
            elif opt[0] == "-u":
                self.urlfile = opt[1]
            elif opt[0] == "-o":
                self.out = opt[1]
            elif opt[0] == "-a":
                self.addr = opt[1]
            elif opt[0] == "-r":
                self.cluefile = opt[1]
            elif opt[0] == "-w":
                self.save = opt[1]
            elif opt[0] == "-c":
                self.confname = opt[1]
            else:
                return -1

        return 0

    def make_url(self):
        """Ensures the URL is a valid one.

        Characters aren't escaped, so strings like 'htt%xx://' won't be parsed.
        :return newurl: string
        """

        if self.url.startswith('http://') or self.url.startswith('https://'):
            newurl = self.url
        else:
            newurl = 'http://' + self.url

        return newurl

    def scannerFactory(self):
        '''
        Method that generate default startup parameters.
        :return scanner(): object

        '''
        # HTTP load balancer detector
        # Scanning tasks
        # Create instance of class ScanTask
        scantask = Halberd.ScanTask.ScanTask()

        # Set our values to scantask variables
        # Time to spend probing the target expressed in seconds.
        scantask.scantime = self.scantime
        # Number of parallel threads to launch for the scan.
        scantask.parallelism = self.parallelism
        # Display status information during the scan
        scantask.verbose = self.verbose
        # Display debug information.
        scantask.debug = self.debug
        # Name of the default configuration file for halberd
        scantask.conf_file = self.confname
        # Name of the default clue file for halberd
        scantask.cluefile = self.cluefile
        # File or directory name where the results will be written
        scantask.save = self.save
        # File where to write reports. If it's not set, stdout will be used
        scantask.out = self.out

        # Set logging level.
        if not scantask.verbose:
            Halberd.logger.setError()
        if scantask.debug:
            Halberd.logger.setDebug()

        # Call method that tries to read the specified configuration file. If we try to read it at the default path and it's
        # not there we create a bare-bones file and use that one.
        scantask.readConf()

        if self.cluefile:
            # Read and analyze clues.
            scanner = Halberd.shell.ClueReaderStrategy
        elif self.urlfile:
            # MultiScan
            scantask.urlfile = self.urlfile
            scanner = Halberd.shell.MultiScanStrategy
        elif self.url:
            # UniScan
            scantask.url = self.make_url()
            scantask.addr = self.addr
            scanner = Halberd.shell.UniScanStrategy
        else:
            return None

        # Return object
        return scanner(scantask)

    def perform(self):
        '''
        Main method of the class that perform all actions.

        '''
        # Create exception.
        try:
            # Call method self.scannerFactory()
            scanner = self.scannerFactory()
            # If scanner is empty print error message
            if scanner is None:
                print 'incorrect number of arguments'
            # Start to execute
            scanner.execute()
        except Halberd.shell.ScanError, msg:
            sys.stderr.write('\n*** %s ***\n' % msg)
        except KeyboardInterrupt:
            sys.stderr.write('\r*** interrupted by the user ***\n')