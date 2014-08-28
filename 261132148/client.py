import oauth2 as oauth
import urlparse
import os

BASE_URL = os.environ.get('PYTHON_ODESK_BASE_URL', 'https://www.odesk.com')
url = 'https://www.odesk.com/services/'
request_token_url = os.path.join(BASE_URL, 'api/auth/v1/oauth/token/request')
authorize_url = os.path.join(BASE_URL, 'services/api/auth')
access_token_url = os.path.join(BASE_URL, 'api/auth/v1/oauth/token/access')

consumer = oauth.Consumer(key='32740b9bb6385ef667c79530f854e7bc',
                          secret='2c3accb6b562e479')

client = oauth.Client(consumer)

response, content = client.request(request_token_url, 'POST')
print response, content
if response['status'] != '200':
    raise Exception('Invalid response: %s' % response['status'])

request_token = dict(urlparse.parse_qsl(content))

authorize_link = '%s?oauth_token=%s' % (authorize_url,
                                        request_token['oauth_token'])
print authorize_link
accepted = 'n'
while accepted.lower() == 'n':
    # you need to access the authorize_link via a browser,
    # and proceed to manually authorize the consumer
    accepted = raw_input('Have you authorized me? (y/n) ')

token = oauth.Token(request_token['oauth_token'],
                    request_token['oauth_token_secret'])


client = oauth.Client(consumer, token)
access_token_url='https://www.odesk.com/services/api/auth?oauth_token=00f2e7dc47c87fc34203a020a922be67&oauth_verifier=323f005c7909eb984725813e8c456c3f'
response, content = client.request(access_token_url, 'POST')
if response['status'] != '200':
    raise Exception('Invalid response: %s' % response['status'])

access_token = dict(urlparse.parse_qsl(content))

# this is the token you should save for future uses
token = oauth.Token(access_token['oauth_token'],
                    access_token['oauth_token_secret'])

#
# As an example, let's add a book to one of the user's shelves
#

#import urllib

#client = oauth.Client(consumer, token)
# the book is: "Generation A" by Douglas Coupland
#body = urllib.urlencode({'name': 'to-read', 'book_id': 6801825})
#headers = {'content-type': 'application/x-www-form-urlencoded'}
#response, content = client.request('%s/shelf/add_to_shelf.xml' % url,
#                                   'POST', body, headers)
# check that the new resource has been created
#if response['status'] != '201':
#    raise Exception('Cannot create resource: %s' % response['status'])
#else:
#    print 'Book added!'