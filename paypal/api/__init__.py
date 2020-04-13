import itertools
import json
import logging
from collections import OrderedDict

import requests

from ..configuration import Configuration
from ..exceptions import PaypalError
from ..utils import mixedmethod, parse_nvp, nvp_array_re


__all__ = [
    'PaypalAPIError',
    'PaypalJSONAPIRequest', 'PaypalNVPAPIRequest',
    'PaypalJSONAPIResponse', 'PaypalNVPAPIResponse',
]


class PaypalAPIError(PaypalError):
    pass


class PaypalAPIMeta(type):
    @property
    def configuration(cls):
        """ Classproperty for PaypalAPI.configuration """
        if not cls._configuration:
            cls._configuration = Configuration.instantiate()
        return cls._configuration

    @property
    def config(cls):
        """ Alias for PaypalAPI.configuration """
        return cls.configuration


class PaypalAPI(object):
    __metaclass__ = PaypalAPIMeta
    """ Abstract class for PayPal API method subclasses

    Allows instantiation with specific configuration instance,
    or using classmethods for global configuration::

        # Use global configuration
        >>> PaypalAPI.config
        <PaypalConfiguration ... >

        >>> PaypalAPI.pay()

        # Use instance configuration
        >>> PaypalAPI(config).config
        <PaypalConfiguration ... >

        >>> PaypalAPI(config).pay()

    Since methods in this class can be called as either classmethods
    or instancemethods, most should be wrapped in @mixedmethod decorator

    """

    _configuration = None

    def __init__(self, configuration=None):
        super(PaypalAPI, self).__init__()
        self._configuration = configuration

    @property
    def configuration(self):
        """ Instance property for PaypalAPI().configuration """
        if not self._configuration:
            self._configuration = Configuration.instantiate()
        return self._configuration

    @property
    def config(self):
        """ Alias for PaypalAPI().configuration """
        return self.configuration


class PaypalAPIRequest(PaypalAPI):
    """ Wrapper around an API request to Paypal

    Provides access to http wrappers for posting with data and headers

    Subclasses should expose specific methods to API endpoints
    """

    @mixedmethod
    def encode_data(self, data):
        return NotImplemented

    @mixedmethod
    def headers(self):
        return {}

    @mixedmethod
    def post(self, url, data=None, headers=None, **kwargs):
        """ POSTs to the PayPal API url provided, sending along the data,
        and any required headers

        `data` values of `None` will be stripped before being sent

        `headers` passed in will be added to the standard headers

        Returns the response as a json object
        """

        if data is None:
            data = {}
        final_data = {k: v for k, v in data.items() if v is not None}

        final_headers = {}
        final_headers.update(self.headers())
        if headers is not None:
            final_headers.update(headers)

        response = requests.post(
            url,
            data=self.encode_data(final_data),
            headers=final_headers,
            **kwargs
        )
        return response


class PaypalJSONAPIRequest(PaypalAPIRequest):

    @mixedmethod
    def encode_data(self, data):
        return json.dumps(data)


class PaypalNVPAPIRequest(PaypalAPIRequest):

    @mixedmethod
    def encode_data(self, data):
        return data


class PaypalAPIResponse(PaypalAPI):
    """ Wrapper around an API response from Paypal

    Contains the response object, the `correlationId` and `timestamp`, and a
    possible redirect url to provide to the sender to confirm the action

    Subclasses can expose additional properties

    `PaypalAPIResponse` is always instantiated, so `@mixedmethod` decorators
    are not required
    """

    response = None

    def __init__(self, configuration=None, response=None):
        super(PaypalAPIResponse, self).__init__(configuration=configuration)

        if response:
            self.response = self.parse_response(response)

            if not self.success:
                logging.error('Error in paypal response: {}'.format(self.response))
            else:
                logging.debug('Successful paypal response: {}'.format(self.response))

            # Required by Paypal to log these two values
            logging.info('correlationId {}'.format(self.correlation_id))
            logging.info('timestamp {}'.format(self.timestamp))

    def parse_response(self, response):
        return NotImplemented

    @property
    def ack(self):
        return NotImplemented

    @property
    def correlation_id(self):
        return NotImplemented

    @property
    def timestamp(self):
        return NotImplemented

    @property
    def success(self):
        return self.ack == 'Success'

    def validate(self, keys=None):
        """ Verify the presence of `keys` (but not values)
        in the response dictionary

        """
        if not self.response:
            return

        if keys is None:
            keys = []

        try:
            for key in keys:
                getattr(self, key)
        except KeyError as e:
            logging.debug(self.response)
            logging.debug("KeyError: {}".format(e.message))
            raise PaypalAPIError(
                'Failed parsing PayPal response'
            )

    @property
    def redirect(self):
        """ Return a url if the client should be redirected to authorize this
        action

        Return a Falsy value if no redirect is needed

        Usage::

            response = PaypalAPIResponse(...)
            if response.redirect:
                # redirect to paypal
                return HttpResponseRedirect(response.redirect)
            else:
                # no need to redirect
        """
        return ''


class PaypalJSONAPIResponse(PaypalAPIResponse):

    def __init__(self, *args, **kwargs):
        super(PaypalJSONAPIResponse, self).__init__(*args, **kwargs)

        self.validate(['response_envelope', 'ack', 'correlation_id', 'timestamp'])

    def parse_response(self, response):
        try:
            return response.json()
        except AttributeError:
            return response

    @property
    def response_envelope(self):
        return self.response['responseEnvelope']

    @property
    def ack(self):
        return self.response_envelope['ack']

    @property
    def correlation_id(self):
        return self.response_envelope['correlationId']

    @property
    def timestamp(self):
        return self.response_envelope['timestamp']


class PaypalNVPAPIResponse(PaypalAPIResponse):

    def __init__(self, *args, **kwargs):
        super(PaypalNVPAPIResponse, self).__init__(*args, **kwargs)

        self.validate(['ack', 'correlation_id', 'timestamp'])

    def parse_response(self, response):
        return parse_nvp(response.content)

    _collapsed_response = None

    @property
    def collapsed_response(self):
        """ Returns a new response dictionary with arrays moved into
        lists keyed on the common key name

        Non-array keys are untouched

        Given::

            response = {
                'CORRELATIONID': 0,
                'L_TRANSACTIONID0': 1,
                'L_TRANSACTIONID1': 2,
                'L_TIMESTAMP0': 3,
                'L_TIMESTAMP1': 4,
            }

        Return::

            collapsed_response = {
                'CORRELATIONID': 0,
                'L_TRANSACTIONID': [1, 2],
                'L_TIMESTAMP': [3, 4],
            }

        Note:: Assumes that the input NVP response order has been retained.
        (i.e. the key `L_TRANSACTIONID0` comes before `L_TRANSACTIONID1`)

        Returns an ordered dict with the same order
        """
        if self._collapsed_response is None:
            collapsed_response = OrderedDict()
            for key, value in self.response.iteritems():
                match = nvp_array_re.match(key)
                if match:
                    key, index = match.groups()

                    if key not in collapsed_response:
                        collapsed_response[key] = []

                    keys = len(collapsed_response[key])

                    if int(index) < keys:
                        # E.g. we've hit a key like L_TRANSACTIONID2 after hitting a key like L_TRANSACTIONID3
                        raise IndexError('Index mismatch parsing NVP response, perhaps lost order?')

                    if int(index) > keys:
                        # E.g. we've hit a key like L_TRANSACTIONID2 without hitting a key like L_TRANSACTIONID1
                        # Assume L_TRANSACTIONID1 is missing and pad with None
                        collapsed_response[key].extend([None] * (int(index) - keys))

                    collapsed_response[key].append(value)

                else:
                    # Not an array
                    collapsed_response[key] = value

            self._collapsed_response = dict(collapsed_response)

        return self._collapsed_response

    def zipped_response(self):
        """ Zips the arrays in the response and generates a dictionary
        for each element, using the keys for that array.

        Given::

            response = {
                'CORRELATIONID': 0,
                'L_TRANSACTIONID0': 1,
                'L_TRANSACTIONID1': 2,
                'L_TIMESTAMP0': 3,
                'L_TIMESTAMP1': 4,
            }

        Generate::

            zipped_response = [
                {'TRANSACTIONID': 0, 'TIMESTAMP': 3},
                {'TRANSACTIONID': 1, 'TIMESTAMP': 4},
            ]

        """
        # Get only the keys that hold arrays
        transaction_keys = tuple(
            key.lstrip('L_')
            for key, value
            in self.collapsed_response.iteritems()
            if isinstance(value, list)
        )

        # Zip the values of those arrays
        transaction_values = itertools.izip(*(
            value
            for value
            in self.collapsed_response.itervalues()
            if isinstance(value, list)
        ))

        # Zip those keys and values into dicts
        for keys, values in itertools.izip(
            itertools.repeat(transaction_keys),
            transaction_values
        ):
            yield dict(itertools.izip(keys, values))

    @property
    def ack(self):
        return self.response['ACK']

    @property
    def correlation_id(self):
        return self.response['CORRELATIONID']

    @property
    def timestamp(self):
        return self.response['TIMESTAMP']
