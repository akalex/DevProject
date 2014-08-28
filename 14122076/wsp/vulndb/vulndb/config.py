'''
vulnDB Framework - The Open Source Cross Linked Local Vulnerability Database

Name : config.py -  Configuration File
Purpose : Configuration File. Handles global variables and database URLs.
'''

author = {
    '__name__': 'Strategic Security',
    '__email__': 'hacker@strategicsecurity.com',
    '__website__': '',
}


product = {
    '__title__': 'vulnDB - Open Source Cross-linked and Aggregated Local Vulnerability Database',
    '__website__': '',
    '__mainRepository__': '',
    '__build__': '1.0',
}


database = {
    'default': 'primary',
    'vulndb_db': 'vulndb.db',

    'primary': {
        'description': 'primary repository',
        'url': '',
        'vulndb_db': 'vulndb.db',
        'vulndb_db_compressed': 'vulndb.db.tgz',
        'updateStatus': 'update.dat',
    },

}

gbVariables = {
    'cve_url': 'http://cve.mitre.org/cgi-bin/cvename.cgi?name=',
    'bid_url': 'http://www.securityfocus.com/bid/',
    'certvn_url':'http://www.kb.cert.org/vuls/id/',
    'edb_url': 'http://www.exploit-db.com/exploits/',
    'oval_url': 'http://oval.mitre.org/repository/data/getDef?id=',
    'redhat_oval_url': 'https://www.redhat.com/security/data/oval/com.redhat.rhsa-',
    'cwe_url' : 'http://cwe.mitre.org/data/definitions/',
    'capec_url' : 'http://capec.mitre.org/data/definitions/',
    'scip_url'  : 'http://www.scip.ch/?vuldb',
    'osvdb_url'  : 'http://www.osvdb.org/show/osvdb/',
    'milw0rm_url' : 'http://www.milw0rm.com/exploits/',
    'ms_bulletin_url' : 'http://technet.microsoft.com/en-us/security/bulletin/',    
    'ms_kb_url' : 'http://support.microsoft.com/default.aspx?scid=kb;en-us;',
}
