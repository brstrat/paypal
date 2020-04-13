from setuptools import setup, find_packages

setup(
    name='paypal',
    version='0.1.0',    
    description='Allows interacting with PayPal payments gateway',
    url='https://github.com/brstrat/paypal',
    packages=find_packages(),
    install_requires=[
        'requests',                     
    ],
)

