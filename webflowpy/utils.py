import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from webflowpy import settings
from webflowpy.log import logger
from webflowpy.WebflowResponse import WebflowResponse


class CallbackRetry(Retry):
    def __init__(self, *args, **kwargs):
        self._callback = kwargs.pop("callback", None)
        super(CallbackRetry, self).__init__(*args, **kwargs)

    def new(self, **kw):
        # pass along the subclass additional information when creating
        # a new instance.
        kw["callback"] = self._callback
        return super(CallbackRetry, self).new(**kw)

    def increment(self, method, url, *args, **kwargs):
        if self._callback:
            try:
                if kwargs["_pool"].num_requests == 1:
                    next_try = 0
                else:
                    next_try = settings.backoff_factor * (
                        2 ** (kwargs["_pool"].num_requests - 2)
                    )

                logger.warn(
                    "Unsuccessful request, try {}/{}. Next try in {} seconds".format(
                        kwargs["_pool"].num_requests, settings.retries + 1, next_try
                    )
                )
                self._callback(url, method, kwargs)
            except Exception as e:
                logger.warn(f"Callback raised an exception ({e!r}), ignoring")
        return super(CallbackRetry, self).increment(method, url, *args, **kwargs)


def retry_callback(url, method, kwargs):
    kwargs["response"].url = url
    kwargs["response"].method = method
    WebflowResponse(kwargs["response"])


def requests_retry_session(
    retries=settings.retries,
    backoff_factor=settings.backoff_factor,
    status_forcelist=(500, 429),
    session=None,
):
    session = session or requests.Session()
    retry = CallbackRetry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        callback=retry_callback,
        # Allow retrying dangerous methods (POST/PATCH) because the errors are
        # rate limits, so it is safe to retry.
        allowed_methods={'GET', 'POST', 'PUT', 'PATCH', 'DELETE'},
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
