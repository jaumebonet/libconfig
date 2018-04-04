# -*-
# @project: libconfig
# @file:    config.py
#
# @author: jaume.bonet
# @email:  jaume.bonet@gmail.com
# @url:    jaumebonet.cat
#
# @date:   2017-10-03 14:59:01
# @Last modified time: 04-Apr-2018
#
# -*-
import json
import os

import pandas as pd
import yaml
import six

import libconfig.evaluator as ev
import libconfig.util as util


pd.set_option('display.max_colwidth', -1)


__all__ = ["register_option", "reset_option", "reset_options", "set_option",
           "set_options_from_dict", "set_options_from_JSON",
           "set_options_from_YAML", "get_option", "get_option_default",
           "get_option_description", "write_options_to_JSON",
           "write_options_to_YAML", "show_options", "lock_option",
           "check_option"]


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


@util.entry_must_not_exist
@util.lower_keynames
def register_option(key, subkey, default, _type, definition,
                    values=None, locked=False):
    """
    Create a new option.

    :param key: First identifier of the option.
    :type key: :class:`str`
    :param subkey: Second identifier of the option.
    :type subkey: :class:`str`
    :param default: Default value of the option. Type varies and it is
        described by ``_type``.
    :param _type: Type of the value of the option. Available options are:
        [``int``, ``float``, ``bool``, ``text``, ``string``,
        ``path_in``, ``path_out``].
    :type _type: :class:`str`
    :param definition: Brief explanation of the option.
    :type definition: :class:`str`
    :param list values: Available values for the option.
    :type values: :func:`list` of accepted ``_type``
    :param locked: If True, option cannot be altered.
    :type locked: :class:`bool`

    :raise:
        :KeyError: If ``key`` or ``subkey`` already define an option.

    """
    ev.eval(default, _type)
    if values is False:
        values = None
    new_opt = pd.Series([key, subkey, default, _type, default,
                         locked, definition, values], index=_columns)
    global _global_config
    _global_config = _global_config.append(new_opt, ignore_index=True)


@util.entry_must_exist
@util.lower_keynames
def get_option(key, subkey):
    """
    Get the current value of the option.

    :param key: First identifier of the option.
    :type key: :class:`str`
    :param subkey: Second identifier of the option.
    :type subkey: :class:`str`

    :return: Current value of the option (type varies).

    :raise:
        :KeyError: If ``key`` or ``subkey`` do not define any option.
    """
    df = _get_df(key, subkey)
    if df["type"].values[0] == "bool":
        return bool(df["value"].values[0])
    elif df["type"].values[0] == "int":
        return int(df["value"].values[0])
    else:
        return df["value"].values[0]


@util.entry_must_exist
@util.lower_keynames
def get_option_default(key, subkey):
    """
    Get the default value of the option.

    :param key: First identifier of the option.
    :type key: :class:`str`
    :param subkey: Second identifier of the option.
    :type subkey: :class:`str`

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


@util.entry_must_exist
@util.lower_keynames
def get_option_description(key, subkey):
    """
    Get the string descriving a particular option.

    :param key: First identifier of the option.
    :type key: :class:`str`
    :param subkey: Second identifier of the option.
    :type subkey: :class:`str`

    :return: :class:`str` - description of the option.

    :raise:
        :KeyError: If ``key`` or ``subkey`` do not define any option.
    """
    return _get_df(key, subkey)["description"].values[0]


@util.entry_must_exist
@util.lower_keynames
def get_option_alternatives(key, subkey):
    """
    Get list of available values for an option.

    :param key: First identifier of the option.
    :type key: :class:`str`
    :param subkey: Second identifier of the option.
    :type subkey: :class:`str`

    :return: Union[:func:`list`, :data:`None`] - alternative values
        for the option, if any specified (otherwise, is open).

    :raise:
        :KeyError: If ``key`` or ``subkey`` do not define any option.
    """
    return _get_df(key, subkey)["values"].values[0]


@util.entry_must_exist
@util.lower_keynames
def set_option(key, subkey, value):
    """
    Sets the value of an option.

    :param key: First identifier of the option.
    :type key: :class:`str`
    :param subkey: Second identifier of the option.
    :type subkey: :class:`str`
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
    ev.eval(value, df["type"].values[0])
    if not check_option(key, subkey, value):
        info = "{0}.{1} accepted options are: ".format(key, subkey)
        info += "[{}]".format(", ".join(df["values"].values[0]))
        raise ValueError(info)
    global _global_config
    _global_config.loc[
        (_global_config["primary-key"] == key) &
        (_global_config["secondary-key"] == subkey), "value"] = value


@util.entry_must_exist
@util.lower_keynames
def check_option(key, subkey, value):
    """
    If an option has a limited set of available values, check if the provided
    value is amongst them.

    :param key: First identifier of the option.
    :type key: :class:`str`
    :param subkey: Second identifier of the option.
    :type subkey: :class:`str`
    :param value: Value to test (type varies).

    :return: :class:`bool` - does ``value`` belong to the options?

    :raise:
        :KeyError: If ``key`` or ``subkey`` do not define any option.
        :ValueError: If the provided value is not the expected
            type for the option.
    """
    df = _get_df(key, subkey)
    ev.eval(value, df["type"].values[0])
    if df["values"].values[0] is not None:
        return value in df["values"].values[0]
    return True


@util.entry_must_exist
@util.lower_keynames
def reset_option(key, subkey):
    """
    Resets a single option to the default values.

    :param key: First identifier of the option.
    :type key: :class:`str`
    :param subkey: Second identifier of the option.
    :type subkey: :class:`str`

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


@util.entry_must_exist
@util.lower_keynames
def lock_option(key, subkey):
    """
    Make an option unmutable.

    :param key: First identifier of the option.
    :type key: :class:`str`
    :param subkey: Second identifier of the option.
    :type subkey: :class:`str`

    :raise:
        :KeyError: If ``key`` or ``subkey`` do not define any option.
    """
    global _global_config
    _global_config.loc[
        (_global_config["primary-key"] == key) &
        (_global_config["secondary-key"] == subkey), "locked"] = True


@util.lower_keynames
def show_options(key=""):
    """
    Returns a copy the options :class:`~pandas.DataFrame`.
    Called on jupyter notebook, it will print them in pretty
    :class:`~pandas.DataFrame` format.

    :param key: First identifier of the option. If not provided,
        all options are returned.
    :type key: :class:`str`

    :return: :class:`~pandas.DataFrame`
    """
    global _global_config
    if key == "":
        return _global_config.copy()
    return _global_config[(_global_config["primary-key"] == key)].copy()


def reset_options():
    """
    Empty ALL options.
    This function skips ``locked`` control.
    """
    global _global_config
    _global_config = pd.DataFrame(columns=_columns)


def set_options_from_YAML(filename):
    """
    Load options from a YAML-formated file.

    :param filename: File from which to load the options.
    :type filename: :class:`str`

    :raise:
        :IOError: If ``filename`` does not exist.
    """
    if not os.path.isfile(filename):
        raise IOError("File {0} not found".format(filename))
    stream = open(filename)
    data_dict = yaml.load(stream)
    set_options_from_dict(data_dict)


def set_options_from_JSON(filename):
    """
    Load options from a YAML-formated file.

    :param filename: File from which to load the options.
    :type filename: :class:`str`

    :raise:
        :IOError: If ``filename`` does not exist.
    """
    if not os.path.isfile(filename):
        raise IOError("File {0} not found".format(filename))
    data_str = "".join([x.strip() for x in open(filename).readlines()])
    data_dict = json.loads(data_str)
    set_options_from_dict(data_dict)


def set_options_from_dict(data_dict):
    """
    Load options from a dictionary.

    :param data_dict: Dictionary with the options to load.
    :type data_dict: :class:`dict`
    """
    for k in data_dict:
        if not isinstance(data_dict[k], dict):
            raise ValueError("The input data has to be a dict of dict")
        for sk in data_dict[k]:
            if isinstance(data_dict[k][sk], six.string_types):
                data_dict[k][sk] = str(data_dict[k][sk])
            _type = _get_df(k, sk)[["type"]].values[0]
            data_dict[k][sk] = ev.cast(data_dict[k][sk], _type)
            if get_option(k, sk) != data_dict[k][sk]:
                set_option(k, sk, data_dict[k][sk])


def write_options_to_YAML(filename):
    """
    Writes the options in YAML format to a file.

    :param filename: Target file to write the options.
    :type filename: :class:`str`
    """
    fd = open(filename, "w")
    yaml.dump(_options_to_dict(), fd, default_flow_style=False)
    fd.close()


def write_options_to_JSON(filename):
    """
    Writes the options in JSON format to a file.

    :param filename: Target file to write the options.
    :type filename: :class:`str`
    """
    fd = open(filename, "w")
    fd.write(json.dumps(_options_to_dict(), indent=2, separators=(',', ': ')))
    fd.close()
