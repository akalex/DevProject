#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import here your modules
from recon.recon import Recon
from dork.dork import Dork
from dns_geoip.dns_geoip import Dns
from dir_admin.dir_admin import Dir_admin
from waf.waf import WAF
from load_bal.load_bal import Loadbal
from fimap.fimap import FIMAP as WAAF
from wifite.wifite import WIFITE as WIFI
from findmyhash.findmyhash import FINDMYHASH as HASH
from db_attack.mysql import MYSQLDB_SCANNER as DBATTACK
from sipvicious.svmap import SVMAP
from sipvicious.svwar import SVWAR
from sipvicious.svcrack import SVCRACK
from sipvicious.svreport import SVREPORT
from sipvicious.svcrash import SVCRASH
from phishing.phishing import Phishing_Detector
import sys


class ENGINE(object):
	'''
	Class includes different modules to identify vulnerabilities, such as:
	1) Basic Recon
	2) Google/Bing Dork Attack Functionality
	3) DNS Bruteforce with Geo-IP lookups
	4) Directory Bruteforcer and AdminPage Finder
	5) Load Balancer Detection
	6) Web Application Firewall Detection
	7) Web Application Attack Functionality
	8) Wireless Attack Functionality
	9) Password Cracking Functionality
	10) Database Attack
	11) Network & VoIP Attack
	'''

	def usage(self):
		print """
Usage: python main.py <Command>
	Recon       : Basic Recon Functionality
	Dork        : Google/Bing Dork Attack Functionality
	Dns         : DNS Bruteforce with Geo-IP lookups
	Admin       : Directory Bruteforcer and AdminPage Finder
	LoadBal     : Load Balancer Detection
	WAF         : Web Application Firewall Detection
	WAAF        : Web Application Attack Functionality
	WIFI        : Wireless Attack Functionality
	HASH        : Password Cracking Functionality
	dbAttack    : MySQL Scanner
	phishing    : Tool that will combine Metasploit and Nmap without using Lua

	SIPVicious suite is a set of tools that can be used to audit SIP based VoIP systems. It currently consists of four tools:
	svmap       : this is a sip scanner. Lists SIP devices found on an IP range
	svwar       : identifies active extensions on a PBX
	svcrack     : an online password cracker for SIP PBX
	svreport    : manages sessions and exports reports to various formats
	svcrash     : attempts to stop unauthorized svwar and svcrack scans
	"""
		sys.exit(0)

	def menu(self):
		'''
		Main method. Displays menu and catches console arguments.
		'''
		print "\nPackage of Attack tools (v1.0)\nATTENTION!!! Be careful with using this tools\n"
		if len(sys.argv) < 2:
			self.usage()
		if sys.argv[1] == 'Recon':
			Recon(sys.argv[2:])
		elif sys.argv[1] == 'Dork':
			Dork(sys.argv[2:])
		elif sys.argv[1] == 'Dns':
			Dns(sys.argv[2:])
		elif sys.argv[1] == 'Admin':
			Dir_admin(sys.argv[2:])
		elif sys.argv[1] == 'LoadBal':
			Loadbal(sys.argv[2:])
		elif sys.argv[1] == 'WAF':
			WAF(sys.argv[2:])
		elif sys.argv[1] == 'WAAF':
			waff_instance = WAAF()
			if sys.argv[2:] == []:
				waff_instance.show_help()
			else:
				waff_instance.main(sys.argv[2:])
		elif sys.argv[1] == 'WIFI':
			wifi_instance = WIFI()
			if sys.argv[2:] == []:
				wifi_instance.help()
			else:
				wifi_instance.handle_args()
				wifi_instance.banner()
				wifi_instance.main()
		elif sys.argv[1] == "HASH":
			hash_instance = HASH()
			hash_instance.main(sys.argv[2:])
		elif sys.argv[1] == "dbAttack":
			dbattack_instance = DBATTACK()
			dbattack_instance.main(sys.argv[2:])
		elif sys.argv[1] == "phishing":
			phishing_instance = Phishing_Detector()
			phishing_instance.main(sys.argv[2:])
		elif sys.argv[1] == "svmap":
			svmap_instance = SVMAP()
			svmap_instance.main()
		elif sys.argv[1] == "svwar":
			svwar_instance = SVWAR()
			svwar_instance.main()
		elif sys.argv[1] == "svcrack":
			svcrack_instance = SVCRACK()
			svcrack_instance.main()
		elif sys.argv[1] == "svreport":
			svreport_instance = SVREPORT()
			svreport_instance.main()
		elif sys.argv[1] == "svcrash":
			svcrash_instance = SVCRASH()
			svcrash_instance.main()
		else:
			self.usage()

# main called here
# The main program. The following line is the entry point of this script.
if __name__ == "__main__":
	# We call an instance of the class ENGINE defined above
	child = ENGINE()
	# Create instance for main method
	child.menu()
