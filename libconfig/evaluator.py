# -*-
# @project: libconfig
# @file:    evaluator.py
#
# @author: jaume.bonet
# @email:  jaume.bonet@gmail.com
# @url:    jaumebonet.cat
#
# @date:   2017-10-03 15:19:32
#
# @Last modified by:   bonet
# @Last modified time: 12-Oct-2017
#
# -*-
import os
from pandas.core.config import (is_int, is_float, is_bool, is_text)

def is_path( value ):
    if not os.path.isfile( value ) or os.path.isdir( value ):
        msg = "Value must be an instance of {type_repr}"
        raise ValueError(msg.format(type_repr="path"))


_TYPES = {
    "int": is_int,      "float": is_float, "bool":is_bool,
    "text": is_text,    "string": is_text,
    "path_in": is_path, "path_out": is_text
}


def eval( value, _type ):
    _type = _type.lower()
    if _type not in _TYPES:
        raise KeyError( "{0} is not a known value type; accepted are {1}".format(_type, ",".join(_TYPES.keys() ) ) )

    return _TYPES[_type]( value )

def cast( value, _type ):
    if _type == "bool":
        return bool( value )
    if _type == "int":
        return int( value )
    return value
