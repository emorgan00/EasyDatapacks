from setuptools import setup
import sys, os

try:
    import py2exe
except ImportError:
    pass


egg_dist = "bdist_egg" in sys.argv
if egg_dist:
    main_file = os.path.realpath(os.path.join(__file__, "../__main__.py"))
    with open(main_file, "w") as f:
        f.write(
            """
from datapack.cli import run;
if __name__ == "__main__":
    run()
"""
        )

setup(
    name="EasyDatapacks",
    version="0.1",
    author="emorgan00",
    description="A new minecraft datapack language",
    url="https://github.com/emorgan00/EasyDatapacks",
    keywords="minecraft datapack",
    license="MIT",
    package_dir={"datapack": "src"},
    packages=["datapack"],
    entry_points={"console_scripts": ["datapack = datapack.cli:run"]},
    py_modules=["__main__"] if egg_dist else [],
)

if egg_dist:
    os.remove(main_file)
