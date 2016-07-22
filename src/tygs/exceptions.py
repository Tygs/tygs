

class TygsError(Exception):
    pass


class HttpRequestControllerError(TygsError):
    pass


class HttpResponseControllerError(TygsError):
    pass


class TestClientError(TygsError):
    pass


class RoutingError(TygsError):
    pass
