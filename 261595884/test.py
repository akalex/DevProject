#!/usr/bin/python
#
#import gdata.webmastertools.service
#import gdata.service
#try:
#  from xml.etree import ElementTree
#except ImportError:
#  from elementtree import ElementTree
#import atom
#import getpass

#username = 'a.omyshev@gmail.com'
#password = '[a|k]alex~'
#site_uri = ''

#username = raw_input('Please enter your username: ')
#password = getpass.getpass()
#site_uri = raw_input('Please enter your site url: ')

#client = gdata.webmastertools.service.GWebmasterToolsService(
#    email=username,
#    password=password, source='PythonWebmasterToolsSample-1')

#print 'Logging in'
#client.ProgrammaticLogin()
#client.ClientLogin(username, password)

#print 'Retrieving Sitemaps feed'
#site_uri = 'https://www.google.com/webmasters/tools/feeds/http%3A%2F%2Fwww.criminology.com%2F/sitemaps/http%3A%2F%2Fwww.criminology.com%2Fsitemap.xml'
#feed = client.GetSitemapsFeed(site_uri)
#print type(feed)

# Format the feed
#print
#print 'You have %d sitemap(s), last updated at %s' % (len(feed.entry), feed.updated.text)
#print
#print '='*80

#def safeElementText(element):
#  if hasattr(element, 'text'):
#     return element.text
#  return ''

# Format each site
#for entry in feed.entry:
#    print entry
#    print entry.title.text.replace('http://', '')[:80]
#    print "  Last Updated   : %29s              Status: %10s" % (
#        entry.updated.text[:29], entry.sitemap_status.text[:10])
#    print "  Last Downloaded: %29s           URL Count: %10s" % (
#        safeElementText(entry.sitemap_last_downloaded)[:29],
#        safeElementText(entry.sitemap_url_count)[:10])
#print


#### SELENIUM ####
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import os

fp = webdriver.FirefoxProfile()
fp.set_preference("browser.download.folderList", 2)
fp.set_preference("browser.download.dir", os.getcwd())
fp.set_preference("browser.download.downloadDir", os.getcwd())
fp.set_preference("browser.download.lastDir", os.getcwd())
fp.set_preference("browser.download.manager.showWhenStarting", False)
fp.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv")

driver= webdriver.Firefox(firefox_profile=fp)
#driver = webdriver.Firefox()
driver.get("https://www.google.com/webmasters/tools/sitemap-list?hl=en&siteUrl=http://www.criminology.com/")


emailid=driver.find_element_by_id("Email")
emailid.send_keys("a.omyshev@gmail.com")

passw=driver.find_element_by_id("Passwd")
passw.send_keys("[a|k]alex~")

signin=driver.find_element_by_id("signIn")
signin.click()

#driver.get("https://www.google.com/webmasters/tools/sitemap-list?hl=en&siteUrl=http://www.criminology.com/")
time.sleep(10)
button = driver.find_element_by_id("gwt-uid-163")
button.click()
button_ok = driver.find_element_by_css_selector("button[class='GOJ0WDDBBU GOJ0WDDBMU']")
button_ok.click()
driver.quit()


### Mechanize

#!/usr/bin/env python

#import mechanize

#cj = mechanize.LWPCookieJar()
#cj.load("cookies.txt")

#br = mechanize.Browser()
#br.set_cookiejar(cj)
#br.set_handle_redirect(True)
#br.set_handle_referer(True)
#br.set_handle_robots(False)
#br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
#br.addheaders = [('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.810.0 Safari/535.1 cd34/0.9b')]
#br.open('https://www.google.com/accounts/ServiceLogin?service=oz&passive=1209600&continue=https://www.google.com/webmasters/tools/sitemap-list?hl=en&siteUrl=http://www.criminology.com/')

#br.select_form(nr=0)

#br.form.find_control("Email").readonly = False
#br.form['Email'] = 'a.omyshev@gmail.com'
#br.form['Passwd'] = '[a|k]alex~'

#br.submit()

#for l in br.links():
#    print l

#cj.save("cookies.txt")

