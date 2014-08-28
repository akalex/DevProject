#
# This file is part of fimap.
#

from singleScan import singleScan
from targetScanner import targetScanner
from xgoogle.search import GoogleSearch
import datetime
import sys,time


class googleScan:

    def __init__(self, config):
        self.config = config
        self.gs = GoogleSearch(self.config["p_query"], page=self.config["p_skippages"], random_agent=True)
        self.gs.results_per_page = self.config["p_results_per_query"];
        self.cooldown = self.config["p_googlesleep"];
        if (self.config["p_skippages"] > 0):
            print "Google Scanner will skip the first %d pages..."%(self.config["p_skippages"])

    def getNextPage(self):
        results = self.gs.get_results()

        return(results)

    def startGoogleScan(self):
        print "Querying Google Search: '%s' with max pages %d..."%(self.config["p_query"], self.config["p_pages"])

        pagecnt = 0
        curtry = 0
        
        last_request_time = datetime.datetime.now()

        while(pagecnt < self.config["p_pages"]):
            pagecnt = pagecnt +1
            redo = True
            while (redo):
              try:
                current_time = datetime.datetime.now()
                diff = current_time - last_request_time
                diff = int(diff.seconds)

                if (diff <= self.cooldown):
                    if (diff > 0): 
                        print "Commencing %ds google cooldown..." %(self.cooldown - diff)
                        time.sleep(self.cooldown - diff)
                    
                last_request_time = datetime.datetime.now()
                results = self.getNextPage()
                
                redo = False
              except KeyboardInterrupt:
                raise
              except Exception, err:
                print err
                redo = True
                sys.stderr.write("[RETRYING PAGE %d]\n" %(pagecnt))
                curtry = curtry +1
                if (curtry > self.config["p_maxtries"]):
                    print "MAXIMAL COUNT OF (RE)TRIES REACHED!"
                    sys.exit(1)

            curtry = 0

            if (len(results) == 0): break
            sys.stderr.write("[PAGE %d]\n" %(pagecnt))
            try:
                for r in results:
                    single = singleScan(self.config)
                    single.setURL(r.url)
                    single.setQuite(True)
                    single.scan()
            except KeyboardInterrupt:
                raise
            time.sleep(1)
        print "Google Scan completed."