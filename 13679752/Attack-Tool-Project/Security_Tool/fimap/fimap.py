#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Import additional classes and libraries
from plugininterface import plugininterface
from plugininterface import pluginXMLInfo
import autoawesome
import baseClass, baseTools
from codeinjector import codeinjector
from crawler import crawler
import getopt
from googleScan import googleScan
from massScan import massScan
from singleScan import singleScan
import language
import sys, os
import tarfile, tempfile
import shutil


# Class FIMAP : inherits from the base class object. New-style Classes
# Mandatory and optional args can be identified with the __init__ method
class FIMAP(object):
    # Definitions of member class variables
    # These variables, will be called as self.xxx in the class methods
    # It's a coding error to declare these variables here
    # Normally, we declare an __init__ function (which is the class
    # constructor) and declare the variable as self.num= 10 etc....
    #
    # A better way to write this code would be :
    # def __init__(self):
    #     self.mainconfig = {}
    #     self.pluginlist = "http://fimap.googlecode.com/svn/wiki/PluginList.wiki"
    #  ... etc ...

    mainconfig = {}

    pluginlist = "http://fimap.googlecode.com/svn/wiki/PluginList.wiki"

    def show_help(self, AndQuit=False):
        '''
        Method for shows information about how to use this tool.
        :param AndQuit: Bool, by default this flag set to False.
        '''

        print "Usage: main.py WAAF [options]"
        print "## Operating Modes:"
        print "   -s , --single                 Mode to scan a single URL for FI errors."
        print "                                 Needs URL (-u). This mode is the default."
        print "   -m , --mass                   Mode for mass scanning. Will check every URL"
        print "                                 from a given list (-l) for FI errors."
        print "   -g , --google                 Mode to use Google to aquire URLs."
        print "                                 Needs a query (-q) as google search query."
        print "   -H , --harvest                Mode to harvest a URL recursivly for new URLs."
        print "                                 Needs a root url (-u) to start crawling there."
        print "                                 Also needs (-w) to write a URL list for mass mode."
        print "   -4 , --autoawesome            With the AutoAwesome mode fimap will fetch all"
        print "                                 forms and headers found on the site you defined"
        print "                                 and tries to find file inclusion bugs thru them. Needs an"
        print "                                 URL (-u)."
        print "## Techniques:"
        print "   -b , --enable-blind           Enables blind FI-Bug testing when no error messages are printed."
        print "                                 Note that this mode will cause lots of requests compared to the"
        print "                                 default method. Can be used with -s, -m or -g."
        print "   -D , --dot-truncation         Enables dot truncation technique to get rid of the suffix if"
        print "                                 the default mode (nullbyte poison) failed. This mode can cause"
        print "                                 tons of requests depending how you configure it."
        print "                                 By default this mode only tests windows servers."
        print "                                 Can be used with -s, -m or -g. Experimental."
        print "   -M , --multiply-term=X        Multiply terminal symbols like '.' and '/' in the path by X."
        print "## Variables:"
        print "   -u , --url=URL                The URL you want to test."
        print "                                 Needed in single mode (-s)."
        print "   -l , --list=LIST              The URL-LIST you want to test."
        print "                                 Needed in mass mode (-m)."
        print "   -q , --query=QUERY            The Google Search QUERY."
        print "                                 Example: 'inurl:include.php'"
        print "                                 Needed in Google Mode (-g)"
        print "        --skip-pages=X           Skip the first X pages from the Googlescanner."
        print "   -p , --pages=COUNT            Define the COUNT of pages to search (-g)."
        print "                                 Default is 10."
        print "        --results=COUNT          The count of results the Googlescanner should get per page."
        print "                                 Possible values: 10, 25, 50 or 100(default)."
        print "        --googlesleep=TIME       The time in seconds the Googlescanner should wait befor each"
        print "                                 request to google. fimap will count the time between two requests"
        print "                                 and will sleep if it's needed to reach your cooldown. Default is 5."
        print "   -w , --write=LIST             The LIST which will be written if you have choosen"
        print "                                 harvest mode (-H). This file will be opened in APPEND mode."
        print "   -d , --depth=CRAWLDEPTH       The CRAWLDEPTH (recurse level) you want to crawl your target site"
        print "                                 in harvest mode (-H). Default is 1."
        print "   -P , --post=POSTDATA          The POSTDATA you want to send. All variables inside"
        print "                                 will also be scanned for file inclusion bugs."
        print "        --cookie=COOKIES         Define the cookie which should be send with each request."
        print "                                 Also the cookies will be scanned for file inclusion bugs."
        print "                                 Concatenate multiple cookies with the ';' character."
        print "        --ttl=SECONDS            Define the TTL (in seconds) for requests. Default is 30 seconds."
        print "        --no-auto-detect         Use this switch if you don't want to let fimap automaticly detect"
        print "                                 the target language in blind-mode. In that case you will get some"
        print "                                 options you can choose if fimap isn't sure which lang it is."
        print "        --bmin=BLIND_MIN         Define here the minimum count of directories fimap should walk thru"
        print "                                 in blind mode. The default number is defined in the generic.xml"
        print "        --bmax=BLIND_MAX         Define here the maximum count of directories fimap should walk thru."
        print "        --dot-trunc-min=700      The count of dots to begin with in dot-truncation mode."
        print "        --dot-trunc-max=2000     The count of dots to end with in dot-truncation mode."
        print "        --dot-trunc-step=50      The step size for each round in dot-truncation mode."
        print "        --dot-trunc-ratio=0.095  The maximum ratio to detect if dot truncation was successfull."
        print "        --dot-trunc-also-unix    Use this if dot-truncation should also be tested on unix servers."
        print "        --force-os=OS            Forces fimap to test only files for the OS."
        print "                                 OS can be 'unix' or 'windows'"
        print "## Attack Kit:"
        print "   -x , --exploit                Starts an interactive session where you can"
        print "                                 select a target and do some action."
        print "   -T , --tab-complete           Enables TAB-Completation in exploit mode. Needs readline module."
        print "                                 Use this if you want to be able to tab-complete thru remote"
        print "                                 files\dirs. Eats an extra request for every 'cd' command."
        print "## Disguise Kit:"
        print "   -A , --user-agent=UA          The User-Agent which should be sent."
        print "        --http-proxy=PROXY       Setup your proxy with this option. But read this facts:"
        print "                                   * The googlescanner will ignore the proxy to get the URLs,"
        print "                                     but the pentest\\attack itself will go thru proxy."
        print "                                   * PROXY should be in format like this: 127.0.0.1:8080"
        print "                                   * It's experimental"
        print "        --show-my-ip             Shows your internet IP, current country and user-agent."
        print "                                 Useful if you want to test your vpn\\proxy self.mainconfig."
        print "## Plugins:"
        print "        --plugins                List all loaded plugins and quit after that."
        #print "   -I , --install-plugins        Shows some official exploit-mode plugins you can install "
        #print "                                 and\\or upgrade."
        print ""
        print "## Other:"
        print "        --test-rfi               A quick test to see if you have self.mainconfigured RFI nicely."
        print "        --merge-xml=XMLFILE      Use this if you have another fimap XMLFILE you want to"
        print "                                 include to your own fimap_result.xml."
        print "   -C , --enable-color           Enables a colorful output. Works only in linux!"
        print "        --force-run              Ignore the instance check and just run fimap even if a lockfile"
        print "                                 exists. WARNING: This may erase your fimap_results.xml file!"
        print "   -v , --verbose=LEVEL          Verbose level you want to receive."
        print "                                 LEVEL=3 -> Debug"
        print "                                 LEVEL=2 -> Info(Default)"
        print "                                 LEVEL=1 -> Messages"
        print "                                 LEVEL=0 -> High-Level"
        print "   -h , --help                   Shows this cruft."
        print "## Examples:"
        print "  1. Scan a single URL for FI errors:"
        print "        ./fimap.py -u 'http://localhost/test.php?file=bang&id=23'"
        print "  2. Scan a list of URLS for FI errors:"
        print "        ./fimap.py -m -l '/tmp/urllist.txt'"
        print "  3. Scan Google search results for FI errors:"
        print "        ./fimap.py -g -q 'inurl:include.php'"
        print "  4. Harvest all links of a webpage with recurse level of 3 and"
        print "     write the URLs to /tmp/urllist"
        print "        ./fimap.py -H -u 'http://localhost' -d 3 -w /tmp/urllist"
        # Exit if flag AndQuit is True
        if (AndQuit):
            sys.exit(0)

    def show_ip(self):
        '''
        Method for shows information about IP address.
        '''

        print "Heading to 'http://85.214.27.38/show_my_ip'..."
        print "----------------------------------------------"
        # Create instance of class codeinjector and pass the param
        tester = codeinjector(self.mainconfig)
        # Call method doGetRequest from Class codeinjector
        result = tester.doGetRequest("http://85.214.27.38/show_my_ip")
        # If result is None - exit with code 1
        # else, split result and print it
        if (result == None):
            print "result = None -> Failed! Maybe you have no connection or bad proxy?"
            sys.exit(1)
        print result.strip()
        sys.exit(0)

    def list_results(self, lst = os.path.join(os.path.expanduser("~"), "fimap_result.xml")):
        '''
        Method for show result form XML file.
        '''

        # If file already exists - exit
        # Otherwise create it.
        if (not os.path.exists(lst)):
            print "File not found! ~/fimap_result.xml"
            sys.exit(1)
        # Create instance of class codeinjector and pass the param
        c = codeinjector(self.mainconfig)
        # Call method start from Class codeinjector
        c.start()
        sys.exit(0)

    def show_report(self):
        '''
        Method that shows report about possible new bugs.
        '''

        # Check if there were found new bugs.
        if (len(baseClass.new_stuff.items()) > 0):
            print "New FI Bugs found in this session:"
            for k,v in baseClass.new_stuff.items():
                print "\t- %d (probably) usable FI-Bugs on '%s'."%(v, k)

    def main(self, arg):
        '''
        Main method of the class.
        Note that it's just a name unlike java...
        See below for the entry point of the program.

        #If no arg are passed to main, we grab argv from main.py wrapper.
        #Argv is a list of args.
        '''

        #FIMAP Comment :  User variables
        self.mainconfig["p_url"] = None
        self.mainconfig["p_mode"] = 0 # 0=single ; 1=mass ; 2=google ; 3=crawl ; 4=autoawesome
        self.mainconfig["p_list"] = None
        self.mainconfig["p_verbose"] = 2
        self.mainconfig["p_useragent"] = "fimap.googlecode.com/"
        self.mainconfig["p_pages"] = 10
        self.mainconfig["p_query"] = None
        self.mainconfig["p_exploit_filter"] = ""
        self.mainconfig["p_write"] = None
        self.mainconfig["p_depth"] = 1
        self.mainconfig["p_maxtries"] = 5
        self.mainconfig["p_skippages"] = 0
        self.mainconfig["p_monkeymode"] = False
        self.mainconfig["p_doDotTruncation"] = False
        self.mainconfig["p_dot_trunc_min"] = 700
        self.mainconfig["p_dot_trunc_max"] = 2000
        self.mainconfig["p_dot_trunc_step"] = 50
        self.mainconfig["p_dot_trunc_ratio"] = 0.095
        self.mainconfig["p_dot_trunc_only_win"] = True
        self.mainconfig["p_proxy"] = None
        self.mainconfig["p_ttl"] = 30
        self.mainconfig["p_post"] = ""
        self.mainconfig["p_autolang"] = True
        self.mainconfig["p_color"] = False
        self.mainconfig["p_mergexml"] = None
        self.mainconfig["p_results_per_query"] = 100
        self.mainconfig["p_googlesleep"] = 5
        self.mainconfig["p_tabcomplete"] = False
        self.mainconfig["p_multiply_term"] = 1
        self.mainconfig["header"] = {}
        self.mainconfig["force-run"] = False
        self.mainconfig["force-os"] = None
        self.mainconfig["p_rfi_encode"] = None
        doPluginsShow = False
        doRFITest = False
        doInternetInfo = False
        doInstallPlugins = False
        doMergeXML = False
        blind_min = None
        blind_max = None

        # Check that there is no empty arg.
        if (len(arg) < 1):
            #show_help(True)
            # Show help if were found keys: -h or --help
            if arg[0] == '-h' or arg[0] == '--help':
                self.show_help(True)
            else:
                print "Use -h or --help for some help."
                sys.exit(0)

        try:
            longSwitches = ["url="          , "mass"        , "single"      , "list="       , "verbose="        , "help",
                        "user-agent="   , "query="      , "google"      , "pages="      , "credits"         , "exploit",
                        "harvest"       , "write="      , "depth="      , "greetings"   , "test-rfi"        , "skip-pages=",
                        "show-my-ip"    , "enable-blind", "http-proxy=" , "ttl="        , "post="           , "no-auto-detect",
                        "plugins"       , "enable-color", "merge-xml="  , "install-plugins" , "results=",
                        "googlesleep="  , "dot-truncation", "dot-trunc-min=", "dot-trunc-max=", "dot-trunc-step=", "dot-trunc-ratio=",
                        "tab-complete"  , "cookie="     , "bmin="        , "bmax="      , "dot-trunc-also-unix", "multiply-term=",
                        "autoawesome"   , "force-run"   , "force-os="   , "rfi-encoder=", "header="]
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
            optlist, args = getopt.getopt(arg, "u:msl:v:hA:gq:p:sxHw:d:bP:CIDTM:4R:", longSwitches)

            startExploiter = False

            # Here we check options returned in by getopt
            # we make a for statement on this list
            # o and a are iterator on option type and args values
            # for exemple if optlist = [('-h',''),('-s','3')]
            # first loop : v = '-h' and a= ''
            # second loop : v = '-s' and a='3'
            # Options are registered in member class variables.
            for k,v in optlist:
                if (k in ("-u", "--url")):
                    self.mainconfig["p_url"] = v
                if (k in ("-s", "--single")):
                    self.mainconfig["p_mode"] = 0
                if (k in ("-m", "--mass")):
                    self.mainconfig["p_mode"] = 1
                if (k in ("-g", "--google")):
                    self.mainconfig["p_mode"] = 2
                if (k in ("-H", "--harvest")):
                    self.mainconfig["p_mode"] = 3
                if (k in ("-4", "--autoawesome")):
                    self.mainconfig["p_mode"] = 4
                if (k in ("-l", "--list")):
                    self.mainconfig["p_list"] = v
                if (k in ("-q", "--query")):
                    self.mainconfig["p_query"] = v
                if (k in ("-v", "--verbose")):
                    self.mainconfig["p_verbose"] = int(v)
                if (k in ("-p", "--pages")):
                    self.mainconfig["p_pages"] = int(v)
                if (k in ("--results",)):
                    self.mainconfig["p_results_per_query"] = int(v)
                if (k in ("--googlesleep",)):
                    self.mainconfig["p_googlesleep"] = int(v)
                if (k in ("-A", "--user-agent")):
                    self.mainconfig["p_useragent"] = v
                if (k in ("--http-proxy",)):
                    self.mainconfig["p_proxy"] = v
                if (k in ("-w", "--write")):
                    self.mainconfig["p_write"] = v
                if (k in ("-d", "--depth")):
                    self.mainconfig["p_depth"] = int(v)
                if (k in ("--ttl",)):
                    self.mainconfig["p_ttl"] = int(v)
                if (k in ("-h", "--help")):
                    self.show_help(True)
                if (k in ("--test-rfi",)):
                    doRFITest = True
                if (k in ("-b", "--enable-blind")):
                    self.mainconfig["p_monkeymode"] = True
                if (k in ("-D", "--dot-truncation")):
                    self.mainconfig["p_doDotTruncation"] = True
                if (k in ("-C", "--enable-color")):
                    self.mainconfig["p_color"] = True
                if (k in ("--skip-pages",)):
                    self.mainconfig["p_skippages"] = int(v)
                if (k in ("--show-my-ip",)):
                    doInternetInfo = True
                if (k in("-x", "--exploit")):
                    startExploiter = True
                if (k in ("-P", "--post")):
                    self.mainconfig["p_post"] = v
                if (k in ("--no-auto-detect", )):
                    self.mainconfig["p_autolang"] = False
                if (k in ("--plugins",)):
                    doPluginsShow = True
                if (k in ("-I", "--install-plugins")):
                    doInstallPlugins = True
                if (k in ("--merge-xml",)):
                    doMergeXML = True
                    self.mainconfig["p_mergexml"] = v
                if (k in ("--dot-trunc-min",)):
                    self.mainconfig["p_dot_trunc_min"] = int(v)
                if (k in ("--dot-trunc-max",)):
                    self.mainconfig["p_dot_trunc_max"] = int(v)
                if (k in ("--dot-trunc-step",)):
                    self.mainconfig["p_dot_trunc_step"] = int(v)
                if (k in ("--dot-trunc-ratio",)):
                    self.mainconfig["p_dot_trunc_ratio"] = float(v)
                if (k in ("--dot-trunc-also-unix",)):
                    self.mainconfig["p_dot_trunc_only_win"] = False
                if (k in ("-T", "--tab-complete")):
                    self.mainconfig["p_tabcomplete"] = True
                if (k in ("-M", "--multiply-term")):
                    self.mainconfig["p_multiply_term"] = int(v)
                if (k in ("--cookie",)):
                    self.mainconfig["header"]["Cookie"] = v
                if (k in ("--header",)):
                    head  = None
                    value = ""
                    if (v.find(":") == -1):
                        head = v
                    else:
                        head = v.split(":")[0]
                        value = ":".join(v.split(":")[1:])
                    self.mainconfig["header"][head] = value
                if (k in ("--bmin",)):
                    blind_min = int(v)
                if (k in ("--bmax",)):
                    blind_max = int(v)
                if (k in ("--force-run",)):
                    self.mainconfig["force-run"] = True
                if (k in ("--force-os",)):
                    self.mainconfig["force-os"] = v
                if (k in ("--rfi-encoder")):
                    self.mainconfig["p_rfi_encode"] = v
                #if (k in("-f", "--exploit-filter")):
                #    self.mainconfig["p_exploit_filter"] = v

            # Create instance of class codeinjector and pass the param
            xmlsettings = language.XML2Config(self.mainconfig)

            # Ape style lockfile. But it works! :)
            lockFound = False
            curlockfile = None
            # Check if another process of fimap is already runned. If so, exit with error message.
            # Otherwise create new lockfile
            for f in os.listdir(tempfile.gettempdir()):
                if f.startswith("fimap_") and f.endswith("_lockfile"):
                    lockFound = True
                    curlockfile = f
                    break
            # Only one instance of fimap can be run
            if (lockFound):
                if (self.mainconfig["force-run"] == True):
                    print "Another fimap instance is running! But you requested to ignore that..."
                else:
                    print "Another fimap instance is already running!"
                    print "If you think this is not correct please delete the following file:"
                    print "-> " + os.path.join(tempfile.gettempdir(), curlockfile)
                    print "or start fimap with '--force-run' on your own risk."
                    sys.exit(0)
            else:
                lockfile = tempfile.NamedTemporaryFile(prefix="fimap_", suffix="_lockfile")

            # Setup possibly changed engine settings.
            if (blind_min != None):
                xmlsettings.blind_min = blind_min
                print "Overwriting 'blind_min' setting to %s..." %(blind_min)
            if (blind_max != None):
                xmlsettings.blind_max = blind_max
                print "Overwriting 'blind_max' setting to %s..." %(blind_max)

            self.mainconfig["XML2CONFIG"] = xmlsettings

            # Create instance of class plugininterface and pass the param
            plugman = plugininterface(self.mainconfig)
            self.mainconfig["PLUGINMANAGER"] = plugman

            # If startExploiter is True then call method self.list_results()
            if startExploiter:
                try:
                    self.list_results()
                except KeyboardInterrupt:
                    print "\n\nYou killed me brutally.\n\n"
                    sys.exit(0)
        # This is raised when an unrecognized option is found in the argument list or when an option requiring
        # an argument is given none. The argument to the exception is a string indicating the cause of the error.
        except getopt.GetoptError, err:
            print (err)
            # Exit with error code 1
            sys.exit(1)

        # If doInstallPlugins is True then create instance of codeinjector and pass the param
        # Requesting list of plugins
        if doInstallPlugins:
            print "Requesting list of plugins..."
            tester = codeinjector(self.mainconfig)
            # Call method doGetRequest from class codeinjector with param
            result = tester.doGetRequest(self.pluginlist)

            # If result is None then exit with Error code 1
            if result == None:
                print "Failed to request plugins! Are you online?"
                sys.exit(1)

            choice = {}
            idx = 1
            # Parse the result and creates plugin list
            for line in result.split("\n"):
                tokens = line.split("|")
                label = tokens[0].strip()
                name = tokens[1].strip()
                version = int(tokens[2].strip())
                url = tokens[3].strip()
                choice[idx] = (label, name, version, url)
                idx += 1
            pluginman = self.mainconfig["PLUGINMANAGER"]

            # Create instance of baseTools.baseTools
            tools = baseTools.baseTools()
            header = "LIST OF TRUSTED PLUGINS"
            boxarr = []
            for k,(l,n,v,u) in choice.items():
                # Create instance of pluginman.getPluginVersion and pass the param
                instver = pluginman.getPluginVersion(n)
                if (instver == None):
                    boxarr.append("[%d] %s - At version %d not installed." %(k, l, v))
                elif (instver < v):
                    boxarr.append("[%d] %s - At version %d has an UPDATE." %(k, l, v))
                else:
                    boxarr.append("[%d] %s - At version %d is up-to-date and installed." %(k, l, v))
            boxarr.append("[q] Cancel and Quit.")
            # Call method drawBox from class baseTools with params
            tools.drawBox(header, boxarr, False)
            nr = None

            # Takes plugin from stdin that will be installed.
            nr = raw_input("Choose a plugin to install: ")
            # if "nr" is equal to "q" then exit without any actions
            # Otherwise try to install plugin
            if (nr != "q"):
                (l,n,v,u) = choice[int(nr)]
                print "Downloading plugin '%s' (%s)..." %(n, u)
                # Make HTTP request and trying to download plugin
                # If plugin is None then print error message
                plugin = tester.doGetRequest(u)
                if (plugin != None):
                    # Creating temp file and writing result of HTTP request into this file.
                    tmpFile = tempfile.mkstemp()[1] + ".tar.gz"
                    f = open(tmpFile, "wb")
                    f.write(plugin)
                    f.close()

                    # Try to unpack downloaded plugin
                    # If failed, print an error message.
                    print "Unpacking plugin..."
                    try:
                        # The tarfile module makes it possible to read and write tar archives,
                        # including those using gzip or bz2 compression.
                        # For more details: http://docs.python.org/2/library/tarfile.html
                        # Return a TarFile object for the pathname name.
                        tar = tarfile.open(tmpFile, 'r:gz')
                        tmpdir = tempfile.mkdtemp()
                        # Extract all members from the archive to the current working directory or directory path
                        tar.extractall(tmpdir)
                        pluginxml = os.path.join(tmpdir, n, "plugin.xml")
                        pluginsdir = os.path.join(sys.path[0], "plugins")

                        if (os.path.exists(pluginxml)):
                            # Creates and instance of class pluginXMLInfo and pass the param
                            info = pluginXMLInfo(pluginxml)
                            # try to get version of plugin
                            ver = pluginman.getPluginVersion(info.getStartupClass())
                            # Check if plugin does not installed
                            if (ver != None):
                                inp = ""
                                # Check if downloaded plugin has new version.
                                # Waiting stdin args
                                if (ver > info.getVersion()):
                                    inp = raw_input("Do you really want to downgrade this plugin? [y/N]")
                                elif (ver == info.getVersion()):
                                    inp = raw_input("Do you really want to reinstall this plugin? [y/N]")
                                # If "Y" or "y" than install it
                                # Otherwise, exit with code 0
                                if (inp == "Y" or inp == "y"):
                                    dir = info.getStartupClass()
                                    deldir = os.path.join(pluginsdir, dir)
                                    print "Deleting old plugin directory..."
                                    shutil.rmtree(deldir)
                                else:
                                    print "OK aborting..."
                                    sys.exit(0)
                            tar.extractall(os.path.join(pluginsdir))
                            print "Plugin '%s' installed successfully!" %(info.getName())
                        else:
                            print "Plugin doesn't have a plugin.xml! (%s)" %pluginxml
                            sys.exit(1)

                    except:
                        print "Unpacking failed!"
                        #sys.exit(0)
                else:
                    print "Failed to download plugin package!"

            sys.exit(0)

        # If doPluginsShow is True, show iniformation about installed plugins
        if doPluginsShow:
            plugins = self.mainconfig["PLUGINMANAGER"].getAllPluginObjects()
            if (len(plugins) > 0):
                for plug in plugins:
                    print "[Plugin: %s] by %s (%s)" %(plug.getPluginName(), plug.getPluginAutor(), plug.getPluginEmail())
            else:
                print "No plugins :T"
            sys.exit(0)

        # If doMergeXML is True, Add new vulnerabilities into XML config.
        if doMergeXML:
            tester = codeinjector(self.mainconfig)
            newVulns, newDomains = tester.mergeXML(self.mainconfig["p_mergexml"])
            print "%d new vulnerabilitys added from %d new domains." %(newVulns, newDomains)
            sys.exit(0)

        # Upgrade XML if needed...
        bc = baseClass.baseClass(self.mainconfig)
        bc.testIfXMLIsOldSchool()

        # If doRFITest is True then Perform some RFI test and exit with code 0
        if doRFITest:
            # Create instance of class condeinjector and pass the param
            injector = codeinjector(self.mainconfig)
            # Call method testRFI()
            injector.testRFI()
            sys.exit(0)
        else:
            # Test RFI settings stupidly.
            # Take default settings from config.py
            from config import settings
            if settings["dynamic_rfi"]["mode"] == "local":
                if settings["dynamic_rfi"]["local"]["local_path"] == None or \
                                settings["dynamic_rfi"]["local"]["http_map"] == None:
                    print "Invalid Dynamic_RFI self.mainconfig!"
                    print "local_path and\\or http_map is not defined for local mode!"
                    print "Fix that in config.py"
                    sys.exit(1)
            elif settings["dynamic_rfi"]["mode"] == "ftp":
                if settings["dynamic_rfi"]["ftp"]["ftp_host"] == None or \
                                settings["dynamic_rfi"]["ftp"]["ftp_user"] == None or \
                                settings["dynamic_rfi"]["ftp"]["ftp_pass"] == None or \
                                settings["dynamic_rfi"]["ftp"]["ftp_path"] == None or \
                                settings["dynamic_rfi"]["ftp"]["http_map"] == None:
                    print "Invalid Dynamic_RFI config!"
                    print "One of your FTP self.mainconfig values is missing!"
                    print "Fix that in config.py"
                    sys.exit(1)

        if (self.mainconfig["p_proxy"] != None):
            print "Using HTTP-Proxy '%s'." %(self.mainconfig["p_proxy"])

        # Call method that print information about your IP
        if (doInternetInfo):
            self.show_ip()

        # Check that important parameters have been set
        if (self.mainconfig["p_url"] == None and self.mainconfig["p_mode"] == 0):
            print self.mainconfig["p_url"]
            print "Target URL required. (-u)"
            sys.exit(1)
        if (self.mainconfig["p_list"] == None and self.mainconfig["p_mode"] == 1):
            print "URLList required. (-l)"
            sys.exit(1)
        if (self.mainconfig["p_query"] == None and self.mainconfig["p_mode"] == 2):
            print "Google Query required. (-q)"
            sys.exit(1)
        if (self.mainconfig["p_url"] == None and self.mainconfig["p_mode"] == 3):
            print "Start URL required for harvesting. (-u)"
            sys.exit(1)
        if (self.mainconfig["p_write"] == None and self.mainconfig["p_mode"] == 3):
            print "Output file to write the URLs to is needed in Harvest Mode. (-w)"
            sys.exit(1)
        if (self.mainconfig["p_url"] == None and self.mainconfig["p_mode"] == 4):
            print "Root URL required for AutoAwesome. (-u)"
            sys.exit(1)
        if (self.mainconfig["p_monkeymode"] == True):
            print "Blind FI-error checking enabled."

        if (self.mainconfig["force-os"] != None):
            if (self.mainconfig["force-os"] != "unix" and self.mainconfig["force-os"] != "windows"):
                print "Invalid parameter for 'force-os'."
                print "Only 'unix' or 'windows' are allowed!"
                sys.exit(1)


        try:
            # Parse p_mode and launch appropriate method
            # 0 - single URL
            # 1 - mass URL. URLs will be taken from list
            # 2 - Google Scan
            # 3 - Crawler
            # 4 - AutoAwesome mode
            if (self.mainconfig["p_mode"] == 0):
                single = singleScan(self.mainconfig)
                single.setURL(self.mainconfig["p_url"])
                single.scan()

            elif(self.mainconfig["p_mode"] == 1):
                if (not os.path.exists(self.mainconfig["p_list"])):
                    print "Your defined URL-List doesn't exist: '%s'" % self.mainconfig["p_list"]
                    sys.exit(0)
                print "MassScanner is loading URLs from file: '%s'" % self.mainconfig["p_list"]
                m = massScan(self.mainconfig)
                m.startMassScan()
                self.show_report()

            elif(self.mainconfig["p_mode"] == 2):
                print "GoogleScanner is searching for Query: '%s'" % self.mainconfig["p_query"]
                g = googleScan(self.mainconfig)
                g.startGoogleScan()
                self.show_report()

            elif(self.mainconfig["p_mode"] == 3):
                print "Crawler is harvesting URLs from start URL: '%s' with depth: %d and writing results to: '%s'" %(self.mainconfig["p_url"], self.mainconfig["p_depth"], self.mainconfig["p_write"])
                c = crawler(self.mainconfig)
                c.crawl()

            elif(self.mainconfig["p_mode"] == 4):
                print "AutoAwesome mode engaging URL '%s'..." % (self.mainconfig["p_url"])
                awe = autoawesome.autoawesome(self.mainconfig)
                awe.setURL(self.mainconfig["p_url"])
                awe.scan()

        except KeyboardInterrupt:
            print "\n\nYou have terminated me :("

        except Exception, err:
            print "\n\n========= CONGRATULATIONS! ========="
            print "You have just found a bug!"
            print "Exception: %s" % err
            raise
