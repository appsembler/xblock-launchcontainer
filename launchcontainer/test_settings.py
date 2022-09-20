"""
Test settings for the Launchcontainer XBlock.
"""

from workbench.settings import *  # noqa - needed for the XBlock tests to work
from workbench.settings import INSTALLED_APPS

from django.conf.global_settings import LOGGING  # noqa - fix workbench-specific log requirements


INSTALLED_APPS += [
    'django.contrib.sites',
    'launchcontainer',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

ENV_TOKENS = {
    'LAUNCHCONTAINER_WHARF_URL': 'dummy',
}
