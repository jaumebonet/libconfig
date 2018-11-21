# @Author: Jaume Bonet <bonet>
# @Date:   04-Apr-2018
# @Email:  jaume.bonet@gmail.com
# @Filename: util.py
# @Last modified by:   bonet
# @Last modified time: 21-Nov-2018


from functools import wraps


__all__ = ["lower_keynames", "entry_must_exist", "entry_must_not_exist"]


def lower_keynames(func):
    """
    *Decorator* to lowercase string attributes.

    The decorated function will have the first two arguments
    (or arguments ``key`` and ``subkey``) lowercased.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        new_args = []
        for i, _ in enumerate(args):
            if i < 2:
                new_args.append(_.lower())
            else:
                new_args.append(_)
        if 'key' in kwargs:
            kwargs['key'] = kwargs['key'].lower()
            kwargs['subkey'] = kwargs['subkey'].lower()
        return func(*new_args, **kwargs)
    return wrapper


def entry_must_exist(func):
    """
    *Decorator* to evaluate key-subkey existence.

    Checks that the key-subkey combo exists in the
    configuration options.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        from .config import _global_config as cfg
        k1 = kwargs['key'] if 'key' in kwargs else args[0]
        k2 = kwargs['subkey'] if 'subkey' in kwargs else args[1]
        count = cfg[(cfg['primary-key'] == k1) &
                    (cfg['secondary-key'] == k2)].shape[0]
        if count == 0:
            raise KeyError("Option {0}.{1} not registered".format(k1, k2))
        return func(*args, **kwargs)
    return wrapper


def entry_must_not_exist(func):
    """
    *Decorator* to evaluate key-subkey non-existence.

    Checks that the key-subkey combo does not exists in the
    configuration options.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        from .config import _global_config as cfg
        k1 = kwargs['key'] if 'key' in kwargs else args[0]
        k2 = kwargs['subkey'] if 'subkey' in kwargs else args[1]
        count = cfg[(cfg['primary-key'] == k1) &
                    (cfg['secondary-key'] == k2)].shape[0]
        if count > 0:
            raise KeyError("Option {0}.{1} already registered".format(k1, k2))
        return func(*args, **kwargs)
    return wrapper
