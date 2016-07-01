

class TygsError(Exception):
    pass


class HttpRequestControllerError(TygsError):
    pass


class HttpResponseControllerError(TygsError):
    pass
