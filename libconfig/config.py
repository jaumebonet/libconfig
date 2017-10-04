# -*-
# @project: libconfig
# @file:    config.py
#
# @author: jaume.bonet
# @email:  jaume.bonet@gmail.com
# @url:    jaumebonet.cat
#
# @date:   2017-10-03 14:59:01
#
# @last modified by:   jaume.bonet
# @last modified time: 2017-10-04 10:00:16
#
# -*-
import json
import os

import pandas as pd
import yaml

from evaluator import eval

_columns = [ "primary-key", "secondary-key",
             "value", "type", "default", "locked" ]

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
    pass

def register_option( key, subkey, default, _type, locked = False ):
    eval( default, _type )
    _key    = key.lower()
    _subkey = subkey.lower()
    if not _has_primary_key( _key ) or not _has_secondary_key( _key, _subkey ):
        new_opt = pd.Series([key, subkey, default, _type, default, locked], index=_columns)
        global _global_config
        _global_config = _global_config.append(new_opt, ignore_index = True)
    else:
        raise KeyError("{0}.{1} option is already registered".format(_key, _subkey))

def get_option( key, subkey ):
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

def set_option( key, subkey, value ):
    _key = key.lower()
    _subkey = subkey.lower()
    if not _has_secondary_key( _key, _subkey ):
        raise KeyError("{0}.{1} option is not registered".format(_key, _subkey))
    else:
        df = _secondary_df( _key, _subkey )
        eval( value, df["type"].values[0] )
        if df["locked"].values[0]:
            raise ValueError("{0}.{1} option is locked".format(_key, _subkey))
        global _global_config
        _global_config.loc[
            ( _global_config["primary-key"] == _key ) &
            ( _global_config["secondary-key"] == _subkey), "value" ] = value


def reset_option( key, subkey ):
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
    global _global_config
    if key == "":
        return _global_config.copy()
    return _primary_df( key )

def reset_options():
    global _global_config
    _global_config = pd.DataFrame( columns = _columns )

def set_options_from_YAML( filename ):
    if not os.path.isfile( filename ):
        raise IOError( "File {0} not found".format( filename ) )
    stream    = open( filename )
    data_dict = yaml.load(stream)
    set_options_from_dict( data_dict )

def set_options_from_JSON( filename ):
    if not os.path.isfile( filename ):
        raise IOError( "File {0} not found".format( filename ) )
    data_dict = json.loads("".join([ x.strip() for x in open(filename).readlines() ]))
    set_options_from_dict( data_dict )

def set_options_from_dict( data_dict ):
    for k in data_dict:
        if not isinstance( data_dict[k], dict ):
            raise ValueError("The input data has to be a dictionary of dictionaries")
        for sk in data_dict[k]:
            set_option( k, sk, data_dict[k][sk] )

def write_options_to_YAML( filename ):
    pass

def write_options_to_JSON( filename ):
    pass
