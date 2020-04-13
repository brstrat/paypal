from setuptools import setup

setup(
    name='paypal',
    version='0.1.0',    
    description='Allows interacting with PayPal payments gateway',
    url='https://github.com/brstrat/paypal',
    packages=['paypal'],
    install_requires=[
        'requests',                     
    ],
)

