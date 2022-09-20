import django
import os
from django.core.management import call_command


def main():
    # Dynamically configure the Django settings with the minimum necessary to
    # get Django running tests
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'launchcontainer.test_settings')
    django.setup()

    # Fire off the tests
    call_command('migrate')
    call_command('test')


if __name__ == '__main__':
    main()
