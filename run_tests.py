import django
from django.conf import settings
from django.core.management import call_command


def main():
    # Dynamically configure the Django settings with the minimum necessary to
    # get Django running tests
    settings.configure(
        INSTALLED_APPS=(
            'django.contrib.sites',
            'launchcontainer',
        ),
        # Django replaces this, but it still wants it. *shrugs*
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
                'HOST': '',
                'PORT': '',
                'USER': '',
                'PASSWORD': '',
            }
        },
        ENV_TOKENS={
            'LAUNCHCONTAINER_WHARF_URL': 'dummy',
        },
    )

    django.setup()

    # Fire off the tests
    call_command('migrate')
    call_command('test')

if __name__ == '__main__':
    main()
