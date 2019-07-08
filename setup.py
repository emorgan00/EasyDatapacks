from setuptools import setup


setup(
    name="EasyDatapacks",
    version="0.1",
    author="emorgan00",
    description="A new minecraft datapack language",
    url="https://github.com/emorgan00/EasyDatapacks",
    keywords="minecraft datapack",
    license="MIT",
    license_file="LICENSE",
    packages=["datapack"],
    entry_points={"console_scripts": ["datapack = datapack.__main__:main"]},
)
