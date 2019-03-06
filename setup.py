from setuptools import setup, find_packages

requirements = ['cherrypy', 'gpxpy', 'mako', 'bson', 'pymongo', 'bcrypt', 'fitparse', 'markdown', 'scipy', 'sklearn', 'flask', 'unidecode', 'Celery', 'tensorflow', 'lxml']

setup(
    name='straenweb',
    version='0.9.0',
    description='',
    url='https://github.com/msimms/StraenWeb',
    author='Mike Simms',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=requirements,
)
