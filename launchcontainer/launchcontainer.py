"""This XBlock provides an HTML page fragment to display a button
   allowing the course user to launch an external course container
   via Appsembler Virtual Labs (AVL or "Wharf").
"""

import pkg_resources
import logging
from urllib.parse import urlparse

from django.conf import settings
from django.core import validators
from django.template import Context, Template
from django.core.exceptions import (
    ImproperlyConfigured,
    MultipleObjectsReturned,
    ObjectDoesNotExist,
)

from crum import get_current_user
from xblock.core import XBlock
from xblock.fields import Boolean, Scope, String
from xblock.fragment import Fragment
from xblockutils import settings as xblocksettings

try:
    from site_config_client.openedx import api as site_config_client_api
except ImportError:
    site_config_client_api = None

try:
    from tahoe_sites import api as tahoe_sites_api
except ImportError:
    tahoe_sites_api = None

logger = logging.getLogger(__name__)

WHARF_URL_KEY = 'LAUNCHCONTAINER_WHARF_URL'
STATIC_FILES = {
    'studio': {
        'template': 'static/html/launchcontainer_edit.html',
        'css': 'static/css/launchcontainer_edit.css',
        'js': 'static/js/src/launchcontainer_edit.js',
        'js_class': 'LaunchContainerEditBlock'
    },
    'student': {
        'template': 'static/html/launchcontainer.html',
        'css': 'static/css/launchcontainer.css',
        'js': 'static/js/src/launchcontainer.js',
        'js_class': 'LaunchContainerXBlock'
    }
}
DEFAULT_SUPPORT_URL = '/help'
DEFAULT_LAUNCHER_TIMEOUT_SECONDS = 120


def get_site_by_course(course_key):
    """
    Thin wrapper for tahoe_sites.api.get_site_by_course().
    """
    # Needs `tahoe-sites` to be installed.
    if course_key and tahoe_sites_api:
        try:
            return tahoe_sites_api.get_site_by_course(course_key)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            logger.info("Error while getting site for course: %s", course_key, exc_info=True)

    return None


def get_tahoe_wharf_url_for_course(course_key, default=None):
    """
    Gets Tahoe Wharf URL for a specific course.

    Safe fallback: This method will return `None` if the `tahoe-sites` package isn't installed.
    """
    # Needs `site-configuration-client` to be installed.
    if site_config_client_api:
        site = get_site_by_course(course_key)
        if site:
            return site_config_client_api.get_secret_value(
                WHARF_URL_KEY,
                site=site,
                default=default,
            )

    return default


def get_api_root_url(url):
    parsed_url = urlparse(url)
    return "{}://{}".format(parsed_url.scheme, parsed_url.netloc)


def is_valid(url):
    """Return True if this URL is valid."""
    if not url:
        return False
    validator = validators.URLValidator()
    try:
        validator(url)
    except validators.ValidationError:
        return False
    else:
        return True


def _add_static(fragment, type, context):
    """Add the staticfiles to the fragment, where `type` is either student or studio,
    and `context` is a dict that will be passed to the render_template function."""
    fragment.add_content(render_template(STATIC_FILES[type]['template'], context))
    fragment.add_css(render_template(STATIC_FILES[type]['css'], context))
    fragment.add_javascript(render_template(STATIC_FILES[type]['js'], context))
    fragment.initialize_js(STATIC_FILES[type]['js_class'])

    return fragment


@XBlock.needs('user')
@XBlock.wants('settings')
class LaunchContainerXBlock(XBlock, xblocksettings.XBlockWithSettingsMixin):
    """
    Provide a Fragment with associated Javascript to display to
    Students a button that will launch a configurable external course
    Container via a call to Appsembler's container deploy API.
    """

    has_author_view = True  # Tells Studio to use author_view

    display_name = String(help="Display name of the component",
                          default="Container Launcher",
                          scope=Scope.settings)

    project = String(
        display_name='Project name',
        default='(EDIT THIS COMPONENT TO SET PROJECT NAME)',
        scope=Scope.content,
        help=("The name of the project as defined for the "
              "Appsembler Virtual Labs (AVL) API."),
    )

    project_friendly = String(
        display_name='Project Friendly name',
        default='',
        scope=Scope.content,
        help=("The name of the container's Project as displayed to the end "
              "user"),
    )

    project_token = String(
        display_name='Project Token',
        default='',
        scope=Scope.content,
        help=("This is a unique token that can be found in the AVL dashboard")
    )

    enable_container_resetting = Boolean(
        display_name='Enable container resetting',
        default=False,
        scope=Scope.content,
        help=("Enables students to reset/delete their container and start over")
    )

    support_email = String(
        display_name='Tech support email',
        default='',
        scope=Scope.content,
        help=(
            "Email address of tech support for AVL labs. If set, help messages displayed "
            "in case of error or timeout will use this address for a mailto: link.  If unset, "
            "a link to the configured support URL (defaulting to /help) will be used instead."
        ),
    )

    def get_wharf_url(self, required=True):
        """
        Get WHARF URL.
        """
        course_id = getattr(self, "course_id", None)

        # System-wide fallback settings
        system_default_wharf_url = settings.ENV_TOKENS.get(WHARF_URL_KEY)

        # Attempt getting Tahoe site-specific WHARF URL
        wharf_url = get_tahoe_wharf_url_for_course(
            course_id, default=system_default_wharf_url
        )

        message = "A valid url for the LaunchContainer XBlock is needed: {}".format(wharf_url)

        if wharf_url:
            if not is_valid(wharf_url):
                raise ImproperlyConfigured(message)  # Invalid URL
        elif required:
            raise ImproperlyConfigured(message)  # Missing required URL

        return wharf_url

    def get_wharf_delete_url(self, required=True):
        wharf_url = self.get_wharf_url(required=required)
        if not required and not wharf_url:
            return wharf_url

        api_root = get_api_root_url(wharf_url)
        return "{}/isc/dashboard/userprojectdeployments/delete_user_deployments/".format(api_root)

    # TODO: Cache this property?
    @property
    def user_email(self):
        user = get_current_user()
        if hasattr(user, 'email') and user.email:
            return user.email

        user_service = self.runtime.service(self, 'user')
        user = user_service.get_current_user()
        email = user.emails[0] if type(user.emails) == list else user.email

        return email

    @property
    def support_url(self):
        lcsettings = self.get_xblock_settings()
        return lcsettings.get('support_url', DEFAULT_SUPPORT_URL)

    @property
    def timeout_secs(self):
        lcsettings = self.get_xblock_settings()
        return lcsettings.get('timeout_seconds', DEFAULT_LAUNCHER_TIMEOUT_SECONDS)

    def student_view(self, context=None, required_wharf_urls=True):
        """
        The primary view of the LaunchContainerXBlock, shown to students
        when viewing courses.
        """
        support_email = self.support_email if self.support_email is not None else ''
        context = {
            'enable_container_resetting': self.enable_container_resetting,
            'project': self.project,
            'project_friendly': self.project_friendly,
            'project_token': self.project_token,
            'support_email': support_email,
            'support_url': self.support_url,
            'timeout_seconds': self.timeout_secs,
            'user_email': self.user_email,
            'API_url': self.get_wharf_url(required=required_wharf_urls),
            'API_delete_url': self.get_wharf_delete_url(required=required_wharf_urls),
        }

        return _add_static(Fragment(), 'student', context)

    def studio_view(self, context=None):
        """
        Return fragment for editing block in studio.
        """
        try:
            cls = type(self)

            def none_to_empty(data):
                """
                Return empty string if data is None else return data.
                """
                return data if data is not None else ''

            edit_fields = (
               (field, none_to_empty(getattr(self, field.name)), validator)
               for field, validator in (
                   (cls.project, 'string'),
                   (cls.project_friendly, 'string'),
                   (cls.project_token, 'string'),
                   (cls.enable_container_resetting, 'boolean'),
                   (cls.support_email, 'string'),
               )
            )

            context = {'fields': edit_fields,
                       'API_url': self.get_wharf_url(required=False),
                       'API_delete_url': self.get_wharf_delete_url(required=False),
                       'support_email': self.support_email,
                       'user_email': self.user_email
                       }

            return _add_static(Fragment(), 'studio', context)

        except:  # noqa E722 # pragma: NO COVER
            # TODO: Handle all the errors and handle them well.
            logger.error("Don't swallow my exceptions", exc_info=True)
            raise

    def author_view(self, context=None):
        """
        Studio author preview view.
        """
        return self.student_view(context, required_wharf_urls=False)

    @XBlock.json_handler
    def studio_submit(self, data, suffix=''):
        logger.info('Received data: {}'.format(data))

        # TODO: This could use some better validation.
        try:
            self.enable_container_resetting = data['enable_container_resetting']
            self.project = data['project'].strip()
            self.project_friendly = data['project_friendly'].strip()
            self.project_token = data['project_token'].strip()
            self.support_email = data.get('support_email', '')
            self.api_url = self.get_wharf_url()
            self.api_delete_url = self.get_wharf_delete_url()

            return {'result': 'success'}

        except Exception as e:
            return {'result': 'Error saving data:{0}'.format(str(e))}

    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("A single launchcontainer",
             """\
                <vertical_demo>
                    <launchcontainer/>
                </vertical_demo>
             """)
        ]


def load_resource(resource_path):  # pragma: NO COVER
    """
    Gets the content of a resource
    """
    resource_content = pkg_resources.resource_string(__name__, resource_path)
    return resource_content.decode('utf-8')


def render_template(template_path, context=None):  # pragma: NO COVER
    """
    Evaluate a template by resource path, applying the provided context.
    """
    if context is None:
        context = {}

    template_str = load_resource(template_path)
    template = Template(template_str)

    return template.render(Context(context))
