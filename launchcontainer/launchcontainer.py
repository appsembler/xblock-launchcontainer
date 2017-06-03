"""This XBlock provides an HTML page fragment to display a button
   allowing the Course user to launch an external course Container
   via Appsembler's Container deploy API.
"""

import pkg_resources
import logging

from django.conf import settings
from django.template import Context, Template
from django.core import validators

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from xblock.core import XBlock
from xblock.fields import Scope, String
from xblock.fragment import Fragment


logger = logging.getLogger(__name__)


DEFAULT_WHARF_ENDPOINT = 'https://wharf.appsembler.com/isc/newdeploy'


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
        help=(u"This is a unique token that can be found in the AVL dashboard.")
    )

    @property
    def block_course_org(self):
        return self.runtime.course_id.org

    @property
    def student_email(self):
        if hasattr(self, "runtime"):
            user = self.runtime._services['user'].get_current_user()
            return user.emails[0]
        else:
            return None

    def _get_API_url(self, force=False):

        urls = (
            # TODO: Write tests for each of these.
            # A string: the currently supported implementation.
            settings.ENV_TOKENS.get('LAUNCHCONTAINER_WHARF_ENDPOINT'),
            # A dict: the deprecated version.
            settings.ENV_TOKENS.get('LAUNCHCONTAINER_API_CONF', {}).get('default'),
            # Fallback to the default.
            DEFAULT_WHARF_ENDPOINT
        )

        if not hasattr(self, '_wharf_endpoint') or force:
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
            'API_url': self._get_API_url()
        }
        frag = Fragment()
        frag.add_content(
            render_template('static/html/launchcontainer.html', context)
        )
        frag.add_css(render_template("static/css/launchcontainer.css"))
        frag.add_javascript(render_template("static/js/src/launchcontainer.js",
                                            context))
        frag.initialize_js('LaunchContainerXBlock')
        return frag

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

            context = {
                'fields': edit_fields,
                'API_url': self._get_API_url()
            }
            fragment = Fragment()
            fragment.add_content(
                render_template(
                    'static/html/launchcontainer_edit.html',
                    context
                )
            )
            # TODO: Should we be relying more heavily on XBlock's tools for
            # loading this stuff? See:
            # http://edx.readthedocs.io/projects/xblock-tutorial/en/latest/concepts/methods.html#view-methods
            fragment.add_css(render_template("static/css/launchcontainer_edit.css"))
            fragment.add_javascript(
                load_resource("static/js/src/launchcontainer_edit.js")
            )
            fragment.initialize_js('LaunchContainerEditBlock')

            return fragment
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
            self.api_url = self._get_API_url()

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
