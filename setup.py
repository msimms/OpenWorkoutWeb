from setuptools import setup, find_packages

requirements = ['cherrypy', 'gpxpy', 'mako', 'bson', 'pymongo', 'bcrypt', 'fitparse', 'flask', 'lxml', 'markdown', 'scipy', 'sklearn', 'unidecode', 'Celery', 'tensorflow', 'pandas']

setup(
    name='straenweb',
    version='0.26.0',
    description='',
    url='https://github.com/msimms/StraenWeb',
    author='Mike Simms',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=requirements,
)
