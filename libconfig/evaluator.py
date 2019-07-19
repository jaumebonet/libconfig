# -*-
# @project: libconfig
# @file:    evaluator.py
#
# @author: jaume.bonet
# @email:  jaume.bonet@gmail.com
# @url:    jaumebonet.cat
#
# @date:   2017-10-03 15:19:32
# @Last modified time: 05-Feb-2019
#
# -*-
import os
try:
    # up until pandas 0.24.2
    from pandas.core.config import (is_int, is_float, is_bool, is_text)
except ImportError:
    # from pandas 0.25.0
    from pandas._config.config import (is_int, is_float, is_bool, is_text)

__all__ = ["value_eval", "cast"]


def is_path(value):
    if value is not None:
        if not os.path.isfile(value) and not os.path.isdir(value):
            msg = "Value must be an instance of {type_repr}"
            raise IOError(msg.format(type_repr="path"))


_TYPES = {
    "int": is_int,      "float": is_float, "bool": is_bool,
    "text": is_text,    "string": is_text,
    "path_in": is_path, "path_out": is_text
}


def value_eval(value, _type):
    _type = _type.lower()
    if _type not in _TYPES:
        info = "{} is not a known value type;".format(_type)
        info += "accepted are {}".format(",".join(_TYPES.keys()))
        raise KeyError(info)

    return _TYPES[_type](value)


def cast(value, _type):
    if _type == "bool":
        return bool(value)
    if _type == "int":
        return int(value)
    return value
