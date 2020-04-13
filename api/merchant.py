from . import PaypalNVPAPIRequest, PaypalNVPAPIResponse, PaypalAPIError
from ..utils import mixedmethod, oauth_header


__all__ = [
    'Merchant', 'MerchantError', 'TransactionSearchResponse',
]


class MerchantError(PaypalAPIError):
    pass


class Merchant(PaypalNVPAPIRequest):

    @mixedmethod
    def headers(self):
        return {
            #'X-PAYPAL-SECURITY-USERID': self.configuration.userid,
            #'X-PAYPAL-SECURITY-PASSWORD': self.configuration.password,
            #'X-PAYPAL-SECURITY-SIGNATURE': self.configuration.signature,

            #'X-PAYPAL-APPLICATION-ID': self.configuration.application_id,
        }

    @mixedmethod
    def transaction_search(
        self, token, token_secret,
        start_date=None, end_date=None,
        email=None, receiver=None,
        transaction_id=None, inv_num=None,
    ):
        url = self.config.environment.Merchant.merchant_endpoint

        payload = {
            'METHOD': 'TransactionSearch',
            'VERSION': '119',

            'STARTDATE': start_date.isoformat() if start_date is not None else None,
            'ENDDATE': end_date.isoformat() if end_date is not None else None,

            'EMAIL': email,
            'RECEIVER': receiver,

            'TRANSACTIONID': transaction_id,
            'INVNUM': inv_num,
        }

        headers = oauth_header(
            self.configuration.userid,
            self.configuration.password,
            token,
            token_secret,
            'POST',
            url,
        )

        response = self.post(url, data=payload, headers=headers)

        return TransactionSearchResponse(self.config, response)

    @mixedmethod
    def transaction_details(
        self, token, token_secret,
        transaction_id
    ):

        url = self.config.environment.Merchant.merchant_endpoint

        payload = {
            'METHOD': 'GetTransactionDetails',
            'VERSION': '119',

            'TRANSACTIONID': transaction_id,
        }

        headers = oauth_header(
            self.configuration.userid,
            self.configuration.password,
            token,
            token_secret,
            'POST',
            url,
        )

        response = self.post(url, data=payload, headers=headers)

        return TransactionDetailsResponse(self.config, response)


class TransactionSearchResponse(PaypalNVPAPIResponse):

    @property
    def transactions(self):
        """ Generates transaction dicts based on zipped arrays in the response """
        return self.zipped_response()


class TransactionDetailsResponse(PaypalNVPAPIResponse):
    pass
