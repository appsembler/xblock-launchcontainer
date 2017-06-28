"""This XBlock provides an HTML page fragment to display a button
   allowing the course user to launch an external course container
   via Appsembler Virtual Labs (AVL or "Wharf").
"""

import pkg_resources
import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.core import validators
from django.core.cache import cache
from django.db.models.signals import post_save
from django.template import Context, Template

from xblock.core import XBlock
from xblock.fields import Scope, String
from xblock.fragment import Fragment

try:
    from openedx.core.djangoapps.site_configuration import helpers as siteconfig_helpers
    from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
    from openedx.core.djangoapps.site_configuration.helpers import (
        is_site_configuration_enabled
    )
    from openedx.core.djangoapps.theming.helpers import get_current_site
except ImportError:  # We're not in an openedx environment.
    IS_OPENEDX_ENVIRON = False
    siteconfig_helpers = None
else:
    IS_OPENEDX_ENVIRON = True


logger = logging.getLogger(__name__)

WHARF_URL_KEY = 'LAUNCHCONTAINER_WHARF_URL'
CACHE_KEY_TIMEOUT = 60 * 60 * 72  # 72 hours.
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


def make_cache_key(site_domain):
    return '{}.{}.'.format('launchcontainer_wharf_url', site_domain)


def is_valid(url):
    """Return True if this URL is valid."""
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
        default=u'(EDIT THIS COMPONENT TO SET PROJECT NAME)',
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
        help=(u"This is a unique token that can be found in the AVL dashboard")
    )

    @property
    def wharf_url(self, force=False):
        """Determine which site we're on, then get the Wharf URL that said
        site has configured."""

        # If we are in Tahoe studio, the Site object associated with this request
        # will not be the Site associated with the user's "microsite" within Tahoe.
        # To remedy this, we need to rely on the "organization" of the current course.
        # However, if we are on the studio side, edX's get_current_site() helper
        # will return the proper URL (and the sting assigned to edx_site_domain will
        # not).
        try:
            # TODO: Can we hook into edX's RequestCache? See: https://git.io/vH7Zf
            edx_site_domain = "{}.{}".format(self.course_id.org, settings.LMS_BASE)
            site = Site.objects.get(domain=edx_site_domain)
        except (AttributeError, Site.DoesNotExist):  # We're probably on the lms side of Tahoe.
            site = None

        if not site and IS_OPENEDX_ENVIRON:
            site = get_current_site()  # From the request.
        else:  # We're in the xblock-sdk.
            site = Site.objects.all(order_by='domain').first()

        url = cache.get(make_cache_key(site.domain))
        if url:
            return url

        # Nothing in the cache. Go find the URL.
        site_wharf_url = None
        if hasattr(site, 'configuration'):
            site_wharf_url = site.configuration.get_value(WHARF_URL_KEY)
        else:
            # Rely on edX's helper, which will fall back to the microsites app.
            site_wharf_url = siteconfig_helpers.get_value(WHARF_URL_KEY)

        urls = (
            # A SiteConfig object: this is the preferred implementation.
            (
                'SiteConfiguration',
                site_wharf_url
            ),
            # TODO: Maybe we can cache this and set up a signal
            # to update this value if a SiteConfig object is changed.
            # A string: the currently supported implementation.
            (
                "ENV_TOKENS[{}]".format(WHARF_URL_KEY),
                settings.ENV_TOKENS.get(WHARF_URL_KEY)
            ),
            # A dict: the deprecated version.
            (
                "ENV_TOKENS['LAUNCHCONTAINER_API_CONF']",
                settings.ENV_TOKENS.get('LAUNCHCONTAINER_API_CONF', {}).get('default')
            ),
            # Fallback to the default.
            (
                "Default", DEFAULT_WHARF_URL
            )
        )

        url = next((x[1] for x in urls if is_valid(x[1])))
        if not url:
            raise AssertionError("You must set a valid url for the launchcontainer XBlock. "
                                 "URLs attempted: {}".format(urls)
                                 )

        cache.set(make_cache_key(site), url, CACHE_KEY_TIMEOUT)

        logger.debug("XBlock-launchcontainer urls attempted: {}".format(urls))
        if IS_OPENEDX_ENVIRON:
            logger.debug("Current site: {}".format(get_current_site()))
            logger.debug("Current site config enabled: {}".format(
                is_site_configuration_enabled())
            )
            logger.debug("Current site config LAUNCHCONTAINER_WHARF_URL: {}".format(
                siteconfig_helpers.get_value('LAUNCHCONTAINER_WHARF_URL')))

        return url

    # TODO: Cache this property?
    @property
    def user_email(self):

        user_email = None
        user_service = self.runtime.service(self, 'user')
        user = user_service.get_current_user()
        user_email = user.emails[0] if type(user.emails) == list else user.email

        return user_email

    def student_view(self, context=None):
        """
        The primary view of the LaunchContainerXBlock, shown to students
        when viewing courses.
        """

        context = {
            'project': self.project,
            'project_friendly': self.project_friendly,
            'project_token': self.project_token,
            'user_email': self.user_email,
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

            context = {'fields': edit_fields,
                       'API_url': self.wharf_url,
                       'user_email': self.user_email
                       }

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

            return {
                'result': 'success',
                'validated_data': {
                        'project': self.project,
                        'project_friendly': self.project_friendly,
                        'project_token': self.project_token
                }
            }

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


def update_wharf_url_cache(sender, **kwargs):
    """
    Receiver that will update the cache item that contains
    this site's WHARF_URL_KEY.
    """
    instance = kwargs['instance']
    new_key = instance.values.get(WHARF_URL_KEY)
    if new_key:
        cache.set(make_cache_key(instance.site.domain),
                  instance.values.get(WHARF_URL_KEY),
                  CACHE_KEY_TIMEOUT
                  )
    else:
        # Delete the key in the off chance that the user is trying
        # to fall back to one of the other methods of storing the URL.
        cache.delete(make_cache_key(instance.site.domain))

if IS_OPENEDX_ENVIRON:
    post_save.connect(update_wharf_url_cache, sender=SiteConfiguration, weak=False)
