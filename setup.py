from setuptools import setup, find_packages

setup(
    name="ephemeris",
    version="0.1.0",
    packages=find_packages(include=["ephemeris", "ephemeris.*"]),
    include_package_data=True,
    # Other setup configurations
)
