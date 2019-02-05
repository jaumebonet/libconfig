.. libconfig documentation master file, created by
   sphinx-quickstart on Thu Jan 18 11:39:05 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

libconfig: global config variables for libraries
================================================


``libconfig`` is a Python library inspired by `pandas <https://pandas.pydata.org/>`_
to manage global configuration variables in your own python libraries.

To see the code, please visit the `github repository <https://github.com/jaumebonet/libconfig>`_.

Report bugs and problems through our `issue tracker <https://github.com/jaumebonet/RosettaSilentToolbox/issues>`_.

Install
-------

You can install ``libconfig`` directly from **PyPi**::

  pip install libconfig

Basic Example
-------------

The most expected way to use the library is by creating a ``core`` file in your library in which to setup the global
values of your library. As an example, a minimized version of the configuration of the
`RosettaSilentToolbox <https://github.com/jaumebonet/RosettaSilentToolbox>`_ looks like this:

.. ipython::

  In [1]: import multiprocessing
     ...:
     ...: from libconfig import Config
     ...:
     ...: core = Config()
     ...: with core.ifndef():
     ...:   # This avoids recalling this every time, as register_option will raise an error when
     ...:   # trying to re-register. Basically, this is the equivalent to Cpp's #IFDEF
     ...:
     ...:   # Register IO control options
     ...:   core.register_option("system", "overwrite",  False, "bool", "Allow overwriting already existing files")
     ...:   core.register_option("system", "output", "./", "path_out", "Default folder to output generated files")
     ...:   core.register_option("system", "cpu", multiprocessing.cpu_count() - 1, "int", "Available CPU for multiprocessing")
     ...:
     ...:   # There are different levels of configuration files that can be picked.
     ...:   # If any configuration file is set up, the priority goes as follows:
     ...:   #   1) Local config file (in the actual executable directory)
     ...:   #   2) Root of the current working repository (if any)
     ...:   #   3) User's home path
     ...:   config_file = core.get_local_config_file('.topobuilder.cfg')
     ...:   if config_file is not None:
     ...:       core.set_options_from_YAML( config_file )
     ...: # Finally, some options are blocked so that they cannot be accessed by users outside the library.
     ...: core.lock_configuration()

This ends up loading a starting set of options:

.. ipython::

  In [2]: import pandas as pd
     ...: pd.set_option('display.width', 1000)
     ...: core.show_options()

And exposing only to the rest of the library (and maybe to the user) the functions to modify those options
in a controlled manner by taking out :meth:`.Config.register_option` and :meth:`.Config.reset_options` from the global view.

One can also make the target library able to be configured through a file defining the values of the registered
options. Through :meth:`.Config.get_local_config_file`, the library will search for a config file in the current working
directory, the repo root or the user's home, allowing for different levels of specific configuration.

Errors
------

The library defines two specific errors:

* **AlreadyRegisteredError:** When trying to register an already registered option
* **NotRegisteredError:** When trying to access a non-registered option.

A list of all the available functions can be found in the :ref:`API <api>`.

.. toctree::
   :hidden:

   api
