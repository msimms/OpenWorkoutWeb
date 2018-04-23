from setuptools import setup, find_packages

requirements = ['cherrypy', 'gpxpy', 'mako', 'bson', 'pymongo', 'bcrypt', 'python-tcxparser', 'fitparse']

setup(
    name='straenweb',
    version='0.1.0',
    description='',
    url='https://github.com/msimms/StraenWeb',
    author='Mike Simms',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=requirements,
)
