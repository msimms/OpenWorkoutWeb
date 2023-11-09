from setuptools import setup, find_packages

requirements = ['cherrypy', 'gpxpy', 'mako', 'bson', 'pymongo', 'bcrypt', 'fitparse', 'flask', 'lxml', 'markdown', 'requests', 'scipy', 'sklearn', 'unidecode', 'Celery', 'tensorflow', 'pandas']

setup(
    name='openworkoutweb',
    version='0.57.0',
    description='',
    url='https://github.com/msimms/OpenWorkoutWeb',
    author='Mike Simms',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=requirements,
)
