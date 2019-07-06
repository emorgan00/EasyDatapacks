from reader import *

# this should accept a command as a string, and return a string detailing the issue
# if <command> is not a valid vanilla minecraft command. None otherwise.
def check(command):
    
    # note: this is a temporary version.

    tokens = broad_tokenize(command)
    if len(tokens) == 0:
        return 'The command is empty.'

    # post-process flag, ignore it.
    if command[0] == '!':
        return None

    return None