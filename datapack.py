from src import cli
import sys, os

if __name__ == "__main__":
    args = sys.argv
    if args[0].split('.')[-1] in ('exe', 'py'):
        args = args[1:]
    cli.run(args)