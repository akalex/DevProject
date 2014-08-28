import odesk
from pprint import pprint
import mechanize
import cookielib
from BeautifulSoup import BeautifulSoup
import re


def auth(link):
    """
    Emulating authentication via oDesk
    :param link: string that contains verification URL
    """

    # Browser
    br = mechanize.Browser()

    # Cookie Jar
    cj = cookielib.LWPCookieJar()
    br.set_cookiejar(cj)

    # Browser options
    br.set_handle_equiv(True)
    #br.set_handle_gzip(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)

    # Follows refresh 0 but not hangs on refresh > 0
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

    # User-Agent (this is cheating, ok?)
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

    # Open odesk site
    r = br.open(link)
    form = br.forms().next()  # the login form is unnamed...
    print "Make authorization in oDesk..."
    print form.action
    # Authentication data
    form['username'] = 'ak_alex'
    form['password'] = '[a|k]alex~'
    br.form = form
    br.submit()
    print "Success!!!"
    # Create url object
    home_page = br.geturl()
    # Get page with verification code (html code).
    r2 = br.open(home_page)
    # Read out page
    html_page = r2.read()
    # Running our document through Beautiful Soup
    soup = BeautifulSoup(html_page)
    # Looking for div with class oNote
    beautiful_result = soup.findAll('div', attrs={'class': 'oNote'})
    # Searching pattern that contains verification token
    pattern_match = re.search("Your oauth_verifier=(\w+)", str(beautiful_result))
    token = pattern_match.group(1)
    # Return verification token
    return token


def desktop_app():
    """Emulation of desktop app.
    Your keys should be created with project type "Desktop".

    Returns: ``odesk.Client`` instance ready to work.

    """
    print "Emulating desktop app"

    #public_key = raw_input('Please enter public key: > ')
    #secret_key = raw_input('Please enter secret key: > ')
    public_key = '32740b9bb6385ef667c79530f854e7bc'
    secret_key = '2c3accb6b562e479'

    client = odesk.Client(public_key, secret_key)
    confirm_code = auth(client.auth.get_authorize_url())
    verifier = confirm_code
    #verifier = raw_input(
    #    'Please enter the verification code you get '
    #    'following this link:\n{0}\n\n> '.format(
    #        client.auth.get_authorize_url()))


    print 'Retrieving keys.... '
    access_token, access_token_secret = client.auth.get_access_token(verifier)
    print access_token, access_token_secret
    print 'OK'

    # For further use you can store ``access_toket`` and
    # ``access_token_secret`` somewhere
    client = odesk.Client(public_key, secret_key,
                          oauth_access_token=access_token,
                          oauth_access_token_secret=access_token_secret)
    return client


if __name__ == '__main__':
    client = desktop_app()

    try:
        print "My info"
        pprint(client.auth.get_info())
        print "Team rooms:"
        pprint(client.team.get_teamrooms())
        #HRv2 API
        print "HR: companies"
        pprint(client.hr.get_companies())
        print "HR: teams"
        pprint(client.hr.get_teams())
        print "HR: userroles"
        pprint(client.hr.get_user_roles())
        print "Get jobs"
        pprint(client.provider.search_jobs({'q': 'python'}))
    except Exception, e:
        print "Exception at %s %s" % (client.last_method, client.last_url)
        raise e