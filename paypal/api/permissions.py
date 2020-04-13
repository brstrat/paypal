""" https://developer.paypal.com/docs/classic/permissions-service/gs_PermissionsService/ """
from . import PaypalJSONAPIRequest, PaypalJSONAPIResponse, PaypalAPIError
from ..utils import mixedmethod


__all__ = [
    'Permissions', 'PermissionsError', 'RequestPermissionsResponse',
    'GetAccessTokenResponse', 'GetPermissionsResponse',
    'CancelPermissionsResponse'
]


class PermissionsError(PaypalAPIError):
    pass


class Permissions(PaypalJSONAPIRequest):

    class Scope:
        TRANSACTION_SEARCH = 'TRANSACTION_SEARCH'
        GET_TRANSACTION_DETAILS = 'TRANSACTION_DETAILS'

    @mixedmethod
    def headers(self):
        return {
            'X-PAYPAL-SECURITY-USERID': self.configuration.userid,
            'X-PAYPAL-SECURITY-PASSWORD': self.configuration.password,
            'X-PAYPAL-SECURITY-SIGNATURE': self.configuration.signature,

            'X-PAYPAL-APPLICATION-ID': self.configuration.application_id,

            'X-PAYPAL-REQUEST-DATA-FORMAT': 'JSON',
            'X-PAYPAL-RESPONSE-DATA-FORMAT': 'JSON',
        }

    @mixedmethod
    def request_permissions(self, scope, callback):
        url = self.config.environment.Permissions.request_permissions_endpoint

        payload = {
            'scope': scope,
            'callback': callback,
        }

        response = self.post(url, data=payload)

        return RequestPermissionsResponse(self.config, response)

    @mixedmethod
    def get_access_token(self, token, verifier):
        url = self.config.environment.Permissions.get_access_token_endpoint

        payload = {
            'token': token,
            'verifier': verifier,
        }

        response = self.post(url, data=payload)

        return GetAccessTokenResponse(self.config, response)

    @mixedmethod
    def get_permissions(self, token):
        url = self.config.environment.Permissions.get_permissions_endpoint

        payload = {
            'token': token,
        }

        response = self.post(url, data=payload)

        return GetPermissionsResponse(self.config, response)

    @mixedmethod
    def cancel_permissions(self, token):
        url = self.config.environment.Permissions.cancel_permissions_endpoint

        payload = {
            'token': token,
        }

        response = self.post(url, data=payload)

        return CancelPermissionsResponse(self.config, response)


class RequestPermissionsResponse(PaypalJSONAPIResponse):

    _required_fields = ('token',)

    @property
    def token(self):
        return self.response['token']

    @property
    def redirect(self):
        return '{url}&request_token={token}'.format(
            url=self.config.environment.Permissions.grant_permission_redirect,
            token=self.token
        )


class GetAccessTokenResponse(PaypalJSONAPIResponse):

    _required_fields = ('token', 'token_secret')

    @property
    def token(self):
        return self.response['token']

    @property
    def token_secret(self):
        return self.response['tokenSecret']


class GetPermissionsResponse(PaypalJSONAPIResponse):

    _required_fields = ('scope',)

    @property
    def scope(self):
        return self.response['scope']


class CancelPermissionsResponse(PaypalJSONAPIResponse):
    pass
