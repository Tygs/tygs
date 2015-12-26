

from collections import namedtuple

FrozenHttpResponse = namedtuple('FrozenHttpResponse',
                                ['status', 'reason', 'content_type',
                                 'charset', 'headers', 'body'])


def template_renderer(response):
    template_engine = response.request.app.components['templates']
    body = template_engine.render(response.template, response.data)
    body = body.encode(response.charset)

    # TODO: maybe it can be just a dict
    return FrozenHttpResponse(
        status=response.status,
        reason=response.reason,
        content_type=response.content_type,
        charset=response.charset,
        # TODO: update default heaers
        headers=response.headers,
        body=body
    )

