#!/usr/bin/env python3.3
# -*- coding: utf-8 -*-

# Module Generate pseudo-random numbers
from random import choice

def main():

    def confirm_user_choice():
        """
        This is a function which verifies that еhe user has entered the correct options

        :return arg: string with user choice
        """
        # List of correct options
        correct_value = ['r', 'p', 's']
        # Catch an input from CLI
        arg = input("Choose (R)ock, (P)aper or (S)cissors: ")
        # If arg is empty, calls function once again, until arg will be empty.
        if arg != "":
            # Is there allowed options or not, calls function once again.
            if arg.lower() not in correct_value:
                print ("Only (R)ock, (P)aper or (S)cissors!!!")
                return confirm_user_choice()
            # If everything is correct, function returns argument
            else:
                return arg.upper()
        else:
            return confirm_user_choice()

    # Console colors
    BOLD = '\033[1m' # Bold
    END = '\033[0m' # Classical text
    W  = '\033[0m'  # white (normal)
    R  = '\033[31m' # red
    G  = '\033[32m' # green
    O  = '\033[33m' # orange
    B  = '\033[34m' # blue
    P  = '\033[35m' # purple
    C  = '\033[36m' # cyan
    GR = '\033[37m' # gray
    # Print a welcome message
    print (BOLD+"Welcome to Rock, Paper, Scissors!"+END)
    # Create a dictionary with correct order. This allow us to make the right choice
    variants = {'R': 'S', 'P': 'R', 'S': 'P'}
    # Counter of wins
    total_user_wins = 0
    total_comp_wins = 0
    # Game counter
    total_games = 0
    # We will play three games. Number can be changed, as you wish.
    while total_games < 3:
        # Call the function confirm_user_choice(), it returns us a user choice
        user_choise = confirm_user_choice()
        # Generate pseudo-random choice for computer. Available parameters take from our dictionary of variants
        comp_choise = choice(list(variants.keys()))
        print ("---------------------------------------")
        print ("User's choise:", user_choise)
        print ("Computer's choise:", comp_choise)
        # Comparing our choices. If they similar - it's a DRAW
        if (user_choise).upper() == (comp_choise).upper():
            print (O+"It's a Draw!"+W)
        # Getting a value from dictionary for user choice, if they are similar - User won this round
        elif variants.get((user_choise).upper()) == (comp_choise).upper():
            # Increase counter by one
            total_user_wins += 1
            print (G+"User wins!"+W)
        # Otherwise - Computer won this round
        else:
            # Increase counter by one
            total_comp_wins += 1
            print (R+"Computer wins!"+W)
        print ("---------------------------------------")
        # Increase counter by one
        total_games += 1

    # Check who won by the total scores
    print ("Total user's score: %s" % total_user_wins)
    print ("Total computer score: %s" % total_comp_wins)
    if total_user_wins > total_comp_wins:
        print (G+"Congratulations!!! You won by the total score!"+W)
    elif total_user_wins < total_comp_wins:
        print (R+"Unfortunately!!! Computer won by the total score!"+W)
    else:
        print (G+"Seems we have a draw!"+W)

# main called here
# The main program. The following line is the entry point of this script.
if __name__ == "__main__":
    # Call the main function without any parameters.
    main()
