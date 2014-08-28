#!/usr/bin/python
# -*- coding: utf-8 -*-


__author__ = 'aomyshev'


import re, urllib, urllib2
import csv
import getpass


class excel_semicolon(csv.excel):
    delimiter = ';'


class Spreadsheet(object):

    def __init__(self, key):
	super(Spreadsheet, self).__init__()
	self.key = key

class Client(object):
    
    def __init__(self, email, password):
	super(Client, self).__init__()
	self.email = email
	self.password = password

    def _get_auth_token(self, email, password, source, service):
	url = "https://www.google.com/accounts/ClientLogin"
	params = {
		"Email": email, "Passwd": password,
		"service": service,
		"accountType": "HOSTED_OR_GOOGLE",
		"source": source
	}
	req = urllib2.Request(url, urllib.urlencode(params))
	return re.findall(r"Auth=(.*)", urllib2.urlopen(req).read())[0]

    def get_auth_token(self):
	source = type(self).__name__
	return self._get_auth_token(self.email, self.password, source, service="wise")

    def download(self, spreadsheet, gid=0, format="csv"):
	url_format = ""
	if gid == 0:
	    url_format = "https://spreadsheets.google.com/feeds/download/spreadsheets/Export?key=%s&exportFormat=%s"
	else:
	    url_format = "https://spreadsheets.google.com/feeds/download/spreadsheets/Export?key=%s&exportFormat=%s&gid=%i"
	headers = {
		"Authorization": "GoogleLogin auth=" + self.get_auth_token(),
		"GData-Version": "3.0"
	}
	req = ""
	if gid == 0:
    	    req = urllib2.Request(url_format % (spreadsheet.key, format), headers=headers)
	else:
	    req = urllib2.Request(url_format % (spreadsheet.key, format, gid), headers=headers)
	return urllib2.urlopen(req)


if __name__ == "__main__":

    def ask_question(question):
	answer = raw_input(question)
	return answer

    def parse_input():
	resourse = ""
	while resourse == "":
	    resourse = ask_question("{0}".format("Please enter URL or document ID: "))
	if re.search("https://", resourse):
	    from urlparse import urlparse
	    url_parse = urlparse(resourse)
	    return re.search("(^key%3D|^key=)(.*)[\%26|\&]", url_parse.query).group(2), re.search("(^gid=|^gid%3D)(\d+)", url_parse.fragment).group(2)
	else:	
	    return resourse, 0

    def get_email():
	email = ""
	while email == "":
	    email = ask_question("{0}".format("Email: "))
	return email

    def get_pass():
	password = ""
	while password == "":
	    password = getpass.getpass()
	return password
	
    #email = "" # (your email here)
    #password = "" # (your password here)
    email = get_email()
    password = get_pass() # (get password for email)
    spreadsheet_id, gid = parse_input() # (get URL or resourse ID)
    print "Downloading resourse with key={0} and gid={1}".format(spreadsheet_id, gid)

    # Create client and spreadsheet objects
    gs = Client(email, password)
    ss = Spreadsheet(spreadsheet_id)

    # Request a file-like object containing the spreadsheet's contents
    csv_file = gs.download(ss, int(gid))
		
    # Where to write data
    output_file = "{0}.csv".format(spreadsheet_id)
	
    # Parse as CSV and print the rows
    with open(output_file, 'wb') as filename:
        writer = csv.writer(filename, dialect=excel_semicolon)
        for row in csv.reader(csv_file):
            writer.writerow(row)
