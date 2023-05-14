import json
from optparse import Option


class KVOptionException(Exception):
    pass


class KVOption(Option):

    def __init__(self, *ops, **kwargs):
        if 'action' in kwargs:
            raise KVOptionException("action argument must not be passed.  It is ignored")
        Option.__init__(self, *ops, **kwargs)

    def take_action(self, action, dest, opt, value, values, parser):
        try:
            key, val = value.split(sep="=", maxsplit=1)
            values.ensure_value(dest, {})
            if key in values.ensure_value(dest, {}):
                raise KVOptionException("{value} key value has a duplicate")

            if val.startswith('['):
                val = json.loads(val)
            elif val.startswith('file:'):
                with open(val.replace("file:", ""), 'r') as thefile:
                    val = thefile.read()

            values.ensure_value(dest, {})[key] = val
        except ValueError as ve:
            raise KVOptionException(f"argument passed '{val}' "
                                    f"must be of format key=value. \n {ve}")
        except FileNotFoundError as fne:
            raise KVOptionException(f"file argument passed '{val}' "
                                    f"can't be found. \n {fne}")
