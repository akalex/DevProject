#import urllib2
#import urllib
#import cookielib
#import oauth2 as oauth
#import mechanize,cookielib
# Browser
#br = mechanize.Browser()

# Cookie Jar
#cj = cookielib.LWPCookieJar()
#br.set_cookiejar(cj)

# Browser options
#br.set_handle_equiv(True)
#br.set_handle_gzip(True)
#br.set_handle_redirect(True)
#br.set_handle_referer(True)
#br.set_handle_robots(False)

# Follows refresh 0 but not hangs on refresh > 0
#br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

# Want debugging messages?
#br.set_debug_http(True)
#br.set_debug_redirects(True)
#br.set_debug_responses(True)

# User-Agent (this is cheating, ok?)
#br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

# Open odesk site
#r = br.open('https://www.odesk.com/login.php')
#form = br.forms().next()  # the login form is unnamed...
#print form.action
#form['username'] = 'ak_alex'
#form['password'] = '[a|k]alex~'
#br.form = form
#br.submit()

#print br.geturl()
#your form data goes here

import os
import time
import urlparse
import urllib, urllib2
import oauth2 as oauth
import logging
import cookielib
import json
import mechanize
import collections
import requests

BASE_URL = os.environ.get('PYTHON_ODESK_BASE_URL', 'https://www.odesk.com')

key = '32740b9bb6385ef667c79530f854e7bc'
secret = '2c3accb6b562e479'
request_token_url = os.path.join(BASE_URL, 'api/auth/v1/oauth/token/request')
authorize_url = os.path.join(BASE_URL, 'services/api/auth')
access_token_url = os.path.join(BASE_URL, 'api/auth/v1/oauth/token/access')

def get_oauth_consumer():
    """
    Returns OAuth consumer object.
    """
    return oauth.Consumer(key, secret)

def get_request_token():
    """
    Returns request token and request token secret.
    """

    client = oauth.Client(get_oauth_consumer())
    response, content = client.request(request_token_url, 'POST')
    if response.get('status') != '200':
        raise Exception(
            "Invalid request token response: {0}.".format(content))
    request_token = dict(urlparse.parse_qsl(content))
    request_token1 = request_token.get('oauth_token')
    request_token_secret = request_token.get('oauth_token_secret')
    print "=========================================="
    print request_token1, request_token_secret
    print "=========================================="
    return request_token1, request_token_secret

def get_authorize_url(callback_url=None):
    """
    Returns authentication URL to be used in a browser.
    """
    oauth_token  = get_request_token()[0]

    if callback_url:
        params = urllib.urlencode({'oauth_token': oauth_token, 'oauth_callback': callback_url})
    else:
        params = urllib.urlencode({'oauth_token': oauth_token})
    return '{0}?{1}'.format(authorize_url, params)


def get_access_token(verifier):
    """
    Returns access token and access token secret.
    """

    try:
        #request_token = self.request_token
        #request_token_secret = self.request_token_secret
        request_token, request_token_secret = get_request_token()
    except AttributeError, e:
        logger = logging.getLogger('python-odesk')
        logger.debug(e)
        raise Exception("At first you need to call get_authorize_url")
    token = oauth.Token(request_token, request_token_secret)
    token.set_verifier(verifier)
    client = oauth.Client(get_oauth_consumer(), token)
    response, content = client.request(access_token_url, 'POST')
    if response.get('status') != '200':
        raise Exception(
            "Invalid access token response: {0}.".format(content))
    access_token = dict(urlparse.parse_qsl(content))
    access_token1 = access_token.get('oauth_token')
    access_token_secret1 = access_token.get('oauth_token_secret')
    #return access_token1, access_token_secret1
    #print access_token1, access_token_secret1

def create_auth_header(parameters):
    """For all collected parameters, order them and create auth header"""
    ordered_parameters = {}
    ordered_parameters = collections.OrderedDict(sorted(parameters.items()))
    auth_header = (
        '%s="%s"' % (k, v) for k, v in ordered_parameters.iteritems())
    val = "OAuth " + ', '.join(auth_header)
    return val

def main(method='GET', to_header=False, to_dict=False):
    url = get_authorize_url()
    #print "Go to the following link in your browser:"
    #print url
    #print
    #url = 'https://www.odesk.com/login.php'
    data = {}
    token = oauth.Token(key, secret)
    consumer = get_oauth_consumer()

    data.update({
        'oauth_token': '00f2e7dc47c87fc34203a020a922be67',
        'oauth_consumer_key': consumer.key,
        'oauth_version': '1.0',
        'oauth_nonce': oauth.generate_nonce(),
        'oauth_timestamp': int(time.time()),
        'oauth_verifier': '323f005c7909eb984725813e8c456c3f',
        })
    request = oauth.Request(method=method, url=request_token_url, parameters=data)
    signature_method = oauth.SignatureMethod_HMAC_SHA1()
    request.sign_request(signature_method, consumer, token)
    print request.to_postdata()


    test="https://www.odesk.com/services/api/auth?oauth_token=00f2e7dc47c87fc34203a020a922be67&oauth_verifier=323f005c7909eb984725813e8c456c3f"

    #if to_header:
    #    return request.to_header()
    Y = request.to_header()
    #print Y

    X = request.to_postdata()
    # convert string to dict
    #body = dict([x.split('=') for x in X.split('&')])
    #print body

    #print X
    #url = 'https://www.odesk.com/services/api/auth?oauth_token=856a6f2aa80aa2075106c88086178c49'

    #print url

    #client = oauth.Client(consumer, token)
    #r, c = client.request('{0}?{1}'.format(authorize_url, token.key), 'POST', X)
    #print r, c

    #header = {'Authorization': create_auth_header(body)}
    #r = requests.get(url, headers=header)
    #print r.text


    #access_token1, access_token_secret1 = get_access_token()
    #print access_token1, access_token_secret1
    #url = 'https://www.odesk.com/login?redir=%2Fservices%2Fapi%2Fauth%3Foauth_token%3D32740b9bb6385ef667c79530f854e7bc'

    #header = urllib.urlencode(Y)
    #url = "https://www.odesk.com/services/api/auth?oauth_token=00f2e7dc47c87fc34203a020a922be67&oauth_verifier=323f005c7909eb984725813e8c456c3f"
    #request = urllib2.Request(url)
    #request.add_header("", urllib.urlencode(Y))
    #opener = urllib2.build_opener(urllib2.HTTPSHandler(debuglevel = 1))
    #opener.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    #request = opener.open(request)
    #result = request.read()
    #request.close()

    #cj = cookielib.CookieJar()
    #opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    #urllib2.install_opener(opener)
    #opener.addheaders = header
    #req=opener.open(url, urllib.urlencode(Y))
    #result = req.read()

    #print result



main()

