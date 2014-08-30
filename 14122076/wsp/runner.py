#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import datetime
from nmapscan.nmapscanner import Nmap_Vuln_Scan
from vulndb.vulndbscanner import VulnDB_Scan
from wpscan.wpscanner import WP_Scan

def usage():
    """How To?
python2.7 runner.py <scan_type> <target>

Available scan_types:
full - Executes all available scans
 
owasp_topten - The OWASP top 10 scan needs to check for:
	1) Injection vulnerabilities
	2) Authentication/Authorization, and Session Management issues
	3) Cross Site Scripting
	4) Insecure Direct Object References
	5) Security Misconfiguration
	6) Sensitive Data Exposure
	7) Missing function level access control
	8) Cross Site Request Forgery
	9) Unvalidated Redirects and Forwarders

pci - This scan checks for:
	1) Injection (SQL, LDAP, and Xpath flaws)
	2) Buffer overflows
	3) Insecure cryptographic storage
	4) Insecure communications/transport layer protection
	5) Information leakage and improper error handling
	6) All high vulnerabilities (Reference: PCI Req. 6.2)
	7) Cross site scripting (XSS)
	8) Improper access controls
	9) Cross site request forgery (CSRF)

Example: python2.7 runner.py full domain.com
    """

if __name__ == "__main__":
    if len(sys.argv) >= 3:
	scan_type = sys.argv[1]
	target = sys.argv[2:]
    	start_dt = datetime.datetime.today()
	list_of_classes = []
	if scan_type == "full":
    	    list_of_classes = [VulnDB_Scan, Nmap_Vuln_Scan, WP_Scan]
	else:
	    list_of_classes = [Nmap_Vuln_Scan]
	for host in target:
    	    for cls in list_of_classes:
            	child = cls(host)
                child.engine()
        print datetime.datetime.today() - start_dt
    else:
	print usage.__doc__
