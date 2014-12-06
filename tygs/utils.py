
import encodings

SUPPORTED_ENCODING = set(list(encodings.aliases.aliases.keys()) +
                         list(encodings.aliases.aliases.values()))

class TygsError(Exception):
    pass

class TygsEncodingError(TygsError):
    pass

def raise_on_unsupported_encoding(encoding):
    """ Raises an exception if the encoding is not supported by Python. """
    if encoding not in SUPPORTED_ENCODING:
        msg = ("'%s' is not a supported encoding. Import 'encodings' and "
               "check 'encodings.aliases.aliases' for supported encodings.")
        raise TygsEncodingError(msg % encoding)


def do_nothing(*args, **kwargs):
    """ Take any arguments and do nothing """
    pass