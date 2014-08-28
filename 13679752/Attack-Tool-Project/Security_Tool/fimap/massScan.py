#
# This file is part of fimap.
#

from targetScanner import targetScanner
from singleScan import singleScan


class massScan:

    def __init__(self, config):
        self.config = config
        self.list = config["p_list"]

    def startMassScan(self):
        print "MassScan reading file: '%s'..."%self.list

        f = open(self.list, "r")
        idx = 0
        for l in f:
            if idx >= 0:
                l = l.strip()
                if (l.startswith("http://"), l.startswith("https://")):
                    print "[%d][MASS_SCAN] Scanning: '%s'..." %(idx,l)
                    single = singleScan(self.config)
                    single.setURL(l)
                    single.setQuite(True)
                    single.scan()

                    idx = idx +1

        print "MassScan completed."