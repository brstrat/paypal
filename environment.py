class Environment(object):

    class Sandbox(object):
        application_id = 'APP-80W284485P519543T'  # Global sandbox application id

        class AdaptivePayments(object):
            authorization_redirect = 'https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_ap-payment'
            preapproval_redirect = 'https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_ap-preapproval'

            pay_endpoint = 'https://svcs.sandbox.paypal.com/AdaptivePayments/Pay'
            payment_details_endpoint = 'https://svcs.sandbox.paypal.com/AdaptivePayments/PaymentDetails'
            preapproval_endpoint = 'https://svcs.sandbox.paypal.com/AdaptivePayments/Preapproval'
            preapproval_details_endpoint = 'https://svcs.sandbox.paypal.com/AdaptivePayments/PreapprovalDetails'
            cancel_preapproval_endpoint = 'https://svcs.sandbox.paypal.com/AdaptivePayments/CancelPreapproval'
            refund_endpoint = 'https://svcs.sandbox.paypal.com/AdaptivePayments/Refund'

        class Permissions(object):
            grant_permission_redirect = 'https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_grant-permission'

            request_permissions_endpoint = 'https://svcs.sandbox.paypal.com/Permissions/RequestPermissions/'
            get_access_token_endpoint = 'https://svcs.sandbox.paypal.com/Permissions/GetAccessToken/'
            get_permissions_endpoint = 'https://svcs.sandbox.paypal.com/Permissions/GetPermissions/'
            cancel_permissions_endpoint = 'https://svcs.sandbox.paypal.com/Permissions/CancelPermissions/'

        class Merchant(object):
            merchant_endpoint = "https://api-3t.sandbox.paypal.com/nvp"

    class Production(object):
        application_id = None

        class AdaptivePayments(object):
            authorization_redirect = 'https://www.paypal.com/cgi-bin/webscr?cmd=_ap-payment'
            preapproval_redirect = 'https://www.paypal.com/cgi-bin/webscr?cmd=_ap-preapproval'

            pay_endpoint = 'https://svcs.paypal.com/AdaptivePayments/Pay'
            payment_details_endpoint = 'https://svcs.paypal.com/AdaptivePayments/PaymentDetails'
            preapproval_endpoint = 'https://svcs.paypal.com/AdaptivePayments/Preapproval'
            preapproval_details_endpoint = 'https://svcs.paypal.com/AdaptivePayments/PreapprovalDetails'
            cancel_preapproval_endpoint = 'https://svcs.paypal.com/AdaptivePayments/CancelPreapproval'
            refund_endpoint = 'https://svcs.paypal.com/AdaptivePayments/Refund'

        class Permissions(object):
            grant_permission_redirect = 'https://www.paypal.com/cgi-bin/webscr?cmd=_grant-permission'

            request_permissions_endpoint = 'https://svcs.paypal.com/Permissions/RequestPermissions/'
            get_access_token_endpoint = 'https://svcs.paypal.com/Permissions/GetAccessToken/'
            get_permissions_endpoint = 'https://svcs.paypal.com/Permissions/GetPermissions/'
            cancel_permissions_endpoint = 'https://svcs.paypal.com/Permissions/CancelPermissions/'

        class Merchant(object):
            merchant_endpoint = "https://api-3t.paypal.com/nvp"

Sandbox = Environment.Sandbox
Production = Environment.Production
