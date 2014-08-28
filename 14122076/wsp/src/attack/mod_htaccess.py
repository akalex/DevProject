from attack import Attack
from vulnerability import Vulnerability
from vulnerabilitiesdescriptions import VulnerabilitiesDescriptions as VulDescrip

# WSP 1.0 - A web application vulnerability scanner
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 1 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


class mod_htaccess(Attack):
    """
    This class implements a htaccess attack
    """

    name = "htaccess"

    doGET = False
    doPOST = False

    def __init__(self, HTTP, xmlRepGenerator):
        Attack.__init__(self, HTTP, xmlRepGenerator)

    #this function return code signification when htaccess protection enabled
    def __returnErrorByCode(self, code):
        err = ""
        if code == "401":
            err = "Authorization Required"
        elif code == "402":
            err = "Payment Required"
        elif code == "403":
            err = "Forbidden"
        else:
            err = "ok"
        return err


    def attackGET(self, page, dict, headers={}):
        err = ""
        url = page
        err500 = 0
        if url not in self.attackedGET:
            #print the url if verbose equal 2
            if self.verbose == 2:
                print "+ " + url

            err1 = self.__returnErrorByCode(headers["status"])

            if err1 != "ok":
                data1 = self.HTTP.send(url).getPage()
                #htaccess protection detected
                if self.verbose >= 1:
                    print _("HtAccess protection found:"), url

                data2, code2 = self.HTTP.send(url, method="ABC").getPageCode()
                err2 = self.__returnErrorByCode(code2)

                if err2 == "ok":
                    #htaccess bypass success

                    #print output informations by verbosity option
                    if self.verbose >= 1:
                        if self.color == 1:
                            print self.CYAN + "|HTTP Code : ", headers["status"], ":", err1 + self.STD
                        else:
                            print "|HTTP Code : ", headers["status"], ":", err1

                    if self.verbose == 2:
                        if self.color == 1:
                            print self.YELLOW + _("Source code:") + self.STD
                            print self.GB + data1 + self.STD
                        else:
                            print _("Source code:")
                            print data1

                    #report xml generator (ROMULUS) not implemented for htaccess
                    self.reportGen.logVulnerability(Vulnerability.HTACCESS, Vulnerability.HIGH_LEVEL_VULNERABILITY, \
                                                    url, "", err + " HtAccess")
                    if self.color == 1:
                        print self.RED + "  " + _(".htaccess bypass vulnerability:"), url + self.STD
                    else:
                        print "  " + _(".htaccess bypass vulnerability:"), url

                    #print output informations by verbosity option
                    if self.verbose >= 1:
                        if self.color == 1:
                            print self.CYAN + "|HTTP Code : ", code2 + self.STD
                        else:
                            print "|HTTP Code : ", code2

                    if self.verbose == 2:
                        if self.color == 1:
                            print self.YELLOW + _("Source code:") + self.STD
                            print self.GB + data2 + self.STD
                        else:
                            print _("Source code:")
                            print data2

                else:
                    if code1 == 500 and err500 == 0:
                        err500 = 1
                        self.reportGen.logVulnerability(Vulnerability.HTACCESS, Vulnerability.HIGH_LEVEL_VULNERABILITY, \
                                                        url, "",
                                                        VulDescrip.ERROR_500 + "\n" + VulDescrip.ERROR_500_DESCRIPTION)
                        print _("500 HTTP Error code with")
                        print "  " + _("Evil url") + ":", url

                        #add the url with the url attacked
                self.attackedGET.append(url)

