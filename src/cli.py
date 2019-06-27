import sys
import argparse
import os

from datapack import *


parser = argparse.ArgumentParser(prog="datapack")

subparser = parser.add_subparsers(title="commands", dest="cmd")

build_parser = subparser.add_parser(
    "build", help="build EasyFunction files into a datapack"
)
build_parser.add_argument(
    "-v", "--verbose", action="store_true", help="print out all generated commands."
)
build_parser.add_argument(
    "-n",
    "--nofiles",
    action="store_true",
    help="don't actually generate any files, just print out the generated commands.",
)
build_parser.add_argument(
    "-o",
    "--output",
    default=None,
    nargs=1,
    action="store",
    help="the output directory, defaults to the name of the first file provided",
)
build_parser.add_argument("files", nargs="+")

link_parser = subparser.add_parser(
    "link", help="link a datapack directory into a minecraft world for easy development"
)
link_parser.add_argument("dir", help="the directory to link into a minecraft world")
link_parser.add_argument(
    "save", help="the **directory name** of the save to link your datapack into"
)


def run(args):
    args = parser.parse_args(args)

    if args.cmd == "build":
        success = False
        try:
            outdir = args.output[0] if args.output else args.files[0]
            outdir = os.path.realpath(os.path.splitext(outdir)[0])
            success = compile(outdir, args.files, args.verbose, args.nofiles)
        except CompilationError as e:
            print(e)
            sys.exit()

        if success:
            print(f'successfully created datapack {os.path.basename(outdir)!r}')
    else:
        print("A command is required", file=sys.stderr)
        parser.print_help(sys.stderr)
        sys.exit(1)
