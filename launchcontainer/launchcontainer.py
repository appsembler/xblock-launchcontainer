"""This XBlock provides an HTML page fragment to display a button
   allowing the Course user to launch an external course Container
   via Appsembler's Container deploy API.
"""

import pkg_resources
import logging

from django.conf import settings
from django.template import Context, Template
from django.core import validators

from xblock.core import XBlock
from xblock.fields import Scope, String
from web_fragments.fragment import Fragment

try:
    from openedx.core.djangoapps.site_configuration import helpers as siteconfig_helpers
except ImportError:  # We're not in an openedx environment.
    siteconfig_helpers = None


logger = logging.getLogger(__name__)

DEFAULT_WHARF_URL = 'https://wharf.appsembler.com/isc/newdeploy'
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


class URL(object):

    def __init__(self, url_string):
        self.url_string = url_string
        self.validator = validators.URLValidator()

    def is_valid(self):
        """Return True if the url is valid."""

        try:
            self.validator(self.url_string)
        except validators.ValidationError:
            return False
        else:
            return True


def _add_static(fragment, type, context):
    """Add the staticfiles to the fragment, where `type` is either student or studio,
    and `context` is a dict that will be passed to the render_template function."""
    fragment.add_content(render_template(STATIC_FILES[type]['template'], context))
    fragment.add_css(render_template(STATIC_FILES[type]['css'], context))
    fragment.add_javascript(render_template(STATIC_FILES[type]['js']))
    fragment.initialize_js(STATIC_FILES[type]['js_class'])

    return fragment


@XBlock.needs('user')
class LaunchContainerXBlock(XBlock):
    """
    Provide a Fragment with associated Javascript to display to
    Students a button that will launch a configurable external course
    Container via a call to Appsembler's container deploy API.
    """

    display_name = String(help="Display name of the component",
                          default="Container Launcher",
                          scope=Scope.settings)

    project = String(
        display_name='Project name',
        placeholder=u'Please enter the project id from AVL.',
        default=u'',
        scope=Scope.content,
        help=(u"The name of the project as defined for the "
              "Appsembler Virtual Labs (AVL) API."),
    )

    project_friendly = String(
        display_name='Project Friendly name',
        default=u'',
        scope=Scope.content,
        help=(u"The name of the container's Project as displayed to the end "
              "user"),
    )

    project_token = String(
        display_name='Project Token',
        default=u'',
        scope=Scope.content,
        help=(u"This is a unique token that can be found in the Appsembler "
              "Virtual Labs dashboard.")
    )

    @property
    def wharf_url(self, force=False):
        # TODO: logger.debug the failed validations.
        site_wharf_url = None
        if siteconfig_helpers:
            site_wharf_url = siteconfig_helpers.get_value('LAUNCHCONTAINER_WHARF_URL')
        urls = (
            # A SiteConfig object: this is the preferred implementation.
            site_wharf_url,
            # TODO: Maybe we can set up a signal to update this value if
            # a SiteConfig object is changed.
            # A string: the currently supported implementation.
            settings.ENV_TOKENS.get('LAUNCHCONTAINER_WHARF_URL'),
            # A dict: the deprecated version.
            settings.ENV_TOKENS.get('LAUNCHCONTAINER_API_CONF', {}).get('default'),
            # Fallback to the default.
            DEFAULT_WHARF_URL
        )

        self._wharf_endpoint = next((x for x in urls if URL(x).is_valid()))

        return self._wharf_endpoint

    def student_view(self, context=None):
        """
        The primary view of the LaunchContainerXBlock, shown to students
        when viewing courses.
        """
        user_email = None
        user_service = self.runtime.service(self, 'user')
        user = user_service.get_current_user()
        user_email = user.emails[0] if type(user.emails) == list else user.email

        context = {
            'project': self.project,
            'project_friendly': self.project_friendly,
            'project_token': self.project_token,
            'user_email': user_email,
            'API_url': self.wharf_url
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
               )
            )

            context = {'fields': edit_fields, 'API_url': self.wharf_url}

            return _add_static(Fragment(), 'studio', context)

        except:  # pragma: NO COVER
            # TODO: Handle all the errors and handle them well.
            logger.error("Don't swallow my exceptions", exc_info=True)
            raise

    @XBlock.json_handler
    def studio_submit(self, data, suffix=''):
        logger.info(u'Received data: {}'.format(data))

        # TODO: This could use some better validation.
        try:
            self.project = data['project'].strip()
            self.project_friendly = data['project_friendly'].strip()
            self.project_token = data['project_token'].strip()
            self.api_url = self.wharf_url

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

    return unicode(resource_content)


def render_template(template_path, context=None):  # pragma: NO COVER
    """
    Evaluate a template by resource path, applying the provided context.
    """
    if context is None:
        context = {}

    template_str = load_resource(template_path)
    template = Template(template_str)

    return template.render(Context(context))
