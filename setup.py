from setuptools import setup, find_packages

# versioning
import versioneer

setup(
    name='libconfig',
    version=versioneer.get_version(),

    description='Library Configuration Library',
    long_description='A simple tool to generate and manage '
                     'global configuration variables',

    # The project's main homepage.
    url='https://github.com/jaumebonet/libconfig',

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
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    project_urls={
        'Documentation': 'http://jaumebonet.cat/libconfig',
        'Source': 'https://github.com/jaumebonet/libconfig/',
        'Tracker': 'https://github.com/jaumebonet/libconfig/issues',
    },

    platforms='UNIX',
    keywords='development',

    install_requires=['pandas', 'pyyaml', 'six'],

    packages=find_packages(exclude=['docs', 'test', 'sphinx-docs']),
    include_package_data=True,
    cmdclass=versioneer.get_cmdclass(),
)
