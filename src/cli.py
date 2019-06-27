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

    elif args.cmd == "link":
        mcdir = os.getenv("MINECRAFT_DIR")
        if mcdir is not None:
            pass  # we found it already
        elif sys.platform.startswith("linux"):
            mcdir = os.path.expanduser("~/.minecraft")
        elif sys.platform.startswith("win32"):
            mcdir = os.path.expandvars("%APPDATA%/.minecraft")
        elif sys.platform.startswith("darwin"):
            mcdir = os.path.expanduser("~/Library/Application Support/minecraft")
        else:
            print(
                "Unsupported OS for automatically finding the .minecraft directory, "
                "please set the $MINECRAFT_DIR environment variable to its location"
            )
            sys.exit(1)
        args.dir = os.path.realpath(args.dir)
        datapackdir = os.path.join(
            mcdir, "saves", args.save, "datapacks", os.path.basename(args.dir)
        )
        os.symlink(args.dir, datapackdir, target_is_directory=True)
        print(f"successfully symlinked {args.dir!r} to {datapackdir!r}")

    else:
        print("A command is required", file=sys.stderr)
        parser.print_help(sys.stderr)
        sys.exit(1)
