#!/usr/bin/env python3.3
# -*- coding: utf-8 -*-

import sys

def main():

    def confirm_user_choice():
        """
        This is a function which verifies that еhe user has entered the correct options

        :return arg: string with user choice
        """

        # Catch an input from CLI
        arg = input("Please enter year (or q for quit): ")
        # If arg is empty, calls function once again, until arg will be empty.
        if arg != "":
            # Is there allowed options or not, calls function once again.
            if arg == 'q':
                print ("q has been caught. Exiting...")
                return arg
            # If everything is correct, function returns argument
            elif str(arg).isdigit() is True:
                return arg
            else:
                print ("You should enter only integer number of 'q'...")
                return confirm_user_choice()
        else:
            return confirm_user_choice()

    # Console colors
    BOLD = '\033[1m' # Bold
    END = '\033[0m' # Classical text
    # Print a welcome message
    print (BOLD + "Leap Year Tester!" + END)
    # Create and exception
    # This allow us to make sure that the inputted argument is digit
    year = ""
    while True:
        year = confirm_user_choice()
        # If year divisible by 4 and not divisible by 100 - LEAP YEAR
        # if year is divisible by 400 - LEAP YEAR
        # else not a LEAP YEAR
        if year == 'q':
            sys.exit()
        else:
            if ((int(year) % 4) == 0) and not ((int(year) % 100) == 0):
                print (BOLD + year + END, "is a leap year")
            elif ((int(year) % 400) == 0):
                print (BOLD + year + END, "is a leap year")
            else:
                print (BOLD + year + END, "is NOT a leap year")

# main called here
# The main program. The following line is the entry point of this script.
if __name__ == "__main__":
    # Call the main function without any parameters.
    main()