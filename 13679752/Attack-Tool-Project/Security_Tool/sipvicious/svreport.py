#!/usr/bin/env python
# SIPVicious report engine

from libs.svhelper import __version__
__prog__   = 'svreport'

import anydbm
from xml.dom.minidom import Document
from optparse import OptionParser
from sys import exit
import os
import logging
import socket
from datetime import datetime


# Class SVREPORT : inherits from the base class object. New-style Classes
# Mandatory and optional args can be identified with the __init__ method
class SVREPORT(object):

    #SVREPORT Comment :  beware if you change anything below - execution starts here
    def main(self):
        #Here is the main function of the class.
        #Note that it's just a name unlike java...
        #See below for the entry point of the program.
        commandsusage = """Supported commands:\r\n
                - list:\tlists all scans\r\n
                - export:\texports the given scan to a given format\r\n
                - delete:\tdeletes the scan\r\n
                - stats:\tprint out some statistics of interest\r\n
                - search:\tsearch for a specific string in the user agent (svmap)\r\n
        """
        commandsusage += "examples:\r\n\r\n"
        commandsusage += "      %s.py list\r\n\r\n" % __prog__
        commandsusage += "      %s.py svreport export -f pdf -o scan1.pdf -s scan1\r\n\r\n" % __prog__
        commandsusage += "      %s.py svreport delete -s scan1\r\n\r\n" % __prog__
        usage = "%prog [command] [options]\r\n\r\n"
        usage += commandsusage
        # Parse arguments.
        # The OptionParser constructor has no required arguments, but a number of optional keyword arguments.
        # You should always pass them as keyword arguments, i.e. do not rely on the order in which the arguments are declared.
        # More about this method of parsing, see there http://docs.python.org/2/library/optparse.html#optparse.OptionParser
        parser = OptionParser(usage=usage,version="%prog v"+str(__version__))
        parser.add_option('-v', '--verbose', dest="verbose", action="count",
                          help="Increase verbosity")
        parser.add_option('-q', '--quiet', dest="quiet", action="store_true",
                          default=False,
                          help="Quiet mode")
        parser.add_option("-t", "--type", dest="sessiontype",
                        help="Type of session. This is usually either svmap, svwar or svcrack. If not set I will try to find the best match")
        parser.add_option("-s", "--session", dest="session",
                        help="Name of the session")
        parser.add_option("-f", "--format", dest="format",
                        help="Format type. Can be stdout, pdf, xml, csv or txt")
        parser.add_option("-o", "--output", dest="outputfile",
                        help="Output filename")
        parser.add_option("-n", dest="resolve", default=True,
                          action="store_false", help="Do not resolve the ip address")
        parser.add_option("-c", "--count", dest="count", default=False,
                          action="store_true", help="Used togather with 'list' command to count the number of entries")
        (options,args) = parser.parse_args()
        # Check that there is no empty arg.
        if len(args) <= 1:
                parser.error("Please specify a command.\r\n")
                exit(1)
        command = args[1]
        # Import additional modules
        from libs.svhelper import listsessions,deletesessions,createReverseLookup, dbexists
        from libs.svhelper import getsessionpath,getasciitable,outputtoxml,outputtopdf, calcloglevel
        # Create list of valid commands that can use
        validcommands = ['list','export','delete','stats','search']
        if command not in validcommands:
                parser.error('%s is not a supported command' % command)
                exit(1)
        # Does basic configuration for the logging system by creating a StreamHandler with a default
        # Formatter and adding it to the root logger. The functions debug(), info(), warning(), error() and
        # critical() will call basicConfig() automatically if no handlers are defined for the root logger.
        logging.basicConfig(level=calcloglevel(options))
        sessiontypes = ['svmap','svwar','svcrack']
        logging.debug('started logging')        
        if command == 'list':
                # Get current sessions. If they are
                listsessions(options.sessiontype,count=options.count)
        if command == 'delete':
                if options.session is None:
                        parser.error("Please specify a valid session.")
                        exit(1)
                sessionpath = deletesessions(options.session,options.sessiontype)
                if sessionpath is None:
                        parser.error('Session could not be found. Make sure it exists by making use of %s.py list' % __prog__)
                        exit(1)
        elif command == 'export':
                start_time = datetime.now()
                if options.session is None:
                        parser.error("Please specify a valid session")
                        exit(1)
                if options.outputfile is None and options.format not in [None,'stdout']:
                        parser.error("Please specify an output file")
                        exit(1)
                tmp = getsessionpath(options.session,options.sessiontype)                
                if tmp is None:
                        parser.error('Session could not be found. Make sure it exists by making use of %s list' % __prog__)
                        exit(1)
                sessionpath,sessiontype = tmp
                resolve = False
                resdb = None
                if sessiontype == 'svmap':
                        dbloc = os.path.join(sessionpath,'resultua')
                        labels = ['Host','User Agent']
                elif sessiontype == 'svwar':
                        dbloc = os.path.join(sessionpath,'resultauth')
                        labels = ['Extension','Authentication']
                elif sessiontype == 'svcrack':
                        dbloc = os.path.join(sessionpath,'resultpasswd')
                        labels = ['Extension','Password']
                if not dbexists(dbloc):
                        logging.error('The database could not be found: %s'%dbloc)
                        exit(1)
                db = anydbm.open(dbloc,'r')

                if options.resolve and sessiontype == 'svmap':
                        resolve = True
                        labels.append('Resolved')                                
                        resdbloc = os.path.join(sessionpath,'resolved')
                        if not dbexists(resdbloc):
                                logging.info('Performing DNS reverse lookup')
                                resdb = anydbm.open(resdbloc,'c')
                                createReverseLookup(db,resdb)
                        else:
                                logging.info('Not Performing DNS lookup')
                                resdb = anydbm.open(resdbloc,'r')

                if options.outputfile is not None:
                        if options.outputfile.find('.') < 0:
                                if options.format is None:
                                        options.format = 'txt'
                                options.outputfile += '.%s' % options.format

                if options.format in [None,'stdout','txt']:
                        o = getasciitable(labels,db,resdb)
                        if options.outputfile is None:
                                print o
                        else:
                                open(options.outputfile,'w').write(o)
                elif options.format == 'xml':
                        doc = Document()
                        node = doc.createElement(sessiontype)                        
                        o = outputtoxml('%s report' % sessiontype,labels,db,resdb)
                        open(options.outputfile,'w').write(o)
                elif options.format == 'pdf':
                        outputtopdf(options.outputfile,'%s report' % sessiontype,labels,db,resdb)
                elif options.format == 'csv':
                        import csv
                        writer = csv.writer(open(options.outputfile,"w"))
                        for k in db.keys():
                                row = [k,db[k]]
                                if resdb is not None:
                                        if resdb.has_key(k):
                                                row.append(resdb[k])
                                        else:
                                                row.append('N/A')
                                writer.writerow(row)
                logging.info( "That took %s" % (datetime.now() - start_time))
        elif command == 'stats':
                from operator import itemgetter
                import re                
                if options.session is None:
                        parser.error("Please specify a valid session")
                        exit(1)
                if options.outputfile is None and options.format not in [None,'stdout']:
                        parser.error("Please specify an output file")
                        exit(1)
                tmp = getsessionpath(options.session,options.sessiontype)                
                if tmp is None:
                        parser.error('Session could not be found. Make sure it exists by making use of %s list' % __prog__)
                        exit(1)
                sessionpath,sessiontype = tmp
                if sessiontype != 'svmap':
                        parser.error('Only takes svmap sessions for now')
                        exit(1)
                dbloc = os.path.join(sessionpath,'resultua')
                if not dbexists(dbloc):
                        logging.error('The database could not be found: %s'%dbloc)
                        exit(1)
                db = anydbm.open(dbloc,'r')
                useragents = dict()
                useragentconames = dict()
                for k in db.keys():
                        v = db[k]
                        if not useragents.has_key(v):
                                useragents[v] = 0
                        useragents[v]+=1
                        useragentconame = re.split('[ /]',v)[0]
                        if not useragentconames.has_key(useragentconame):
                                useragentconames[useragentconame] = 0
                        useragentconames[useragentconame] += 1
                        
                _useragents = sorted(useragents.iteritems(), key=itemgetter(1), reverse=True)
                suseragents = map(lambda x: '\t- %s (%s)' % (x[0],x[1]), _useragents)
                _useragentsnames = sorted(useragentconames.iteritems(), key=itemgetter(1), reverse=True)
                suseragentsnames = map(lambda x: '\t- %s (%s)' % (x[0],x[1]), _useragentsnames)
                print "Total number of SIP devices found: %s" % len(db.keys())
                print "Total number of useragents: %s\r\n" % len(suseragents)
                print "Total number of useragent names: %s\r\n" % len(suseragentsnames)
                
                print "Most popular top 30 useragents:\r\n"
                print '\r\n'.join(suseragents[:30])
                print '\r\n\r\n'
                print "Most unpopular top 30 useragents:\r\n\t"
                print '\r\n'.join(suseragents[-30:])
                print "\r\n\r\n"
                print "Most popular top 30 useragent names:\r\n"
                print '\r\n'.join(suseragentsnames[:30])
                print '\r\n\r\n'
                print "Most unpopular top 30 useragent names:\r\n\t" 
                print '\r\n'.join(suseragentsnames[-30:])
                print "\r\n\r\n"
        elif command == 'search':
                if options.session is None:
                        parser.error("Please specify a valid session")
                        exit(1)
                if len(args) < 2:
                        parser.error('You need to specify a search string')
                searchstring = args[1]
                tmp = getsessionpath(options.session,options.sessiontype)                
                if tmp is None:
                        parser.error('Session could not be found. Make sure it exists by making use of %s list' % __prog__)
                        exit(1)
                sessionpath,sessiontype = tmp
                if sessiontype != 'svmap':
                        parser.error('Only takes svmap sessions for now')
                        exit(1)
                dbloc = os.path.join(sessionpath,'resultua')
                if not dbexists(dbloc):
                        logging.error('The database could not be found: %s'%dbloc)
                        exit(1)
                db = anydbm.open(dbloc,'r')
                useragents = dict()
                useragentconames = dict()
                labels = ['Host','User Agent']
                for k in db.keys():
                        v = db[k]
                        if searchstring.lower() in v.lower():
                                print k+'\t'+v
