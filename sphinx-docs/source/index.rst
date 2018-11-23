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
     ...: from libconfig import *
     ...:
     ...: with ifndef():
     ...:   # This avoids recalling this every time, as register_option will raise an error when
     ...:   # trying to re-register. Basically, this is the equivalent to Cpp's #IFDEF
     ...:
     ...:   # Register IO control options
     ...:   register_option("system", "overwrite",  False, "bool", "Allow overwriting already existing files")
     ...:   register_option("system", "output", "./", "path_out", "Default folder to output generated files")
     ...:   register_option("system", "cpu", multiprocessing.cpu_count() - 1, "int", "Available CPU for multiprocessing")
     ...:
     ...: # Finally, register_option, unregister_option and reset_option are taken out from the global view
     ...: # so that they are not imported with the rest of the functions. This way the user can not access
     ...: # them when importing the library and has to work through the rest of the available functions.
     ...: for name in user_forbidden:
     ...:   del globals()[name]

This ends up loading a starting set of options:

.. ipython::

  In [2]: import pandas as pd
     ...: pd.set_option('display.width', 1000)
     ...: show_options()

And exposing only to the rest of the library (and maybe to the user) the functions to modify those options
in a controlled manner by taking out :func:`.register_option` and :func:`.reset_options` from the global view.

One can also make the target library able to be configured through a file defining the values of the registered
options. Through :func:`.get_local_config_file`, the library will search for a config file in the current working
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
