from setuptools import setup, find_packages  # Always prefer setuptools over distutils
__version__ = '0.0.4'

setup(
    name='libconfig',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # http://packaging.python.org/en/latest/tutorial.html#version
    version=__version__,

    description='Library Configuration Library',
    # long_description=read('README.md'),

    # The project's main homepage.
    url='https://github.com/jaumebonet/libconfig',
    download_url = 'https://github.com/jaumebonet/libconfig/archive/{0}.tar.gz'.format(__version__),

    # Author details
    author='Jaume Bonet',
    author_email='jaume.bonet@gmail.com',

    # Choose your license
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    platforms='UNIX',
    keywords='development',

    install_requires=['pandas', 'pyyaml'],

    packages=find_packages(exclude=['docs', 'test']),

    zip_safe = False,
)
