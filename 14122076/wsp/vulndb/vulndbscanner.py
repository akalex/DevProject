#!/usr/bin/env python
# -*- coding: utf-8 -*-

from vulndb import vulnDB, vulnDBInfo, vulnDBXML


class VulnDB_Scan(object):
    '''
    vulndb.py -  Sample script to call methods from your programs

    '''

    def __init__(self, target):
	self.target = target

    def engine(self):
        print "vulnDB - open source cross-linked local vulnerability database"
        # create an instance of the class vulnDBInfo
        print '[instance] creating an instance with vulnDBApi.vulnDBInfo() '
        info = vulnDBInfo()

        print '[invoking] the get_version() method '
        print 'version: ', info.get_version()['build']

        print '[invoking] the get_owner() method '
        print 'author (if you want to get in touch and say hello):', info.get_owner()['author']

        print '[invoking] the get_config() method (note that the values are returned in dict. You can then read any key value you need ..'
        print 'vulnDB global config returned as dict:', info.get_config()['primary']

        # Invoking the vulnDB class

        cve = "cve-2013-3661"
        #cve = "cve-2014-0160"
        print '[setting] using cve ', cve

        # create an instance of the class vulnDB and pass the cve
        print '[instance] creating an instance with vulnDBApi.vulnDB(cve) '
        vulndb = vulnDB(cve)

        print '[invoking] the get_cve() method '
        # invoking the get_cve method
        cveInfo = vulndb.get_cve()

        if cveInfo:
            # returned data is a dictionary with 3 keys.
            print 'description: ', cveInfo['summary']
            print 'published date: ', cveInfo['published']
            print 'modified date: ', cveInfo['modified']

        # invoking the get_cvss method
        print '[invoking] the get_cvss() method '
        cvssScore = vulndb.get_cvss()

        if cvssScore:
            print 'base score:', cvssScore['base']
            print 'impact score:', cvssScore['impact']
            print 'exploit score:', cvssScore['exploit']
            print 'AV (access vector):', cvssScore['access_vector']
            print 'AC (access complexity):', cvssScore['access_complexity']
            print 'Au (authentication):', cvssScore['authentication']
            print 'C (confidentiality impact):', cvssScore['confidentiality_impact']
            print 'I (integrity impact):', cvssScore['integrity_impact']
            print 'A (availability impact):', cvssScore['availability_impact']

        # invoking the get_refs method (it's not longer get_refserences)
        print '[invoking] the get_refs() method '
        cverefs = vulndb.get_refs()
        for i in range(0, len(cverefs)):
            print 'refs id:', cverefs[i]['id']
            print 'refs link', cverefs[i]['link']
        print 'total found refs', len(cverefs)

        # invoking the get_cwe method
        print '[invoking] the get_cwe() method '
        cvecwe = vulndb.get_cwe()
        for i in range(0, len(cvecwe)):
            print 'cwe id:', cvecwe[i]['id']
            print 'cwe title:', cvecwe[i]['title']
        print 'total found cwe', len(cvecwe)

        ## invoking the get_capec method
        print '[invoking] the get_capec() method '
        cvecapec = vulndb.get_capec()
        cvecwe = vulndb.get_cwe()

        for i in range(len(cvecwe), len(cvecapec) + len(cvecwe)):
            print 'capec id %s associated with %s ' %(cvecapec[i]['id'],cvecapec[i]['cwe'])

        print 'total found capec', len(cvecapec)

        # invoking the get_category method
        print '[invoking] the get_category() method '
        cvecategory = vulndb.get_category()
        cvecwe = vulndb.get_cwe()

        for i in range(len(cvecwe), len(cvecategory) + len(cvecwe)):
            print '%s is listed in %s --> %s ' %(cve, cvecategory[i]['id'],cvecategory[i]['title'])

        print '[invoking] the get_cpe() method '
        cvecpe = vulndb.get_cpe()
        for i in range(0, len(cvecpe)):
            print 'cpe id:', cvecpe[i]['id']
        print 'total found cpe', len(cvecpe)

        print '[invoking] the get_debian() method '
        cveDEB = vulndb.get_debian()

        for i in range(0, len(cveDEB)):
            print 'debian id:', cveDEB[i]['id']
        print 'total found debian', len(cveDEB)

        print '[invoking] the get_oval() method '
        cveoval = vulndb.get_oval()
        for i in range(0, len(cveoval)):
            print 'oval id:', cveoval[i]['id']
            print 'oval file', cveoval[i]['file']
        print 'total found oval', len(cveoval)

        print '[invoking] the get_nessus() method '
        cvenessus = vulndb.get_nessus()

        for i in range(0, len(cvenessus)):
            print 'nessus id:', cvenessus[i]['id']
            print 'nessus name', cvenessus[i]['name']
            print 'nessus file', cvenessus[i]['file']
            print 'nessus family', cvenessus[i]['family']
        print 'total found nessus', len(cvenessus)

        print '[invoking] the get_edb() method '
        cveedb = vulndb.get_edb()

        for i in range(0, len(cveedb)):
            print 'edb id:', cveedb[i]['id']
            print 'edb file', cveedb[i]['file']
        print 'total found edb', len(cveedb)

        print '[invoking] the get_saint() method '
        cvesaintexp = vulndb.get_saint()
        for i in range(0, len(cvesaintexp)):
            print 'saint Exploit id:', cvesaintexp[i]['id']
            print 'saint Exploit Title:', cvesaintexp[i]['title']
            print 'saint Exploit File:', cvesaintexp[i]['file']
        print 'total found saint Exploit', len(cvesaintexp)

        print '[invoking] the get_msf() method '
        cvemsfexp = vulndb.get_msf()
        for i in range(0, len(cvemsfexp)):
            print 'msf Exploit id:', cvemsfexp[i]['id']
            print '\tmsf Exploit Title:', cvemsfexp[i]['title']
            print '\tmsf Exploit File:', cvemsfexp[i]['file']
        print 'total found msf Exploit', len(cvemsfexp)

        print '[Generating XML] Invoking the exportXML() method '
        print '[New Instance] Creating new instance with cve ', cve
        vulndb = vulnDBXML(cve, self.target)
        vulndb.export()


if __name__ == "__main__":
    child = VulnDB_Scan()
    child.engine()
