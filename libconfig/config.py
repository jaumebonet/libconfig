# -*-
# @project: libconfig
# @file:    config.py
#
# @author: jaume.bonet
# @email:  jaume.bonet@gmail.com
# @url:    jaumebonet.cat
#
# @date:   2017-10-03 14:59:01
# @Last modified time: 21-Nov-2018
#
# -*-
import json
import os

import pandas as pd
import yaml
import six

import libconfig.evaluator as ev
import libconfig.util as util

if six.PY2:
    from subprocess import check_output, CalledProcessError
else:
    from subprocess import run, PIPE


pd.set_option('display.max_colwidth', -1)


__all__ = ["register_option", "reset_option", "reset_options", "set_option",
           "set_options_from_dict", "set_options_from_file",
           "set_options_from_JSON", "set_options_from_YAML", "get_option",
           "get_option_default", "get_option_description",
           "write_options_to_file", "write_options_to_JSON",
           "write_options_to_YAML", "show_options",
           "lock_option", "check_option", "get_option_alternatives",
           "document_options", "on_option_value",
           "get_local_config_file"]


_columns = ["primary-key", "secondary-key", "value", "type",
            "default", "locked", "description", "values"]


_global_config = pd.DataFrame(columns=_columns)


def _get_df(key, subkey):
    global _global_config
    return _global_config[(_global_config["primary-key"] == key) &
                          (_global_config["secondary-key"] == subkey)]


def _options_to_dict():
    kolums = ["primary-key", "secondary-key", "value"]
    d = _global_config[kolums].values.tolist()
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


@util.lower_keynames
@util.entry_must_not_exist
def register_option(key, subkey, default, _type, definition,
                    values=None, locked=False):
    """Create a new option.

    :param str key: First identifier of the option.
    :param str subkey: Second identifier of the option.
    :param default: Default value of the option. Type varies and it is
        described by ``_type``.
    :param str _type: Type of the value of the option. Available options are:
        [``int``, ``float``, ``bool``, ``text``, ``string``,
        ``path_in``, ``path_out``].
    :param str definition: Brief explanation of the option.
    :type definition: :class:`str`
    :param values: Available values for the option.
    :type values: :func:`list` of accepted ``_type``
    :param bool locked: If True, option cannot be altered.

    :raise:
        :KeyError: If ``key`` or ``subkey`` already define an option.

    """
    ev.value_eval(default, _type)
    if values is False:
        values = None
    new_opt = pd.Series([key, subkey, default, _type, default,
                         locked, definition, values], index=_columns)
    global _global_config
    _global_config = _global_config.append(new_opt, ignore_index=True)


@util.lower_keynames
@util.entry_must_exist
def get_option(key, subkey, in_path_none=False):
    """Get the current value of the option.

    :param str key: First identifier of the option.
    :param str subkey: Second identifier of the option.
    :param bool in_path_none: Allows for ``in_path`` values of
        :data:`None` to be retrieved.

    :return: Current value of the option (type varies).

    :raise:
        :KeyError: If ``key`` or ``subkey`` do not define any option.
        :ValueError: If a ``in_path`` type with :data:`None` value is
            requested.
    """
    df = _get_df(key, subkey)
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


@util.lower_keynames
@util.entry_must_exist
def get_option_default(key, subkey):
    """Get the default value of the option.

    :param str key: First identifier of the option.
    :param str subkey: Second identifier of the option.

    :return: Default value of the option (type varies).

    :raise:
        :KeyError: If ``key`` or ``subkey`` do not define any option.
    """
    df = _get_df(key, subkey)
    if df["type"].values[0] == "bool":
        return bool(df["default"].values[0])
    elif df["type"].values[0] == "int":
        return int(df["default"].values[0])
    else:
        return df["default"].values[0]


@util.lower_keynames
@util.entry_must_exist
def get_option_description(key, subkey):
    """Get the string descriving a particular option.

    :param str key: First identifier of the option.
    :param str subkey: Second identifier of the option.

    :return: :class:`str` - description of the option.

    :raise:
        :KeyError: If ``key`` or ``subkey`` do not define any option.
    """
    return _get_df(key, subkey)["description"].values[0]


@util.lower_keynames
@util.entry_must_exist
def get_option_alternatives(key, subkey):
    """Get list of available values for an option.

    :param str key: First identifier of the option.
    :param str subkey: Second identifier of the option.

    :return: Union[:func:`list`, :data:`None`] - alternative values
        for the option, if any specified (otherwise, is open).

    :raise:
        :KeyError: If ``key`` or ``subkey`` do not define any option.
    """
    return _get_df(key, subkey)["values"].values[0]


@util.lower_keynames
@util.entry_must_exist
def set_option(key, subkey, value):
    """Sets the value of an option.

    :param str key: First identifier of the option.
    :param str subkey: Second identifier of the option.
    :param value: New value for the option (type varies).

    :raise:
        :KeyError: If ``key`` or ``subkey`` do not define any option.
        :ValueError: If the targeted obtion is locked.
        :ValueError: If the provided value is not the expected
            type for the option.
        :ValueError: If the provided value is not in the expected
            available values for the option.
    """
    df = _get_df(key, subkey)
    if df["locked"].values[0]:
        raise ValueError("{0}.{1} option is locked".format(key, subkey))
    ev.value_eval(value, df["type"].values[0])
    if not check_option(key, subkey, value):
        info = "{0}.{1} accepted options are: ".format(key, subkey)
        info += "[{}]".format(", ".join(df["values"].values[0]))
        raise ValueError(info)
    global _global_config
    _global_config.loc[
        (_global_config["primary-key"] == key) &
        (_global_config["secondary-key"] == subkey), "value"] = value


@util.lower_keynames
@util.entry_must_exist
def check_option(key, subkey, value):
    """Evaluate if a given value fits the option.

    If an option has a limited set of available values, check if the provided
    value is amongst them.

    :param str key: First identifier of the option.
    :param str subkey: Second identifier of the option.
    :param value: Value to test (type varies).

    :return: :class:`bool` - does ``value`` belong to the options?

    :raise:
        :KeyError: If ``key`` or ``subkey`` do not define any option.
        :ValueError: If the provided value is not the expected
            type for the option.
    """
    df = _get_df(key, subkey)
    ev.value_eval(value, df["type"].values[0])
    if df["values"].values[0] is not None:
        return value in df["values"].values[0]
    return True


@util.lower_keynames
@util.entry_must_exist
def reset_option(key, subkey):
    """Resets a single option to the default values.

    :param str key: First identifier of the option.
    :param str subkey: Second identifier of the option.

    :raise:
        :KeyError: If ``key`` or ``subkey`` do not define any option.
        :ValueError: If the targeted obtion is locked.
    """
    df = _get_df(key, subkey)
    if df["locked"].values[0]:
        raise ValueError("{0}.{1} option is locked".format(key, subkey))
    val = df["default"].values[0]
    global _global_config
    _global_config.loc[
        (_global_config["primary-key"] == key) &
        (_global_config["secondary-key"] == subkey), "value"] = val


@util.lower_keynames
@util.entry_must_exist
def lock_option(key, subkey):
    """Make an option unmutable.

    :param str key: First identifier of the option.
    :param str subkey: Second identifier of the option.

    :raise:
        :KeyError: If ``key`` or ``subkey`` do not define any option.
    """
    global _global_config
    _global_config.loc[
        (_global_config["primary-key"] == key) &
        (_global_config["secondary-key"] == subkey), "locked"] = True


@util.lower_keynames
def show_options(key=""):
    """Returns a copy the options :class:`~pandas.DataFrame`.

    Called on jupyter notebook, it will print them in pretty
    :class:`~pandas.DataFrame` format.

    :param str key: First identifier of the option. If not provided,
        all options are returned.

    :return: :class:`~pandas.DataFrame`
    """
    global _global_config
    if key == "":
        return _global_config.copy()
    return _global_config[(_global_config["primary-key"] == key)].copy()


def reset_options(empty=True):
    """Empty ALL options.

    :param bool empty: When :data:`True`, completelly removes all options;
        when :data:`False`, sets them back to its original value.

    This function skips ``locked`` control.
    """
    global _global_config

    if empty:
        _global_config = pd.DataFrame(columns=_columns)
    else:
        _global_config["value"] = _global_config["default"]


def set_options_from_YAML(filename):
    """Load options from a YAML-formated file.

    :param str filename: File from which to load the options.

    :raise:
        :IOError: If ``filename`` does not exist.
    """
    if not os.path.isfile(filename):
        raise IOError("File {0} not found".format(filename))
    stream = open(filename)
    data_dict = yaml.safe_load(stream)
    set_options_from_dict(data_dict)


def set_options_from_JSON(filename):
    """Load options from a YAML-formated file.

    :param str filename: File from which to load the options.

    :raise:
        :IOError: If ``filename`` does not exist.
    """
    if not os.path.isfile(filename):
        raise IOError("File {0} not found".format(filename))
    data_str = "".join([x.strip() for x in open(filename).readlines()])
    data_dict = json.loads(data_str)
    set_options_from_dict(data_dict)


def set_options_from_file(filename, format='yaml'):
    """Load options from file.

    This is a wrapper over :func:`.set_options_from_JSON` and
    :func:`.set_options_from_YAML`.

    :param str filename: File from which to load the options.
    :param str format: File format (``yaml`` or ``json``).

    :raises:
        :ValueError: If an unknown ``format`` is requested.
    """
    if format.lower() == 'yaml':
        return set_options_from_YAML(filename)
    elif format.lower() == 'json':
        return set_options_from_JSON(filename)
    else:
        raise ValueError('Unknown format {}'.format(format))


def set_options_from_dict(data_dict):
    """Load options from a dictionary.

    :param dict data_dict: Dictionary with the options to load.
    """
    for k in data_dict:
        if not isinstance(data_dict[k], dict):
            raise ValueError("The input data has to be a dict of dict")
        for sk in data_dict[k]:
            if isinstance(data_dict[k][sk], six.string_types):
                data_dict[k][sk] = str(data_dict[k][sk])
            _type = _get_df(k, sk)[["type"]].values[0]
            data_dict[k][sk] = ev.cast(data_dict[k][sk], _type)
            if get_option(k, sk, True) != data_dict[k][sk]:
                try:
                    set_option(k, sk, data_dict[k][sk])
                except ValueError:
                    pass  # locked options will not be changed


def write_options_to_file(filename, format='yaml'):
    """Write options to file.

    This is a wrapper over :func:`.write_options_to_JSON` and
    :func:`.write_options_to_YAML`.

    :param str filename: Target file to write the options.
    :param str format: File format (``yaml`` or ``json``).

    :raises:
        :ValueError: If an unknown ``format`` is requested.
    """
    if format.lower() == 'yaml':
        write_options_to_YAML(filename)
    elif format.lower() == 'json':
        write_options_to_JSON(filename)
    else:
        raise ValueError('Unknown format {}'.format(format))


def write_options_to_YAML(filename):
    """Writes the options in YAML format to a file.

    :param str filename: Target file to write the options.
    """
    fd = open(filename, "w")
    yaml.dump(_options_to_dict(), fd, default_flow_style=False)
    fd.close()


def write_options_to_JSON(filename):
    """Writes the options in JSON format to a file.

    :param str filename: Target file to write the options.
    """
    fd = open(filename, "w")
    fd.write(json.dumps(_options_to_dict(), indent=2, separators=(',', ': ')))
    fd.close()


def document_options():
    """Generates a docstring table to add to the library documentation.

    :return: :class:`str`
    """
    global _global_config

    k1 = max([len(_) for _ in _global_config['primary-key']]) + 4
    k1 = max([k1, len('Option Class')])
    k2 = max([len(_) for _ in _global_config['secondary-key']]) + 4
    k2 = max([k2, len('Option ID')])

    separators = "  ".join(["".join(["=", ] * k1),
                            "".join(["=", ] * k2),
                            "".join(["=", ] * 11)])
    line = ("{0:>"+str(k1)+"}  {1:>"+str(k2)+"}  {2}")

    data = []
    data.append(separators)
    data.append(line.format('Option Class', 'Option ID', 'Description'))
    data.append(separators)
    for _, row in _global_config.iterrows():
        data.append(line.format("**" + row['primary-key'] + "**",
                                "**" + row['secondary-key'] + "**",
                                row['description']))
    data.append(separators)

    return "\n".join(data)


def get_local_config_file(filename):
    """Find local file to setup default values.

    There is a pre-fixed logic on how the search of the configuration
    file is performed. If the highes priority configuration file is found,
    there is no need to search for the next. From highest to lowest priority:

    1. **Local:** Configuration file found in the current working directory.
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
            config_home = os.path.join(os.getenv("HOME",
                                                 os.path.expanduser("~")),
                                       filename)
            if os.path.isfile(config_home):
                return config_home
    return None


class on_option_value(object):
    """Temporarily change the configuration values.

    :raises:
        :ValueError: If the number of parameters cannot be casted into
            one or multiple options.

    .. ipython::

        In [1]: import libconfig as cfg
           ...: cfg.register_option('opt', 'one', 1, 'int', 'option 1')
           ...: cfg.register_option('opt', 'two', 2, 'int', 'option 2')
           ...: print(cfg.get_option('opt', 'one'))
           ...: with cfg.on_option_value('opt', 'one', 10):
           ...:     print(cfg.get_option('opt', 'one'))
           ...: print(cfg.get_option('opt', 'one'))
           ...: print(cfg.get_option('opt', 'two'))
           ...: with cfg.on_option_value('opt', 'one', 10, 'opt', 'two', 20):
           ...:     print(cfg.get_option('opt', 'one'))
           ...:     print(cfg.get_option('opt', 'two'))
           ...: print(cfg.get_option('opt', 'one'))
           ...: print(cfg.get_option('opt', 'two'))
    """

    def __init__(self, *args):
        def chunks(l, n):
            for i in range(0, len(l), n):
                yield l[i:i + n]

        if not (len(args) % 3 == 0 and len(args) >= 3):
            raise ValueError('option values are defined in 3s.')

        self.values = pd.DataFrame(chunks(args, 3),
                                   columns=['k1', 'k2', 'new_value'])
        self.values['old_value'] = \
            [get_option(l['k1'], l['k2']) for _, l in self.values.iterrows()]

    def __enter__(self):
        for i, l in self.values.iterrows():
            set_option(l['k1'], l['k2'], l['new_value'])

    def __exit__(self, *args):
        for i, l in self.values.iterrows():
            set_option(l['k1'], l['k2'], l['old_value'])
