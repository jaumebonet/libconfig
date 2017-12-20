# -*-
# @project: libconfig
# @file:    config.py
#
# @author: jaume.bonet
# @email:  jaume.bonet@gmail.com
# @url:    jaumebonet.cat
#
# @date:   2017-10-03 14:59:01
# @Last modified time: 20-Dec-2017
#
# -*-
import json
import os

import pandas as pd
import yaml

from evaluator import eval, cast

pd.set_option( 'display.max_colwidth', -1 )

_columns = [ "primary-key", "secondary-key",
             "value", "type", "default", "locked", "description", "values" ]

_global_config = pd.DataFrame( columns = _columns )

def _has_primary_key( key ):
    _key = key.lower()
    return _key in _global_config["primary-key"].values

def _primary_df( key ):
    _key = key.lower()
    return _global_config[ ( _global_config["primary-key"] == _key ) ]

def _has_secondary_key( key, subkey ):
    _subkey = subkey.lower()
    return _subkey in _primary_df(key).values

def _secondary_df( key, subkey ):
    _subkey = subkey.lower()
    df = _primary_df( key )
    return df[ ( df["secondary-key"] == _subkey) ]

def _options_to_dict():
    kolums = ["primary-key", "secondary-key", "value"]
    d  = _global_config[kolums].values.tolist()
    dc = {}
    for x in d:
        dc.setdefault(x[0], {})
        dc[x[0]][x[1]] = x[2]
    return dc

def register_option( key, subkey, default, _type, definition, values=None, locked = False ):
    """
    Create a new option.
    :param str key: First identifier of the option.
    :param str subkey: Second identifier of the option.
    :param default: Default value of the option (type varies).
    :param str _type: Type of the value of the option: [int, float, bool, text, string, path_in, path_out].
    :param str definition: String explaining the option.
    :param list values: Available values for the option.
    :param bool locked: If True, option cannot be altered.

    :raise: KeyError if 'key' or 'subkey' already define an option

    """
    eval( default, _type )
    _key    = key.lower()
    _subkey = subkey.lower()
    if not _has_primary_key( _key ) or not _has_secondary_key( _key, _subkey ):
        new_opt = pd.Series([key, subkey, default, _type, default, locked, definition, values], index=_columns)
        global _global_config
        _global_config = _global_config.append(new_opt, ignore_index = True)
    else:
        raise KeyError("{0}.{1} option is already registered".format(_key, _subkey))

def get_option( key, subkey ):
    """
    Get the current value of the option.
    :param str key: First identifier of the option.
    :param str subkey: Second identifier of the option.
    :return: Current value of the option (type varies).

    :raise: KeyError if 'key' or 'subkey' do not define any option
    """
    _key    = key.lower()
    _subkey = subkey.lower()
    if not _has_secondary_key( _key, _subkey ):
        raise KeyError("{0}.{1} option is not registered".format(_key, _subkey))
    else:
        df = _secondary_df( _key, _subkey )
        if df["type"].values[0] == "bool":
            return bool( df["value"].values[0] )
        elif df["type"].values[0] == "int":
            return int( df["value"].values[0] )
        else:
            return df["value"].values[0]

def get_option_default( key, subkey ):
    """
    Get the default value of the option.
    :param str key: First identifier of the option.
    :param str subkey: Second identifier of the option.
    :return: Defaulf value of the option (type varies).

    :raise: KeyError if 'key' or 'subkey' do not define any option.
    """
    _key    = key.lower()
    _subkey = subkey.lower()
    if not _has_secondary_key( _key, _subkey ):
        raise KeyError("{0}.{1} option is not registered".format(_key, _subkey))
    else:
        df = _secondary_df( _key, _subkey )
        if df["type"].values[0] == "bool":
            return bool( df["default"].values[0] )
        elif df["type"].values[0] == "int":
            return int( df["default"].values[0] )
        else:
            return df["default"].values[0]

def get_option_description( key, subkey ):
    """
    Get the string descriving a particular option.
    :param str key: First identifier of the option.
    :param str subkey: Second identifier of the option.
    :return: String description of the option.

    :raise: KeyError if 'key' or 'subkey' do not define any option.
    """
    _key    = key.lower()
    _subkey = subkey.lower()
    if not _has_secondary_key( _key, _subkey ):
        raise KeyError("{0}.{1} option is not registered".format(_key, _subkey))
    else:
        df = _secondary_df( _key, _subkey )
        return df["description"].values[0]

def get_option_alternatives( key, subkey ):
    """
    Get list of available values for an option.
    :param str key: First identifier of the option.
    :param str subkey: Second identifier of the option.
    :return: List with alternatives or None if field is open.

    :raise: KeyError if 'key' or 'subkey' do not define any option.
    """
    _key    = key.lower()
    _subkey = subkey.lower()
    if not _has_secondary_key( _key, _subkey ):
        raise KeyError("{0}.{1} option is not registered".format(_key, _subkey))
    else:
        df = _secondary_df( _key, _subkey )
        return df["values"].values[0]

def set_option( key, subkey, value ):
    """
    Sets the value of an option
    :param str key: First identifier of the option.
    :param str subkey: Second identifier of the option.
    :param value: New value for the option (type varies).

    :raise: KeyError if 'key' or 'subkey' do not define any option.
    :raise: ValueError if the targeted obtion is locked.
    :raise: ValueError if the provided value is not the expected type for the option.
    """
    _key    = key.lower()
    _subkey = subkey.lower()
    if not _has_secondary_key( _key, _subkey ):
        raise KeyError("{0}.{1} option is not registered".format(_key, _subkey))
    else:
        df = _secondary_df( _key, _subkey )
        if df["locked"].values[0]:
            raise ValueError("{0}.{1} option is locked".format(_key, _subkey))
        eval( value, df["type"].values[0] )
        if df["values"].values[0] is not None:
            if value not in df["values"].values[0]:
                raise ValueError("{0}.{1} accepted options are: ".format(_key, _subkey, ",".join(df["values"].values[0])))
        global _global_config
        _global_config.loc[
            ( _global_config["primary-key"] == _key ) &
            ( _global_config["secondary-key"] == _subkey), "value" ] = value

def reset_option( key, subkey ):
    """
    Resets a single option to the default values.
    :param str key: First identifier of the option.
    :param str subkey: Second identifier of the option.

    :raise: KeyError if 'key' or 'subkey' do not define any option.
    :raise: ValueError if the targeted obtion is locked.
    """
    _key = key.lower()
    _subkey = subkey.lower()
    if not _has_secondary_key( _key, _subkey ):
        raise KeyError("{0}.{1} option is not registered".format(_key, _subkey))
    else:
        df = _secondary_df( _key, _subkey )
        if df["locked"].values[0]:
            raise ValueError("{0}.{1} option is locked".format(_key, _subkey))
        global _global_config
        _global_config.loc[
            ( _global_config["primary-key"] == _key ) &
            ( _global_config["secondary-key"] == _subkey), "value" ] = df["default"].values[0]

def lock_option( key, subkey ):
    """
    Make an option unmutable.
    :param str key: First identifier of the option.
    :param str subkey: Second identifier of the option.
    """
    _key = key.lower()
    _subkey = subkey.lower()
    if not _has_secondary_key( _key, _subkey ):
        raise KeyError("{0}.{1} option is not registered".format(_key, _subkey))
    else:
        global _global_config
        _global_config.loc[
            ( _global_config["primary-key"] == _key ) &
            ( _global_config["secondary-key"] == _subkey), "locked" ] = True

def show_options( key = "" ):
    """
    Returns a copy the options :py:class:`.DataFrame`. Called on jupyter notebook,
    it will print them in pretty :py:class:`.DataFrame` format.
    :param str key: If provided, it will return only those options whose first
        key is 'key'.
    """
    global _global_config
    if key == "":
        return _global_config.copy()
    return _primary_df( key )

def reset_options():
    """
    Empty ALL options.
    """
    global _global_config
    _global_config = pd.DataFrame( columns = _columns )

def set_options_from_YAML( filename ):
    """
    Load options from a YAML-formated file.
    :param str filename: File from which to load the options.
    """
    if not os.path.isfile( filename ):
        raise IOError( "File {0} not found".format( filename ) )
    stream    = open( filename )
    data_dict = yaml.load(stream)
    set_options_from_dict( data_dict )

def set_options_from_JSON( filename ):
    """
    Load options from a YAML-formated file.
    :param str filename: File from which to load the options.
    """
    if not os.path.isfile( filename ):
        raise IOError( "File {0} not found".format( filename ) )
    data_dict = json.loads("".join([ x.strip() for x in open(filename).readlines() ]))
    set_options_from_dict( data_dict )

def set_options_from_dict( data_dict ):
    """
    Load options from a dictionary.
    :param dict data_dict: Dictionary with the options to load.
    """
    for k in data_dict:
        if not isinstance( data_dict[k], dict ):
            raise ValueError("The input data has to be a dictionary of dictionaries")
        for sk in data_dict[k]:
            if isinstance( data_dict[k][sk], unicode ):
                data_dict[k][sk] = str(data_dict[k][sk])
            data_dict[k][sk] = cast( data_dict[k][sk], _secondary_df( k, sk )[["type"]].values[0] )
            if get_option( k, sk ) != data_dict[k][sk]:
                set_option( k, sk, data_dict[k][sk] )

def write_options_to_YAML( filename ):
    """
    Writes the options in YAML format to a file.
    :param str filename: Target file to write the options.
    """
    fd = open( filename, "w" )
    yaml.dump( _options_to_dict(), fd, default_flow_style=False )
    fd.close()

def write_options_to_JSON( filename ):
    """
    Writes the options in JSON format to a file.
    :param str filename: Target file to write the options.
    """
    fd = open( filename, "w" )
    fd.write( json.dumps( _options_to_dict(), indent=2, separators=(',', ': ') ) )
    fd.close()
