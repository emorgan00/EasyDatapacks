import sys
import cli
import os

if __name__ == "__main__":
    args = sys.argv
    if len(args) > 0 and args[0] == __file__ or args[0] == os.path.dirname(__file__):
        args = args[1:]
    cli.run(args)
