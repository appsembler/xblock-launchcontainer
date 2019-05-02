"""This XBlock provides an HTML page fragment to display a button
   allowing the course user to launch an external course container
   via Appsembler Virtual Labs (AVL or "Wharf").
"""

import pkg_resources
import logging
from urlparse import urlparse

from django.conf import settings
from django.contrib.sites.models import Site
from django.core import validators
from django.core.cache import cache
from django.db.models.signals import post_save
from django.template import Context, Template
from django.core.exceptions import ImproperlyConfigured

from crum import get_current_user
from xblock.core import XBlock
from xblock.fields import Boolean, Scope, String
from xblock.fragment import Fragment

try:
    from openedx.core.djangoapps.site_configuration import helpers as siteconfig_helpers
    from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
    from openedx.core.djangoapps.site_configuration.helpers import (
        is_site_configuration_enabled
    )
    from openedx.core.djangoapps.theming.helpers import get_current_site
except ImportError:  # We're in an older Open edX environment.
    siteconfig_helpers = None
    is_site_configuration_enabled = None
    get_current_site = None


logger = logging.getLogger(__name__)

WHARF_URL_KEY = 'LAUNCHCONTAINER_WHARF_URL'
CACHE_KEY_TIMEOUT = 60 * 60 * 72  # 72 hours.
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


def get_api_root_url(url):
    parsed_url = urlparse(url)
    return "{}://{}".format(parsed_url.scheme, parsed_url.netloc)


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

    enable_container_resetting = Boolean(
        display_name='Enable container resetting',
        default=False,
        scope=Scope.content,
        help=(u"Enables students to reset/delete their container and start over")
    )

    support_email = String(
        display_name='Tech support email',
        default=getattr(settings, "TECH_SUPPORT_EMAIL", ""),
        scope=Scope.content,
        help=(u"Email address of tech support for AVL labs."),
    )

    @property
    def wharf_url(self, force=False):
        """Determine which site we're on, then get the Wharf URL that said
        site has configured."""

        # The complexities of Tahoe require that we check several places
        # for the site configuration, which itself contains the URL
        # of the AVL cluster associated with this site.
        #
        # If we are in Tahoe studio, the Site object associated with this request
        # will not be the one used within Tahoe. To get the proper domain
        # we rely on the "organization", which always equals `Site.name`.
        # If the organization value does not return a site object, we are probably on
        # the LMS side. In this case, we use `get_current_site()`, which _does_
        # return the incorrect site object. If all this fails, we fallback
        # to the DEFAULT_WHARF_URL.
        try:
            # The name of the Site object will always match self.course_id.org.
            # See: https://git.io/vpilS
            site = Site.objects.get(name=self.course_id.org)
        except (Site.DoesNotExist, AttributeError):  # Probably on the lms side.
            if get_current_site:
                site = get_current_site()  # From the request.
            else:
                site = Site.objects.all().order_by('domain').first()

        url = cache.get(make_cache_key(site.domain))
        if url:
            return url

        # Nothing in the cache. Go find the URL.
        site_wharf_url = None
        if hasattr(site, 'configuration'):
            site_wharf_url = site.configuration.get_value(WHARF_URL_KEY)
        elif siteconfig_helpers:
            # Rely on edX's helper, which will fall back to the microsites app.
            site_wharf_url = siteconfig_helpers.get_value(WHARF_URL_KEY)

        urls = (
            # A SiteConfig object: this is the preferred implementation.
            (
                'SiteConfiguration',
                site_wharf_url
            ),
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
        )

        try:
            url = next((x[1] for x in urls if is_valid(x[1])))
        except StopIteration:
            raise ImproperlyConfigured("No Virtual Labs URL was found, "
                                       "please contact your site administrator.")

        if not url:
            raise AssertionError("You must set a valid url for the launchcontainer XBlock. "
                                 "URLs attempted: {}".format(urls)
                                 )

        cache.set(make_cache_key(site), url, CACHE_KEY_TIMEOUT)

        logger.debug("XBlock-launchcontainer urls attempted: {}".format(urls))

        return url

    @property
    def wharf_delete_url(self):
        api_root = get_api_root_url(self.wharf_url)
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

    def student_view(self, context=None):
        """
        The primary view of the LaunchContainerXBlock, shown to students
        when viewing courses.
        """

        context = {
            'enable_container_resetting': self.enable_container_resetting,
            'project': self.project,
            'project_friendly': self.project_friendly,
            'project_token': self.project_token,
            'support_email': self.support_email,
            'user_email': self.user_email,
            'API_url': self.wharf_url,
            'API_delete_url': self.wharf_delete_url,
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
                       'API_url': self.wharf_url,
                       'API_delete_url': self.wharf_delete_url,
                       'support_email': self.support_email,
                       'user_email': self.user_email
                       }

            return _add_static(Fragment(), 'studio', context)

        except:  # noqa E722 # pragma: NO COVER
            # TODO: Handle all the errors and handle them well.
            logger.error("Don't swallow my exceptions", exc_info=True)
            raise

    @XBlock.json_handler
    def studio_submit(self, data, suffix=''):
        logger.info(u'Received data: {}'.format(data))

        # TODO: This could use some better validation.
        try:
            self.enable_container_resetting = data['enable_container_resetting']
            self.project = data['project'].strip()
            self.project_friendly = data['project_friendly'].strip()
            self.project_token = data['project_token'].strip()
            self.support_email = data['support_email'].strip()
            self.api_url = self.wharf_url
            self.api_delete_url = self.wharf_delete_url

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


def update_wharf_url_cache(sender, **kwargs):
    """
    Receiver that will update the cache item that contains
    this site's WHARF_URL_KEY.
    TODO: This function could use a test or two once they are running in the edx
    environment.
    """
    instance = kwargs['instance']

    new_key = False
    if hasattr(instance, 'values') and instance.values:
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


if is_site_configuration_enabled:
    post_save.connect(update_wharf_url_cache, sender=SiteConfiguration, weak=False)
