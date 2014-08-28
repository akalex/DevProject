#!/usr/bin/env python
import sys

from vulndb import vulnDB, vulnDBInfo, vulnDBXML, vulnDBUpdate, vulnDBStats

'''
vulnDB - Open Source Cross-linked and Aggregated Local Vulnerability Database

'''

def get_help():
    info = vulnDBInfo()
    print ''
    print '-----------------------------------------------------------------------------'
    print info.get_version()['title']
    print '                                                          version ' + info.get_version()['build']
    print '                                         ' + info.get_owner()['website']
    print '-----------------------------------------------------------------------------'
    print ''
    print '[usage 1]: python' + str(sys.argv[0]) + ' <Method> <CVE>'
    print '[info] Available vulnDB methods:'
    print 'Information  ==> get_cve | get_cpe | get_cwe | get_capec | get_category | get_iavm'
    print 'References   ==> get_refs | get_scip | get_osvdb | get_certvn | get_bid'
    print 'Risk         ==> get_risk | get_cvss'
    print 'Patchs 1/2   ==> get_ms | get_kb | get_aixapar | get_redhat | get_suse | get_debian | get_hp'
    print 'Patchs 2/2   ==> get_mandriva | get_cisco | get_ubuntu | get_gentoo | get_fedora | get_vmware'
    print 'Assessment   ==> get_oval | get_nessus | get_openvas '
    print 'Defense      ==> get_snort | get_suricata'
    print 'Exploitation ==> get_milw0rm | get_edb | get_saint | get_msf'
    print ''
    print '----------'
    print '[usage 2]: python ' + str(sys.argv[0]) + ' export <CVE>'
    print '[info]: This method will export the CVE as vulnDB XML format'
    print ''
    print '----------'
    print '[usage 3]: python ' + str(sys.argv[0]) + ' stats or latest_cve'
    print '[info]: Available stats methods'
    print 'Global statistics   ==> stats'
    print 'Latest Added CVEs   ==> latest_cve '
    print ''
    print '----------'
    print '[Update]: python ' + str(sys.argv[0]) + ' update'
    print '[info]: This method will update the SQLite vulndb database to its latest release'
    exit(0)

def call_get_cve(vulndb):
    cveInfo = vulndb.get_cve()
    if cveInfo:
        print '[cve_description]:', cveInfo['summary']
        print '[cve_published]:', cveInfo['published']
        print '[cve_modified]:', cveInfo['modified']


def call_get_cvss(vulndb):
    cvssScore = vulndb.get_cvss()
    if cvssScore:
        print '[cvss_base]:', cvssScore['base']
        print '[cvss_impact]:', cvssScore['impact']
        print '[cvss_exploit]:', cvssScore['exploit']
        print '[AV (access vector)]:', cvssScore['access_vector']
        print '[AC (access complexity)]:', cvssScore['access_complexity']
        print '[Au (authentication)]:', cvssScore['authentication']    
        print '[C (confidentiality impact)]:', cvssScore['confidentiality_impact']     
        print '[I (integrity impact)]:', cvssScore['integrity_impact']     
        print '[A (availability impact)]:', cvssScore['availability_impact']

def call_get_refs(vulndb):

    cveRef = vulndb.get_refs()
    for i in range(0, len(cveRef)):
        print '[reference_id]:', cveRef[i]['id']
        print '[reference_link]', cveRef[i]['link']
    print ''
    print '[stats] %d Reference(s)' % len(cveRef)


def call_get_osvdb(vulndb):

    cveOSVDB = vulndb.get_osvdb()
    for i in range(0, len(cveOSVDB)):
        print '[osvdb_id]:', cveOSVDB[i]['id']
    print ''
    print '[stats] %d OSVDB id(s)' % len(cveOSVDB)


def call_get_scip(vulndb):

    cveSCIP = vulndb.get_scip()
    for i in range(0, len(cveSCIP)):
        print '[scip_id]:', cveSCIP[i]['id']
        print '[scip_link]', cveSCIP[i]['link']
    print ''
    print '[stats] %d Scip id(s)' % len(cveSCIP)

def call_get_bid(vulndb):

    cveBID = vulndb.get_bid()
    for i in range(0, len(cveBID)):
        print '[bid_id]:', cveBID[i]['id']
        print '[bid_link]', cveBID[i]['link']
    print ''
    print '[stats] %d BID id(s)' % len(cveBID)


def call_get_certvn(vulndb):

    cveCERTVN = vulndb.get_certvn()
    for i in range(0, len(cveCERTVN)):
        print '[certvn_id]:', cveCERTVN[i]['id']
        print '[certvn_link]', cveCERTVN[i]['link']
    print ''
    print '[stats] %d CERT-VN id(s)' % len(cveCERTVN)
    
def call_get_iavm(vulndb):

    cveIAVM = vulndb.get_iavm()
    for i in range(0, len(cveIAVM)):
        print '[iavm_title]', cveIAVM[i]['title']
        print '[iavm_id]:', cveIAVM[i]['id']
        print '[disa_key]:', cveIAVM[i]['key']
    print ''
    print '[stats] %d Iavm id(s)' % len(cveIAVM)


def call_get_cwe(vulndb):

    cveCWE = vulndb.get_cwe()
    for i in range(0, len(cveCWE)):
        print '[cwe_id]:', cveCWE[i]['id']
        print '[cwe_title]:', cveCWE[i]['title']
    print ''
    print '[stats] %d CWE id(s) ' % len(cveCWE)


def call_get_capec(vulndb):

    cveCAPEC = vulndb.get_capec()
    #get_cwe is invoked because CAPEC is related to CWE base
    cveCWE = vulndb.get_cwe()
    for i in range(len(cveCWE), len(cveCAPEC) + len(cveCWE)):
        print '[capec_id]: %s associated with %s ' %(cveCAPEC[i]['id'],cveCAPEC[i]['cwe'])
    print ''
    print '[stats] %d CAPEC id(s) ' % len(cveCAPEC)

def call_get_category(vulndb):

    cveCATEGORY = vulndb.get_category()
    #get_cwe is invoked because CAPEC is related to CWE base
    cveCWE = vulndb.get_cwe()
    for i in range(len(cveCWE), len(cveCATEGORY) + len(cveCWE)):
        print '[category] : %s --> %s ' %(cveCATEGORY[i]['id'],cveCATEGORY[i]['title'])
    print ''


def call_get_cpe(vulndb):

    cveCPE = vulndb.get_cpe()
    for i in range(0, len(cveCPE)):
        print '[cpe_id]:', cveCPE[i]['id']

    print ''
    print '[stats] %d CPE id(s)' % len(cveCPE)


def call_get_oval(vulndb):

    cveOVAL = vulndb.get_oval()
    for i in range(0, len(cveOVAL)):
        print '[oval_id]:', cveOVAL[i]['id']
        print '[oval_file]:', cveOVAL[i]['file']

    print ''
    print '[stats] %d OVAL Definition id(s)' % len(cveOVAL)

def call_get_snort(vulndb):

    cveSnort = vulndb.get_snort()
    for i in range(0, len(cveSnort)):
        print '[snort_id]:', cveSnort[i]['id']
        print '[snort_signature]:', cveSnort[i]['signature']
        print '[snort_classtype]:', cveSnort[i]['classtype']

    print ''
    print '[stats] %d Snort Rule(s)' % len(cveSnort)


def call_get_suricata(vulndb):

    cveSuricata = vulndb.get_suricata()
    for i in range(0, len(cveSuricata)):
        print '[suricata_id]:', cveSuricata[i]['id']
        print '[suricata_signature]:', cveSuricata[i]['signature']
        print '[suricata_classtype]:', cveSuricata[i]['classtype']

    print ''
    print '[stats] %d Suricata Rule(s)' % len(cveSuricata)


def call_get_nessus(vulndb):

    cveNessus = vulndb.get_nessus()
    for i in range(0, len(cveNessus)):
        print '[nessus_id]:', cveNessus[i]['id']
        print '[nessus_name]:', cveNessus[i]['name']
        print '[nessus_file]:', cveNessus[i]['file']
        print '[nessus_family]:', cveNessus[i]['family']

    print ''
    print '[stats] %d Nessus testing script(s)' % len(cveNessus)

def call_get_openvas(vulndb):
    
    cveOpenvas = vulndb.get_openvas()
    for i in range(0, len(cveOpenvas)):
        print '[openvas_id]:', cveOpenvas[i]['id']
        print '[openvas_name]:', cveOpenvas[i]['name']
        print '[openvas_file]:', cveOpenvas[i]['file']
        print '[openvas_family]:', cveOpenvas[i]['family']

    print ''
    print '[stats] %d OpenVAS testing script(s)' % len(cveOpenvas)
    
def call_get_edb(vulndb):

    cveEDB = vulndb.get_edb()
    for i in range(0, len(cveEDB)):
        print '[edb_id]:', cveEDB[i]['id']
        print '[edb_exploit]:', cveEDB[i]['file']

    print ''
    print '[stats] %d ExploitDB id(s)' % len(cveEDB)


def call_get_milw0rm(vulndb):

    cveMILW = vulndb.get_milw0rm()
    for i in range(0, len(cveMILW)):
        print '[milw0rm_id]:', cveMILW[i]['id']

    print ''
    print '[stats] %d Milw0rm id(s)' % len(cveMILW)

def call_get_saint(vulndb):

    cveSAINT = vulndb.get_saint()
    for i in range(0, len(cveSAINT)):
        print '[saintexploit_id]:', cveSAINT[i]['id']
        print '[saintexploit_title]:', cveSAINT[i]['title']
        print '[saintexploit_file]:', cveSAINT[i]['file']

    print ''
    print '[stats] %d SaintExploit id(s)' % len(cveSAINT)


def call_get_msf(vulndb):

    cveMSF = vulndb.get_msf()
    for i in range(0, len(cveMSF)):
        print '[msf_id]:', cveMSF[i]['id']
        print '[msf_title]:', cveMSF[i]['title']
        print '[msf_file]:', cveMSF[i]['file']

    print ''
    print '[stats] %d Metasploit Exploits/Plugins' % len(cveMSF)


def call_get_ms(vulndb):

    cveMS = vulndb.get_ms()
    for i in range(0, len(cveMS)):
        print '[Microsoft_ms_id]:', cveMS[i]['id']
        print '[Microsoft_ms_title]:', cveMS[i]['title']

    print ''
    print '[stats] %d Microsoft MS Patch(s)' % len(cveMS)


def call_get_kb(vulndb):

    cveKB = vulndb.get_kb()
    for i in range(0, len(cveKB)):
        print '[Microsoft_kb_id]:', cveKB[i]['id']
        print '[Microsoft_kb_id]:', cveKB[i]['title']  
    print ''
    print '[stats] %d Microsoft KB bulletin(s)' % len(cveKB)


def call_get_aixapar(vulndb):

    cveAIX = vulndb.get_aixapar()
    for i in range(0, len(cveAIX)):
        print '[IBM_AIXAPAR_id]:', cveAIX[i]['id']

    print ''
    print '[stats] %d IBM AIX APAR(s)' % len(cveAIX)


def call_get_redhat(vulndb):

    cveRHEL, cveBUGZILLA = vulndb.get_redhat()
    for i in range(0, len(cveRHEL)):
        print '[redhat_id]:', cveRHEL[i]['id']
        print '[redhat_patch_title]:', cveRHEL[i]['title']
        print '[redhat_oval_id]:', cveRHEL[i]['oval']

    print ''
    print '[stats] %d Redhat id(s)' % len(cveRHEL)
    print ''
    
    for i in range(0, len(cveBUGZILLA)):
        print '[redhat_bugzilla_issued]:', cveBUGZILLA[i]['date_issue']
        print '[redhat_bugzilla__id]:', cveBUGZILLA[i]['id']
        print '[redhat_bugzilla__title]:', cveBUGZILLA[i]['title']
    
    print ''
    print '[stats] %d Bugzilla id(s)' %len(cveBUGZILLA)


def call_get_suse(vulndb):

    cveSUSE = vulndb.get_suse()
    for i in range(0, len(cveSUSE)):
        print '[suse_id]:', cveSUSE[i]['id']

    print ''
    print '[stats] %d Suse id(s)' % len(cveSUSE)

def call_get_cisco(vulndb):

    cveCISCO = vulndb.get_cisco()
    for i in range(0, len(cveCISCO)):
        print '[cisco_id]:', cveCISCO[i]['id']

    print ''
    print '[stats] %d Cisco id(s)' % len(cveCISCO)

def call_get_ubuntu(vulndb):

    cveUBUNTU = vulndb.get_ubuntu()
    for i in range(0, len(cveUBUNTU)):
        print '[ubuntu_id]:', cveUBUNTU[i]['id']

    print ''
    print '[stats] %d Ubuntu id(s)' % len(cveUBUNTU)

def call_get_gentoo(vulndb):

    cveGENTOO = vulndb.get_gentoo()
    for i in range(0, len(cveGENTOO)):
        print '[gentoo_id]:', cveGENTOO[i]['id']

    print ''
    print '[stats] %d Gentoo id(s)' % len(cveGENTOO)

def call_get_fedora(vulndb):

    cveFEDORA = vulndb.get_fedora()
    for i in range(0, len(cveFEDORA)):
        print '[fedora_id]:', cveFEDORA[i]['id']

    print ''
    print '[stats] %d Fedora id(s)' % len(cveFEDORA)



def call_get_debian(vulndb):

    cveDEBIAN = vulndb.get_debian()
    for i in range(0, len(cveDEBIAN)):
        print '[debian_id]:', cveDEBIAN[i]['id']

    print ''
    print '[stats] %d Debian id(s)' % len(cveDEBIAN)


def call_get_mandriva(vulndb):

    cveMANDRIVA = vulndb.get_mandriva()
    for i in range(0, len(cveMANDRIVA)):
        print '[mandriva_id]:', cveMANDRIVA[i]['id']

    print ''
    print '[stats] %d Mandriva id(s)' % len(cveMANDRIVA)

def call_get_vmware(vulndb):

    cveVMWARE = vulndb.get_vmware()
    for i in range(0, len(cveVMWARE)):
        print '[vmware_id]:', cveVMWARE[i]['id']

    print ''
    print '[stats] %d VMware id(s)' % len(cveVMWARE)

def call_get_hp(vulndb):

    cveHP = vulndb.get_hp()
    for i in range(0, len(cveHP)):
        print '[hp_id]:', cveHP[i]['id']
        print '[hp_link]', cveHP[i]['link']
    print ''
    print '[stats] %d HP id(s)' % len(cveHP)
    
def call_get_risk(vulndb):

    cveRISK = vulndb.get_risk()
    cvssScore = vulndb.get_cvss()

    print 'Severity:', cveRISK['severitylevel']
    print 'Top vulnerablity:', cveRISK['topvulnerable']
    print '\t[cvss_base]:', cvssScore['base']
    print '\t[cvss_impact]:', cvssScore['impact']
    print '\t[cvss_exploit]:', cvssScore['exploit']
    print 'PCI compliance:', cveRISK['pciCompliance']
    print 'is Top alert:', cveRISK['topAlert']

def main():

    if len(sys.argv) == 3:
        myCVE = sys.argv[2]
        apiMethod = sys.argv[1]
        
        if apiMethod == "export":
            vulndb = vulnDBXML(myCVE)
            vulndb.export()
            exit(0)
    
        vulndb = vulnDB(myCVE)
        try:
            globals()['call_%s' % apiMethod](vulndb)
        except:
            print'[error] the method %s is not implemented' % apiMethod
        else:
            exit(0)
   
    elif len(sys.argv) == 2:
        apiMethod = sys.argv[1]
        if apiMethod == "update":
            db = vulnDBUpdate()
            db.update()
            exit(0)
        
        if apiMethod == "stats":
            stat = vulnDBStats()
            stat.stats()
            exit(0)           
            
        if apiMethod == "latest_cve":
            stat = vulnDBStats()
            stat.latest_cve()
            exit(0)    
            
        else:
           get_help()
    else:
        get_help() 

if __name__ == '__main__':
    main()
