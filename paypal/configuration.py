from .exceptions import PaypalError


class ConfigurationError(PaypalError):
    pass


class Configuration(object):
    """ Configure the Paypal environment

    Usage::

        import paypal

        paypal_settings = {
            'environment': paypal.Environment.Sandbox,
            'userid': '<user id>',
            'password': '<password>',
            'signature': '<signature>',
            'application_id': '<application id>',  # Not required for sandbox
        }

        # Global configuration
        paypal.Configuration.configure(**paypal_settings)
        paypal.AdaptivePayments.pay(...)


        # Instance configuration
        config = paypal.Configuration(**paypal_settings)
        paypal.AdaptivePayments(config).pay(...)
    """

    environment = None
    userid = None
    password = None
    signature = None
    application_id = None

    def __init__(
        self, environment, userid, password, signature,
        application_id=None
    ):
        self.environment = environment
        self.userid = userid
        self.password = password
        self.signature = signature
        self.application_id = application_id or environment.application_id

    @classmethod
    def configure(
        cls, environment, userid, password, signature,
        application_id=None
    ):
        """ Use global configuration settings """
        Configuration.environment = environment
        Configuration.userid = userid
        Configuration.password = password
        Configuration.signature = signature
        Configuration.application_id = application_id

    @classmethod
    def instantiate(cls):
        """ Return settings as a configuration instance """
        return cls(
            Configuration.environment,
            Configuration.userid,
            Configuration.password,
            Configuration.signature,
            Configuration.application_id,
        )
