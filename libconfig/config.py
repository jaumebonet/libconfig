# -*- coding: utf-8 -*-
"""
.. codeauthor:: Jaume Bonet <jaume.bonet@gmail.com>
"""
# Standard Libraries
import json
import os

# External Libraries
import pandas as pd
import yaml
import six

# This Library
import libconfig.evaluator as ev

if six.PY2:
    from subprocess import check_output, CalledProcessError
else:
    from subprocess import run, PIPE


pd.set_option('display.max_colwidth', -1)

__all__ = ['Config', 'AlreadyRegisteredError', 'NotRegisteredError']


class Config(object):
    def __init__(self):
        self.clmn = ['k1', 'k2', 'value', 'type',
                     'default', 'locked', 'description', 'values']
        self.gc = pd.DataFrame(columns=self.clmn)
        self.open = True

    def register_option(self, key, subkey, default, _type, definition,
                        values=None, locked=False):
        """Create a new option.

        :param str key: First identifier of the option.
        :param str subkey: Second identifier of the option.
        :param default: Default value of the option. Type varies and it is
            described by ``_type``.
        :param str _type: Type of the value of the option. Available
            options are: [``int``, ``float``, ``bool``, ``text``,
            ``string``, ``path_in``, ``path_out``].
        :param str definition: Brief explanation of the option.
        :type definition: :class:`str`
        :param values: Available values for the option.
        :type values: :func:`list` of accepted ``_type``
        :param bool locked: If True, option cannot be altered.

        :raise:
            :AlreadyRegisteredError: If ``key`` or ``subkey`` already
                define an option.

        """
        if not self.open:
            return

        key, subkey = _lower_keys(key, subkey)
        _entry_must_not_exist(self.gc, key, subkey)

        ev.value_eval(default, _type)
        values = None if values is False else values
        new_opt = pd.Series([key, subkey, default, _type, default,
                             locked, definition, values], index=self.clmn)

        self.gc = self.gc.append(new_opt, ignore_index=True)

    def unregister_option(self, key, subkey):
        """Removes an option from the manager.

        :param str key: First identifier of the option.
        :param str subkey: Second identifier of the option.

        raise:
            :NotRegisteredError: If ``key`` or ``subkey`` do not define
                any option.
        """
        if not self.open:
            return

        key, subkey = _lower_keys(key, subkey)
        _entry_must_exist(self.gc, key, subkey)

        self.gc = self.gc[~((self.gc['k1'] == key) &
                            (self.gc['k2'] == subkey))]

    def get_option(self, key, subkey, in_path_none=False):
        """Get the current value of the option.

        :param str key: First identifier of the option.
        :param str subkey: Second identifier of the option.
        :param bool in_path_none: Allows for ``in_path`` values of
            :data:`None` to be retrieved.

        :return: Current value of the option (type varies).

        :raise:
            :NotRegisteredError: If ``key`` or ``subkey`` do not define
                any option.
            :ValueError: If a ``in_path`` type with :data:`None` value is
                requested.
        """
        key, subkey = _lower_keys(key, subkey)
        _entry_must_exist(self.gc, key, subkey)

        df = self.gc[(self.gc["k1"] == key) & (self.gc["k2"] == subkey)]
        if df["type"].values[0] == "bool":
            return bool(df["value"].values[0])
        elif df["type"].values[0] == "int":
            return int(df["value"].values[0])
        elif df["type"].values[0] == "path_in":
            if df["value"].values[0] is None and not in_path_none:
                raise ValueError('Unspecified path for {0}.{1}'.format(key,
                                                                       subkey))
            return df["value"].values[0]
        else:
            return df["value"].values[0]

    def get_option_default(self, key, subkey):
        """Get the default value of the option.

        :param str key: First identifier of the option.
        :param str subkey: Second identifier of the option.

        :return: Default value of the option (type varies).

        :raise:
            :NotRegisteredError: If ``key`` or ``subkey`` do not define
                any option.
        """
        key, subkey = _lower_keys(key, subkey)
        _entry_must_exist(self.gc, key, subkey)

        df = self.gc[(self.gc["k1"] == key) & (self.gc["k2"] == subkey)]
        if df["type"].values[0] == "bool":
            return bool(df["default"].values[0])
        elif df["type"].values[0] == "int":
            return int(df["default"].values[0])
        else:
            return df["default"].values[0]

    def get_option_description(self, key, subkey):
        """Get the string describing a particular option.

        :param str key: First identifier of the option.
        :param str subkey: Second identifier of the option.

        :return: :class:`str` - description of the option.

        :raise:
            :NotRegisteredError: If ``key`` or ``subkey`` do not define any
                option.
        """
        key, subkey = _lower_keys(key, subkey)
        _entry_must_exist(self.gc, key, subkey)

        return self.gc[(self.gc["k1"] == key) &
                       (self.gc["k2"] == subkey)]["description"].values[0]

    def get_option_type(self, key, subkey):
        """Get the type of a particular option.

        :param str key: First identifier of the option.
        :param str subkey: Second identifier of the option.

        :return: :class:`str` - description of the type.

        :raise:
            :NotRegisteredError: If ``key`` or ``subkey`` do not define any
                option.
        """
        key, subkey = _lower_keys(key, subkey)
        _entry_must_exist(self.gc, key, subkey)

        return self.gc[(self.gc["k1"] == key) &
                       (self.gc["k2"] == subkey)]["type"].values[0]

    def get_option_alternatives(self, key, subkey):
        """Get list of available values for an option.

        :param str key: First identifier of the option.
        :param str subkey: Second identifier of the option.

        :return: Union[:func:`list`, :data:`None`] - alternative values
            for the option, if any specified (otherwise, is open).

        :raise:
            :NotRegisteredError: If ``key`` or ``subkey`` do not define any
                option.
        """
        key, subkey = _lower_keys(key, subkey)
        _entry_must_exist(self.gc, key, subkey)

        return self.gc[(self.gc["k1"] == key) &
                       (self.gc["k2"] == subkey)]["values"].values[0]

    def set_option(self, key, subkey, value):
        """Sets the value of an option.

        :param str key: First identifier of the option.
        :param str subkey: Second identifier of the option.
        :param value: New value for the option (type varies).

        :raise:
            :NotRegisteredError: If ``key`` or ``subkey`` do not define any
                option.
            :ValueError: If the targeted obtion is locked.
            :ValueError: If the provided value is not the expected
                type for the option.
            :ValueError: If the provided value is not in the expected
                available values for the option.
        """
        key, subkey = _lower_keys(key, subkey)
        _entry_must_exist(self.gc, key, subkey)

        df = self.gc[(self.gc["k1"] == key) & (self.gc["k2"] == subkey)]
        if df["locked"].values[0]:
            raise ValueError("{0}.{1} option is locked".format(key, subkey))
        ev.value_eval(value, df["type"].values[0])
        if not self.check_option(key, subkey, value):
            info = "{0}.{1} accepted options are: ".format(key, subkey)
            info += "[{}]".format(", ".join(df["values"].values[0]))
            raise ValueError(info)
        self.gc.loc[
            (self.gc["k1"] == key) &
            (self.gc["k2"] == subkey), "value"] = value

    def check_option(self, key, subkey, value):
        """Evaluate if a given value fits the option.

        If an option has a limited set of available values, check if the
        provided value is amongst them.

        :param str key: First identifier of the option.
        :param str subkey: Second identifier of the option.
        :param value: Value to test (type varies).

        :return: :class:`bool` - does ``value`` belong to the options?

        :raise:
            :NotRegisteredError: If ``key`` or ``subkey`` do not define any
                option.
            :ValueError: If the provided value is not the expected
                type for the option.
        """
        key, subkey = _lower_keys(key, subkey)
        _entry_must_exist(self.gc, key, subkey)

        df = self.gc[(self.gc["k1"] == key) & (self.gc["k2"] == subkey)]
        ev.value_eval(value, df["type"].values[0])
        if df["values"].values[0] is not None:
            return value in df["values"].values[0]
        return True

    def reset_option(self, key, subkey):
        """Resets a single option to the default values.

        :param str key: First identifier of the option.
        :param str subkey: Second identifier of the option.

        :raise:
            :NotRegisteredError: If ``key`` or ``subkey`` do not define any
                option.
            :ValueError: If the targeted obtion is locked.
        """
        if not self.open:
            return

        key, subkey = _lower_keys(key, subkey)
        _entry_must_exist(self.gc, key, subkey)

        df = self.gc[(self.gc["k1"] == key) & (self.gc["k2"] == subkey)]
        if df["locked"].values[0]:
            raise ValueError("{0}.{1} option is locked".format(key, subkey))
        val = df["default"].values[0]
        self.gc.loc[
            (self.gc["k1"] == key) &
            (self.gc["k2"] == subkey), "value"] = val

    def lock_option(self, key, subkey):
        """Make an option unmutable.

        :param str key: First identifier of the option.
        :param str subkey: Second identifier of the option.

        :raise:
            :NotRegisteredError: If ``key`` or ``subkey`` do not define any
                option.
        """
        key, subkey = _lower_keys(key, subkey)
        _entry_must_exist(self.gc, key, subkey)

        self.gc.loc[
            (self.gc["k1"] == key) &
            (self.gc["k2"] == subkey), "locked"] = True

    def lock_configuration(self):
        """Do not allow calls to :meth:`.Config.register_option` or
        :meth:`.Config.unregister_option`
        """
        self.open = False

    def show_options(self, key=""):
        """Returns a copy the options :class:`~pandas.DataFrame`.

        Called on jupyter notebook, it will print them in pretty
        :class:`~pandas.DataFrame` format.

        :param str key: First identifier of the option. If not provided,
            all options are returned.

        :return: :class:`~pandas.DataFrame`
        """
        key, subkey = _lower_keys(key, '')

        if key == "":
            return self.gc.copy()
        return self.gc[(self.gc["k1"] == key)].copy()

    def reset_options(self, empty=True):
        """Empty ALL options.

        :param bool empty: When :data:`True`, completelly removes all options;
            when :data:`False`, sets them back to its original value.

        This function skips ``locked`` control.
        """
        if empty:
            self.gc = pd.DataFrame(columns=self.clmn)
        else:
            self.gc["value"] = self.gc["default"]

    def set_options_from_YAML(self, filename):
        """Load options from a YAML-formated file.

        :param str filename: File from which to load the options.

        :raise:
            :IOError: If ``filename`` does not exist.
        """
        if not os.path.isfile(filename):
            raise IOError("File {0} not found".format(filename))
        stream = open(filename)
        data_dict = yaml.safe_load(stream)
        self.set_options_from_dict(data_dict, filename)

    def set_options_from_JSON(self, filename):
        """Load options from a YAML-formated file.

        :param str filename: File from which to load the options.

        :raise:
            :IOError: If ``filename`` does not exist.
        """
        if not os.path.isfile(filename):
            raise IOError("File {0} not found".format(filename))
        data_str = "".join([x.strip() for x in open(filename).readlines()])
        data_dict = json.loads(data_str)
        self.set_options_from_dict(data_dict, filename)

    def set_options_from_file(self, filename, format='yaml'):
        """Load options from file.

        This is a wrapper over :func:`.set_options_from_JSON` and
        :func:`.set_options_from_YAML`.

        :param str filename: File from which to load the options.
        :param str format: File format (``yaml`` or ``json``).

        :raises:
            :ValueError: If an unknown ``format`` is requested.
        """
        if format.lower() == 'yaml':
            return self.set_options_from_YAML(filename)
        elif format.lower() == 'json':
            return self.set_options_from_JSON(filename)
        else:
            raise ValueError('Unknown format {}'.format(format))

    def set_options_from_dict(self, data_dict, filename=None):
        """Load options from a dictionary.

        :param dict data_dict: Dictionary with the options to load.
        :param str filename: If provided, assume that non-absolute
            paths provided are in reference to the file.
        """
        if filename is not None:
            filename = os.path.dirname(filename)
        for k in data_dict:
            if not isinstance(data_dict[k], dict):
                raise ValueError("The input data has to be a dict of dict")
            for sk in data_dict[k]:
                if self.gc[(self.gc["k1"] == k) &
                           (self.gc["k2"] == sk)].shape[0] == 0:
                    continue
                if isinstance(data_dict[k][sk], six.string_types):
                    data_dict[k][sk] = str(data_dict[k][sk])
                _type = self.gc[(self.gc["k1"] == k) &
                                (self.gc["k2"] == sk)][["type"]].values[0]
                data_dict[k][sk] = ev.cast(data_dict[k][sk], _type)
                if self.get_option(k, sk, True) != data_dict[k][sk]:
                    try:
                        self.set_option(k, sk, data_dict[k][sk])
                    # Provided paths do not work: try add them relative
                    # to the config file
                    except IOError:
                        if filename is None:
                            raise IOError('Error path: {0}.{1}'.format(k, sk))
                        npat = os.path.join(filename, data_dict[k][sk])
                        self.set_option(k, sk, os.path.normpath(npat))
                    except ValueError:
                        pass  # locked options will not be changed

    def write_options_to_file(self, filename, format='yaml'):
        """Write options to file.

        This is a wrapper over :func:`.write_options_to_JSON` and
        :func:`.write_options_to_YAML`.

        :param str filename: Target file to write the options.
        :param str format: File format (``yaml`` or ``json``).

        :raises:
            :ValueError: If an unknown ``format`` is requested.
        """
        if format.lower() == 'yaml':
            self.write_options_to_YAML(filename)
        elif format.lower() == 'json':
            self.write_options_to_JSON(filename)
        else:
            raise ValueError('Unknown format {}'.format(format))

    def write_options_to_YAML(self, filename):
        """Writes the options in YAML format to a file.

        :param str filename: Target file to write the options.
        """
        fd = open(filename, "w")
        yaml.dump(_options_to_dict(self.gc), fd, default_flow_style=False)
        fd.close()

    def write_options_to_JSON(self, filename):
        """Writes the options in JSON format to a file.

        :param str filename: Target file to write the options.
        """
        fd = open(filename, "w")
        fd.write(json.dumps(_options_to_dict(self.gc), indent=2,
                            separators=(',', ': ')))
        fd.close()

    def document_options(self):
        """Generates a docstring table to add to the library documentation.

        :return: :class:`str`
        """
        k1 = max([len(_) for _ in self.gc['k1']]) + 4
        k1 = max([k1, len('Option Class')])
        k2 = max([len(_) for _ in self.gc['k2']]) + 4
        k2 = max([k2, len('Option ID')])

        separators = "  ".join(["".join(["=", ] * k1),
                                "".join(["=", ] * k2),
                                "".join(["=", ] * 11)])
        line = ("{0:>"+str(k1)+"}  {1:>"+str(k2)+"}  {2}")

        data = []
        data.append(separators)
        data.append(line.format('Option Class', 'Option ID', 'Description'))
        data.append(separators)
        for _, row in self.gc.iterrows():
            data.append(line.format("**" + row['k1'] + "**",
                                    "**" + row['k2'] + "**",
                                    row['description']))
        data.append(separators)
        return "\n".join(data)

    def get_local_config_file(self, filename):
        """Find local file to setup default values.

        There is a pre-fixed logic on how the search of the configuration
        file is performed. If the highes priority configuration file is found,
        there is no need to search for the next. From highest to lowest
        priority:

        1. **Local:** Configuration file found in the current working
           directory.
        2. **Project:** Configuration file found in the root of the current
           working ``git`` repository.
        3. **User:** Configuration file found in the user's ``$HOME``.

        :param str filename: Raw name of the configuration file.

        :return: Union[:class:`.str`, :data:`None`] - Configuration file with
            the highest priority, :data:`None` if no config file is found.
        """
        if os.path.isfile(filename):
            # Local has priority
            return filename
        else:
            try:
                # Project. If not in a git repo, this will not exist.
                config_repo = _get_repo()
                if len(config_repo) == 0:
                    raise Exception()
                config_repo = os.path.join(config_repo, filename)
                if os.path.isfile(config_repo):
                    return config_repo
                else:
                    raise Exception()
            except Exception:
                home = os.getenv("HOME", os.path.expanduser("~"))
                config_home = os.path.join(home, filename)
                if os.path.isfile(config_home):
                    return config_home
        return None

    def ifndef(self):
        """Equivalent to C's #IFNDEF.

        If options are repeatedly registered inside this ``with`` statement,
        the resulting error is taken care.

        Although in a library the declaration is only going to be done once, it
        is recomended to go through this process in order to avoid problems
        with _jupyter_ and the ``%autoreload`` setting.
        """
        return IFNDEF(self)

    def on_option_value(self, *args):
        return ONVALUE(self, *args)


class ONVALUE(object):
    """Temporarily change the configuration values.

    :raises:
        :ValueError: If the number of parameters cannot be casted into
            one or multiple options.

    .. ipython::

        In [1]: import libconfig as cfg
           ...: cfg.register_option('opt', 'one', 1, 'int', 'option 1')
           ...: cfg.register_option('opt', 'two', 2, 'int', 'option 2')
           ...: print('opt.one', cfg.get_option('opt', 'one'))
           ...: with cfg.on_option_value('opt', 'one', 10):
           ...:     print('with opt.one', cfg.get_option('opt', 'one'))
           ...: print('opt.one', cfg.get_option('opt', 'one'))
           ...: print('opt.two', cfg.get_option('opt', 'two'))
           ...: with cfg.on_option_value('opt', 'one', 10, 'opt', 'two', 20):
           ...:     print('with opt.one', cfg.get_option('opt', 'one'))
           ...:     print('with opt.two', cfg.get_option('opt', 'two'))
           ...: print('opt.one', cfg.get_option('opt', 'one'))
           ...: print('opt.two', cfg.get_option('opt', 'two'))
           ...: cfg.unregister_option('opt', 'one')
           ...: cfg.unregister_option('opt', 'two')
    """

    def __init__(self, *args):
        def chunks(l, n):
            for i in range(0, len(l), n):
                yield l[i:i + n]

        self.cfg = args[0]
        args = args[1:]

        if not (len(args) % 3 == 0 and len(args) >= 3):
            raise ValueError('option values are defined in 3s.')

        self.values = pd.DataFrame(chunks(args, 3),
                                   columns=['k1', 'k2', 'new_value'])
        self.values['old_value'] = \
            [self.cfg.get_option(l['k1'], l['k2'])
             for _, l in self.values.iterrows()]

    def __enter__(self):
        for i, l in self.values.iterrows():
            self.cfg.set_option(l['k1'], l['k2'], l['new_value'])

    def __exit__(self, *args):
        for i, l in self.values.iterrows():
            self.cfg.set_option(l['k1'], l['k2'], l['old_value'])


class IFNDEF(object):
    """Equivalent to C's #IFNDEF.

    If options are repeatedly registered inside this ``with`` statement, the
    resulting error is taken care.

    Although in a library the declaration is only going to be done once, it
    is recomended to go through this process in order to avoid problems with
    _jupyter_ and the ``%autoreload`` setting.
    """
    def __init__(self, config):
        self.cfg = config
        self.backup = config.gc.copy()

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        if isinstance(value, AlreadyRegisteredError):
            self.cfg.gc = self.backup.copy()
            return True


def _options_to_dict(df):
    kolums = ["k1", "k2", "value"]
    d = df[kolums].values.tolist()
    dc = {}
    for x in d:
        dc.setdefault(x[0], {})
        dc[x[0]][x[1]] = x[2]
    return dc


def _get_repo():
    command = ['git', 'rev-parse', '--show-toplevel']
    if six.PY2:
        try:
            return check_output(command) .decode('utf-8').strip()
        except CalledProcessError:
            return ''
    else:
        return (run(command, stdout=PIPE, stderr=PIPE)
                .stdout.decode('utf-8').strip())


def _lower_keys(key, subkey):
    return key.lower(), subkey.lower()


def _entry_must_exist(df, k1, k2):
    """
    *Decorator* to evaluate key-subkey existence.

    Checks that the key-subkey combo exists in the
    configuration options.
    """
    count = df[(df['k1'] == k1) &
               (df['k2'] == k2)].shape[0]
    if count == 0:
        raise NotRegisteredError(
            "Option {0}.{1} not registered".format(k1, k2))


def _entry_must_not_exist(df, k1, k2):
    """
    *Decorator* to evaluate key-subkey non-existence.

    Checks that the key-subkey combo does not exists in the
    configuration options.
    """
    count = df[(df['k1'] == k1) &
               (df['k2'] == k2)].shape[0]
    if count > 0:
        raise AlreadyRegisteredError(
            "Option {0}.{1} already registered".format(k1, k2))


class AlreadyRegisteredError(Exception):
    """
    """
    pass


class NotRegisteredError(Exception):
    """
    """
    pass
