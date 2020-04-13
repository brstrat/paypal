import functools
import urlparse
import time
import hmac
import hashlib
import base64
import re
from collections import OrderedDict


class MixedMethod(object):
    """ Decorator for method that can receive either the instance or the class
        as the first argument

        Usage::

            class AdaptivePayments(object):
                @mixedmethod
                def pay(self, ...):
                    # self may be AdaptivePayments or AdaptivePayments()

            AdaptivePayments.pay()  # self is class
            AdaptivePayments().pay()  # self is instance

    """
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, cls):
        @functools.wraps(self.func)
        def wrapper(*args, **kwargs):
            return self.func(instance or cls, *args, **kwargs)

        return wrapper

mixedmethod = MixedMethod


def oauth_header(consumer_key, consumer_secret, token, token_secret, http_method, url):

    timestamp = int(time.time())
    key = '{consumer_secret}&{token_secret}'.format(
        consumer_secret=consumer_secret,
        token_secret=oauth_encode(token_secret)
    )

    params = '&'.join(
        '{}={}'.format(key, value)
        for key, value in [
            ('oauth_consumer_key', consumer_key),
            ('oauth_signature_method', 'HMAC-SHA1'),
            ('oauth_timestamp', timestamp),
            ('oauth_token', token),
            ('oauth_version', '1.0'),
        ]
    )

    raw = '{http_method}&{url}&{params}'.format(
        http_method=http_method,
        url=oauth_encode(url),
        params=oauth_encode(params)
    )

    hashed = hmac.new(str(key), str(raw), hashlib.sha1)
    signature = base64.b64encode(hashed.digest())

    return {
        'X-PP-AUTHORIZATION': 'token={token},signature={signature},timestamp={timestamp}'.format(
            timestamp=timestamp,
            token=token,
            signature=signature,
        ),
    }


oauth_encode_re = re.compile(r'([A-Za-z0-9_ ]+)')


def oauth_encode(raw):
    translate = {' ': '+'}
    return ''.join(
        "%" + hex(ord(c))[2:] if not re.match(oauth_encode_re, c) else translate.get(c, c)
        for c in raw
    )


def parse_nvp(nvp):
    """ Parse a name-value-pair response into a dictionary """
    return OrderedDict(urlparse.parse_qsl(nvp))


nvp_array_re = re.compile('^(?P<key>L_.*\D)(?P<index>\d+)$')
