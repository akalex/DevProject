#
# This file is part of fimap.
#

settings = {}

settings["dynamic_rfi"] = {}

settings["dynamic_rfi"]["mode"] = "off" # Set to "ftp" or "local" to use Dynamic_RFI. Set it to "off" to disable it and rely on settings["filesrmt"] files.

###############
#!!!# WARNING #
###################################################################################################
# If you use dynamic_rfi make sure that NO file will be interpreted in the directory you define!  #
# Else code (which should be interpreted on the victim server) will be executed on YOUR machine.  #
# If you don't understand what I say then DON'T USE dynamic_rfi!                                  #
###################################################################################################

# FTP Mode
settings["dynamic_rfi"]["ftp"] = {}
settings["dynamic_rfi"]["ftp"]["ftp_host"] = None
settings["dynamic_rfi"]["ftp"]["ftp_user"] = None
settings["dynamic_rfi"]["ftp"]["ftp_pass"] = None
settings["dynamic_rfi"]["ftp"]["ftp_path"] = None # A non existing file without suffix. Example: /home/imax/public_html/payload
settings["dynamic_rfi"]["ftp"]["http_map"] = None # The mapped HTTP path of the file. Example: http://localhost/~imax/payload

# Local Mode
settings["dynamic_rfi"]["local"] = {}
settings["dynamic_rfi"]["local"]["local_path"] = None   # A non existing file on your filesystem without prefix which is reachable by http. Example: /var/www/payload
settings["dynamic_rfi"]["local"]["http_map"]   = None   # The http url of the file without prefix where the file is reachable from the web. Example: http://localhost/payload


