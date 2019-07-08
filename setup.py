from setuptools import setup

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
    packages=["datapack"],
    entry_points={"console_scripts": ["datapack = datapack.__main__:main"]},
    py_modules=["datapack.__main__:main"],
)
