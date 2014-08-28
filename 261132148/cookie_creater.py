#!/usr/bin/env python2.7
# the path and filename that you want to use to save your cookies in
COOKIEFILE = 'cookies.txt'
import os.path

cj = None
ClientCookie = None
cookielib = None

# Let's see if cookielib is available
try:
    import cookielib
except ImportError:
    pass
else:
    import urllib2, urllib
    urlopen = urllib2.urlopen
    # This is a subclass of FileCookieJar that has useful load and save methods
    cj = cookielib.LWPCookieJar()
    Request = urllib2.Request

# If importing cookielib fails let's try ClientCookie
if not cookielib:
    try:
        import ClientCookie
    except ImportError:
        import urllib2
        urlopen = urllib2.urlopen
        Request = urllib2.Request
    else:
        urlopen = ClientCookie.urlopen
        cj = ClientCookie.LWPCookieJar()
        Request = ClientCookie.Request

####################################################
# We've now imported the relevant library - whichever library is being used urlopen is bound to the right function for retrieving URLs
# Request is bound to the right function for creating Request objects
# Let's load the cookies, if they exist. 


# now we have to install our CookieJar so that it is used as the default CookieProcessor in the default opener handler
if cj != None:
    if os.path.isfile(COOKIEFILE):
        cj.load(COOKIEFILE)
    if cookielib:
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        urllib2.install_opener(opener)
    else:
        opener = ClientCookie.build_opener(ClientCookie.HTTPCookieProcessor(cj))
        ClientCookie.install_opener(opener)

# If one of the cookie libraries is available, any call to urlopen will handle cookies using the CookieJar instance we've created
# (Note that if we are using ClientCookie we haven't explicitly imported urllib2)
# as an example :

# an example url that sets a cookie, try different urls here and see the cookie collection you can make !
theurl = 'https://www.odesk.com/login'
body = {'username':'ak_alex', 'password':'[a|k]alex~'}
# if we were making a POST type request, we could encode a dictionary of values here - using urllib.urlencode
txdata = urllib.urlencode(body)
# fake a user agent, some websites (like google) don't like automated exploration
txheaders =  {'User-agent' : 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.0.6)'}

try:
    # create a request object
    req = Request(theurl, txdata, txheaders)
    # and open it to return a handle on the url
    handle = urlopen(req)
except IOError, e:
    print 'We failed to open "%s".' % theurl
    if hasattr(e, 'code'):
        print 'We failed with error code - %s.' % e.code
    else:
        print 'Here are the headers of the page :'
        # handle.read() returns the page, handle.geturl() returns the true url of the page fetched (in case urlopen has followed any redirects, which it sometimes does)
        print handle.info()

print
if cj == None:
    print "We don't have a cookie library available - sorry."
    print "I can't show you any cookies."
else:
    print 'These are the cookies we have received so far :'
    for index, cookie in enumerate(cj):
        print index, '  :  ', cookie
        # save the cookies again
        cj.save(COOKIEFILE)
