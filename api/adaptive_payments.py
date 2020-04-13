""" https://developer.paypal.com/docs/classic/adaptive-payments/ApiCallRefLanding/ """
import logging

from . import PaypalJSONAPIResponse, PaypalJSONAPIRequest
from . import PaypalAPIError
from ..utils import mixedmethod


__all__ = [
    'AdaptivePayments', 'AdaptivePaymentsError', 'PayResponse',
    'PreapprovalResponse', 'PaymentDetails', 'PreapprovalDetails',
    'Receiver'
]


class AdaptivePaymentsError(PaypalAPIError):
    pass


class AdaptivePayments(PaypalJSONAPIRequest):

    class ActionType:
        PAY = 'PAY'

    class CurrencyCode:
        USD = 'USD'

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
    def pay(
        self, receivers=None, customer_id=None,
        return_url=None, cancel_url=None, ipn_notification_url=None,
        memo=None, tracking_id=None, invoice_id=None,
        reverse_all_parallel_payments_on_error=None,
        preapproval_key=None, implicit=None
    ):
        """ Make a call to the PayPal adaptive payments Pay endpoint

        By default, the sender must be redirected after this request
        to authorize the purchase.  The redirect url can be found on the
        response object at `PayResponse.redirect`

        If `preapproval_key` is provided, then this sender has previously
        authorized this payment request, and no redirect is required.

        If `implicit` is `True`, then the API caller is also the sender,
        and no redirect is required (i.e. `Configuration.userid` is used
        as sender)

        In the above cases where no authorization redirect is required,
        transaction details are available immediately in the `PayResponse`

        If authorization is required, no transaction details are available
        in the response, and instead are sent to the url provided in
        `ipn_notification_url` once the sender completes authorization

        Usage::

            from decimal import Decimal
            from paypal import AdaptivePayment

            amount = Decimal('10.00')
            email = "receiver@receivemoney.com"

            response = AdaptivePayment.pay(amount, email)

            if response.redirect:
                # redirect sender

        """

        if not receivers:
            raise AdaptivePaymentsError('Receivers must not be empty')

        if Receiver.number_of_primary(receivers) > 1:
            raise AdaptivePaymentsError(
                'You can have maximum 1 primary receiver'
            )

        if len(receivers) > 6:
            raise AdaptivePaymentsError(
                'You can send to a maximum of 6 receivers'
            )

        if preapproval_key and implicit:
            raise AdaptivePaymentsError(
                'preapproval_key and implicit payment cannot be specified'
                'at the same time'
            )

        url = self.config.environment.AdaptivePayments.pay_endpoint

        payload = {
            'receiverList': {
                'receiver': [receiver.as_dict() for receiver in receivers]
            },

            # "https://devtools-paypal.com/guide/ap_preapprove_payment/php?success=true"
            'returnUrl': return_url,
            # "https://devtools-paypal.com/guide/ap_preapprove_payment/php?cancel=true"
            'cancelUrl': cancel_url,
            # "http://replaceIpnUrl.com"
            'ipnNotificationUrl': ipn_notification_url,

            # "Simple payment example."
            'memo': memo,
            # "<GUID>"
            'trackingId': tracking_id,

            # default False
            'reverseAllParallelPaymentsOnError': reverse_all_parallel_payments_on_error,

            'actionType': AdaptivePayments.ActionType.PAY,
            'currencyCode': AdaptivePayments.CurrencyCode.USD,
            'requestEnvelope': {
                'errorLanguage': 'en_US',
                'detailLevel': 'ReturnAll',
            },
        }

        if implicit:
            payload['senderEmail'] = self.config.userid

        if preapproval_key:
            payload['preapprovalKey'] = preapproval_key

        if customer_id:
            payload['clientDetails'] = {
                'customerId': customer_id,
            }

        response = self.post(url, data=payload)

        pay_response = PayResponse(self.config, response)

        if implicit or preapproval_key:
            # For approved payments, return transaction details directly
            if not pay_response.payment_details:
                pay_response.payment_details = self.payment_details(
                    pay_response.paykey
                )

        return pay_response

    @mixedmethod
    def pay_simple(self, email=None, amount=None, invoice_id=None, *args, **kwargs):
        """ Send a single payment to a single receiver

            sender -> receiver

            `email` can be a `Receiver` (in which case `amount` is ignored)

            Usage::

                pay_simple(email=..., amount=...)

                # or
                receiver = Receiver(email=..., amount=...)
                pay_simple(receiver)

        """
        receiver = email
        if not isinstance(receiver, Receiver):
            receiver = Receiver(email=email, amount=amount, invoice_id=invoice_id)

        return self.pay(receivers=[receiver], *args, **kwargs)

    @mixedmethod
    def pay_parallel(self, receivers=None, *args, **kwargs):
        """ Send a single payment to multiple receivers

            sender -> receivers

            Usage::

                receivers = [Receiver(email=..., amount=...), ...]
                pay_parallel(receivers)

        """
        return self.pay(receivers=receivers, *args, **kwargs)

    @mixedmethod
    def pay_chained(self, receivers=None, *args, **kwargs):
        """ Send a single payment to a primary receiver, who sends payments
            to secondary receivers

            sender -> primary receiver -> secondary receivers

            Usage::

                primary_receiver = [Receiver(email=..., amount=..., primary=True)]
                other_receivers = [Receiver(email=..., amount=...), ...]
                receivers = primary_receiver + other_receivers
                pay_chained(receivers)

        """
        if Receiver.number_of_primary(receivers) < 1:
            raise AdaptivePaymentsError(
                'You must specify one primary receiver to use chained payments '
                'with `Receiver.primary = True`'
            )
        return self.pay(receivers=receivers, *args, **kwargs)

    @mixedmethod
    def payment_details(
        self,
        paykey=None, tracking_id=None, transaction_id=None
    ):
        """ Retrieve payment details using a payKey or trackingId

            Usage::

                payment_details(paykey="...")
                payment_details(tracking_id="...")

            If `trasaction_id` is provided, only that transaction detail
            will be returned

        """
        url = self.config.environment.AdaptivePayments.payment_details_endpoint

        payload = {
            'payKey': paykey,
            'tackingId': tracking_id,
            'transactionId': transaction_id,

            'requestEnvelope': {
                'errorLanguage': 'en_US',
                'detailLevel': 'ReturnAll',
            }
        }

        response = self.post(url, data=payload)

        return PaymentDetails(self.config, response)

    @mixedmethod
    def preapproval(
        self, sender_email=None,
        return_url=None, cancel_url=None, ipn_notification_url=None,
        starting_date=None, ending_date=None,
        max_total_amount_of_all_payments=None,
        max_amount_per_payment=None, max_number_of_payments=None,
    ):
        """ Request preapproval authorization from a sender, to be able
            to send money on their behalf

            Leave `sender_email` empty to use whoever logs in to approval
            the preapproval as `sender_email`

            Usage::

                response = preapproval(...)

                if response.redirect:
                    # redirect sender

        """

        url = self.config.environment.AdaptivePayments.preapproval_endpoint

        payload = {
            # "platfo_1255077030_biz@gmail.com"
            'senderEmail': sender_email,

            # "https://devtools-paypal.com/guide/ap_preapprove_payment/php?success=true"
            'returnUrl': return_url,
            # "https://devtools-paypal.com/guide/ap_preapprove_payment/php?cancel=true"
            'cancelUrl': cancel_url,
            # "http://replaceIpnUrl.com"
            'ipnNotificationUrl': ipn_notification_url,

            # "2014-10-24"  (After today, before ending date)
            'startingDate': str(starting_date) if starting_date is not None else None,
            # "2015-10-24"  (Max: 1 year after starting date.  Contact PayPal to increase)
            'endingDate': str(ending_date) if ending_date is not None else None,

            # "5.0"  (Max: $2,000.  Contact PayPal to increase)
            'maxTotalAmountOfAllPayments': str(max_total_amount_of_all_payments) if max_total_amount_of_all_payments is not None else None,
            # "1.0"  (Max: maxTotalAmountOfAllPayments setting)
            'maxAmountPerPayment': str(max_amount_per_payment) if max_amount_per_payment is not None else None,
            # "5"
            'maxNumberOfPayments': str(max_number_of_payments) if max_number_of_payments is not None else None,

            'currencyCode': AdaptivePayments.CurrencyCode.USD,
            'requestEnvelope': {
                'errorLanguage': 'en_US',
                'detailLevel': 'ReturnAll',
            }
        }

        response = self.post(url, data=payload)

        preapproval_response = PreapprovalResponse(self.config, response)

        return preapproval_response

    @mixedmethod
    def preapproval_details(self, preapprovalkey):
        """ Retrieve preapproval details using a preapprovalKey

            Usage::

                preapproval_details(preapprovalkey="...")

        """
        url = self.config.environment.AdaptivePayments.preapproval_details_endpoint

        payload = {
            'preapprovalKey': preapprovalkey,

            'requestEnvelope': {
                'errorLanguage': 'en_US',
                'detailLevel': 'ReturnAll',
            }
        }

        response = self.post(url, data=payload)

        return PreapprovalDetails(self.config, response)

    @mixedmethod
    def cancel_preapproval(self, preapprovalkey):
        """ Cancel a preapproval using a preapprovalKey

            Usage::

                cancel_preapproval(preapprovalkey="...")

        """
        url = self.config.environment.AdaptivePayments.cancel_preapproval_endpoint

        payload = {
            'preapprovalKey': preapprovalkey,

            'requestEnvelope': {
                'errorLanguage': 'en_US',
                'detailLevel': 'ReturnAll',
            }
        }

        response = self.post(url, data=payload)

        return PreapprovalDetails(self.config, response)

    @mixedmethod
    def refund(self, transaction):
        url = self.config.environment.AdaptivePayments.transaction_endpoint

        payload = {}

        response = self.post(url, data=payload)

        return response


class PayResponse(PaypalJSONAPIResponse):

    _required_fields = ('paykey',)

    @property
    def paykey(self):
        return self.response['payKey']

    _payment_details = None

    @property
    def payment_details(self):
        if not self._payment_details:
            try:
                self._payment_details = PaymentDetails(self.config, self.response)
            except PaypalAPIError:
                """ Some responses (those requiring authorization) may not
                have payment details available yet"""
                pass
        return self._payment_details

    @payment_details.setter
    def payment_details(self, value):
        self._payment_details = value

    @property
    def redirect(self):
        """ Authorization redirect based on a payKey """
        if self.payment_details:
            return ''
        return '{url}&paykey={key}'.format(
            url=self.config.environment.AdaptivePayments.authorization_redirect,
            key=self.paykey
        )

    @property
    def success(self):
        return super(PayResponse, self).success and 'payErrorList' not in self.response


class PreapprovalResponse(PaypalJSONAPIResponse):
    """ Wrapper around a Preapproval response from Paypal

    Contains the preapprovalKey token, and a redirect url to provide to the
    sender to confirm the preapproval
    """

    _required_fields = ('preapprovalkey',)

    @property
    def preapprovalkey(self):
        return self.response['preapprovalKey']

    @property
    def redirect(self):
        """ Authorization redirect based on a preapprovalKey """
        return '{url}&preapprovalkey={key}'.format(
            url=self.config.environment.AdaptivePayments.preapproval_redirect,
            key=self.preapprovalkey
        )


class PaymentDetails(PaypalJSONAPIResponse):

    _required_fields = ('payments',)

    @property
    def memo(self):
        return self.response['memo']

    @property
    def payments(self):
        return self.response['paymentInfoList']['paymentInfo']

    @property
    def paykey(self):
        return self.response['payKey']

    @property
    def first_payment(self):
        return self.payments and self.payments[0]

    @property
    def first_receiver(self):
        return self.first_payment['receiver']


class PreapprovalDetails(PaypalJSONAPIResponse):

    _required_fields = ('sender_email', 'ending_date', 'starting_date')

    @property
    def sender_email(self):
        return self.response['senderEmail']

    @property
    def ending_date(self):
        return self.response['endingDate']

    @property
    def starting_date(self):
        return self.response['startingDate']

    @property
    def approved(self):
        """ Returns true if this preapproval is valid and active """
        return self.response.get('status') == 'ACTIVE' and self.response.get('approved') == 'true'


class Receiver(object):
    """ Receiver of a Paypal payment """
    email = None
    amount = None
    primary = None

    def __init__(self, email=None, amount=None, invoice_id=None, primary=None):
        if not email:
            raise PaypalAPIError('Email must not be empty')

        if amount is None:
            raise PaypalAPIError('Amount must not be empty')

        self.email = email
        self.amount = str(amount)
        self.invoice_id = invoice_id
        self.primary = primary

    def __str__(self):
        return "<Paypal Receiver {email} for {amount}{primary}>".format(
            email=self.email,
            amount=self.amount,
            primary=' (primary)' if self.primary else '',
        )

    def as_dict(self):
        receiver = {
            'email': self.email,
            'amount': self.amount,
        }

        if self.invoice_id is not None:
            receiver['invoiceId'] = self.invoice_id

        if self.primary is not None:
            receiver['primary'] = self.primary

        return receiver

    @staticmethod
    def number_of_primary(receivers):
        return sum(1 for receiver in receivers if receiver.primary)
