from setuptools import setup
import sys

try:
    import py2exe
except ImportError:
    pass


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
    py_modules=["__main__"] if "bdist_egg" in sys.argv else [],
)
