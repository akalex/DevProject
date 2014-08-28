import odesk
from pprint import pprint



def desktop_app():
    """Emulation of desktop app.
    Your keys should be created with project type "Desktop".

    Returns: ``odesk.Client`` instance ready to work.

    """
    print "Emulating desktop app"

    public_key = '<YOUR API PUBLICK KEY>'
    secret_key = '<YOUR API SECRET KEY>'
    access_token = '<YOUR API ACCESS TOKEN>'
    access_token_secret = '<YOUR API ACCESS SECRET TOKEN>'

    client = odesk.Client(public_key, secret_key)

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