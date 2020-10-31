"""quart-prometheus-logger"""

from setuptools import setup

REQUIREMENTS = [
    'Quart>=0.9.1',
    'prometheus_client==0.7.1'
]

setup(
    name='quart-prometheus-logger',
    version='1.0',
    url='https://github.com/sparkmeter/quart-prometheus-logger',
    license='MIT',
    author='Sparkmeter Systems Engineering',
    author_email='syseng@sparkmeter.io',
    description='Log Prometheus metrics for your Quart application',
    long_description=open('README.md').read(),
    py_modules=['quart_prometheus_logger'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=REQUIREMENTS,
    tests_require=[
        'pytest',
    ],
    extras_require={
        'dev': [
            'asynctest==0.13.0',
            'black==20.8b1',
            'isort==5.4.2',
            'mypy==0.781',
            'mypy-extensions==0.4.3',
            'pip-tools==4.5.1',
            'pylint==2.6.0',
            'pytest==4.3.1',
            'pytest-cov==2.7.1',
            'pytest-asyncio==0.10.0',
        ]
    },
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)