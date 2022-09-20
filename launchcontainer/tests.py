"""
Tests for launchcontainer
"""
from unittest import mock, skipUnless, TestCase
from unittest.mock import patch

import json

from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured

from xblock.field_data import DictFieldData
from opaque_keys.edx.locations import Location, SlashSeparatedCourseKey

try:
    from site_config_client.openedx import api as site_config_client_api
    from site_config_client.openedx.test_helpers import override_site_config
except ImportError:
    site_config_client_api = None

from .launchcontainer import STATIC_FILES, WHARF_URL_KEY

WHARF_ENDPOINT_GOOD = "https://api.localhost"
WHARF_ENDPOINT_BAD = "notARealUrl"
WHARF_ENDPOINT_UNSET = ""


def patch_with_env_token_wharf_url(wharf_url):
    return patch.dict(
        'django.conf.settings.ENV_TOKENS',
        **{WHARF_URL_KEY: wharf_url}
    )


class DummyResource(object):
    """
     A Resource class for use in tests
    """
    def __init__(self, path):
        self.path = path

    def __eq__(self, other):
        return isinstance(other, DummyResource) and self.path == other.path


class DummyUser(object):
    def __init__(self, email):
        self.emails = [email, ]


class LaunchContainerXBlockTests(TestCase):
    """
    Create a launchcontainer block with mock data.
    """
    def setUp(self):
        """
        Creates a test course ID, mocks the runtime, and creates a fake storage
        engine for use in all tests
        """
        super(LaunchContainerXBlockTests, self).setUp()
        self.course_id = SlashSeparatedCourseKey.from_deprecated_string(
            'foo/bar/baz'
        )
        self.scope_ids = mock.Mock()
        self.custom_xblock_config = {'timeout_seconds': 60, 'support_url': '/support'}
        self.default_xblock_config = {}
        self.user_service = mock.Mock()
        self.user_service.get_current_user = mock.Mock(
            return_value=DummyUser(email='user@example.com')
        )
        self.runtime = mock.Mock()

    def tearDown(self):
        cache.clear()

    def settings_val_by_custom(self, key, default):
        return self.custom_xblock_config.get(key, default)

    def settings_val_by_default(self, key, default):
        return self.default_xblock_config.get(key, default)

    def make_one(self, display_name=None, **kw):
        """
        Creates a launchcontainer XBlock for testing purpose.
        """
        from .launchcontainer import LaunchContainerXBlock as cls
        field_data = DictFieldData(kw)
        block = cls(self.runtime, field_data, self.scope_ids)
        block.location = Location(
            'org', 'course', 'run', 'category', 'name', 'revision'
        )
        block.xmodule_runtime = self.runtime
        block.course_id = self.course_id
        block.scope_ids.usage_id = 'XXX'

        if display_name:
            block.display_name = display_name

        block.project = 'Foo project'
        block.project_friendly = 'Foo Project Friendly Name'
        block.project_token = 'Foo token'
        block.support_email = 'support@example.com'
        return block

    @mock.patch('launchcontainer.launchcontainer.load_resource', DummyResource)
    @mock.patch('launchcontainer.launchcontainer.render_template')
    @mock.patch('launchcontainer.launchcontainer.Fragment')
    @patch_with_env_token_wharf_url(WHARF_ENDPOINT_GOOD)
    def test_student_view(self, fragment, render_template):
        # pylint: disable=unused-argument
        """
        Test student view renders correctly.
        """
        # mock user service
        self.runtime.service = mock.Mock(return_value=self.user_service)

        block = self.make_one("Custom name")
        fragment = block.student_view()
        self.assertEqual(render_template.call_count, 3)

        # Confirm that the template was rendered properly.
        template_arg = render_template.call_args_list[0][0][0]
        self.assertEqual(template_arg, STATIC_FILES['student']['template'])
        context = render_template.call_args_list[0][0][1]

        # Confirm that the context was correct.
        self.assertEqual(context['project'], 'Foo project')
        self.assertEqual(context['project_friendly'], 'Foo Project Friendly Name')
        self.assertEqual(context['project_token'], 'Foo token')
        self.assertEqual(context['user_email'], 'user@example.com')
        self.assertEqual(context['API_url'], block.get_wharf_url())
        self.assertEqual(context['support_email'], 'support@example.com')

        # Confirm that the css was included.
        css_template_arg = render_template.call_args_list[1][0][0]
        self.assertEqual(css_template_arg, STATIC_FILES['student']['css'])

        # Confirm that the JavaScript was included.
        javascript_template_arg = render_template.call_args_list[2][0][0]
        self.assertEqual(javascript_template_arg, STATIC_FILES['student']['js'])
        fragment.initialize_js.assert_called_once_with(STATIC_FILES['student']['js_class'])

    def test_author_preview_view(self):
        """
        Test author preview view renders correctly with and without a wharf endpoint.
        """
        self.runtime.service = mock.Mock(return_value=self.user_service)
        block = self.make_one("Custom name")

        with patch_with_env_token_wharf_url(WHARF_ENDPOINT_GOOD):
            fragment = block.author_view()
            self.assertIn('launcher_form', fragment.body_html())  # form is rendered

        with patch_with_env_token_wharf_url(None):
            fragment = block.author_view()
            # Error should be shown if the URL is missing on author view
            self.assertIn('Error: Unable to connect to the Appsembler Virtual Labs API',
                          fragment.body_html())

    @mock.patch('launchcontainer.launchcontainer.LaunchContainerXBlock.get_xblock_settings')
    @mock.patch('launchcontainer.launchcontainer.render_template')
    @mock.patch('launchcontainer.launchcontainer.Fragment')
    @patch_with_env_token_wharf_url(WHARF_ENDPOINT_GOOD)
    def test_xblock_properties_from_settings(self, fragment, render_template, get_xblock_settings):
        """Test that if settings are configured they are used in favor of defaults.
        For support_url, timeout_seconds.
        """
        # default settings case
        get_xblock_settings().get = mock.Mock(side_effect=self.settings_val_by_default)
        block = self.make_one("Custom name")
        fragment = block.student_view()  # noqa: F841
        context = render_template.call_args_list[-1][0][1]
        self.assertEqual(context['support_url'], '/help')
        self.assertEqual(context['timeout_seconds'], 120)

        # custom settings case
        get_xblock_settings().get = mock.Mock(side_effect=self.settings_val_by_custom)
        block2 = self.make_one("Custom name 2")
        fragment = block2.student_view()  # noqa: F841
        context = render_template.call_args_list[-1][0][1]
        self.assertEqual(context['support_url'], '/support')
        self.assertEqual(context['timeout_seconds'], 60)

    @mock.patch('launchcontainer.launchcontainer.load_resource', DummyResource)
    @mock.patch('launchcontainer.launchcontainer.render_template')
    @mock.patch('launchcontainer.launchcontainer.Fragment')
    @patch_with_env_token_wharf_url(WHARF_ENDPOINT_GOOD)
    def test_studio_view(self, fragment, render_template):
        # pylint: disable=unused-argument
        """
        Test that the template, css and javascript are loaded properly into the studio view.
        """
        block = self.make_one()
        fragment = block.studio_view()

        # Called once for the template, once for the css.
        self.assertEqual(render_template.call_count, 3)

        # Confirm that the rendered template is the right one.
        self.assertEqual(render_template.call_args_list[0][0][0],
                         STATIC_FILES['studio']['template'])

        # Confirm that the context was set properly on the XBlock instance.
        render_template.call_args_list[0][0][1]
        # self.assertEqual(tuple(context['fields']), (
        #     (cls.project, 'Foo project', 'string'),
        #     (cls.project_friendly, 'Foo Project Friendly Name', 'string'),
        #     (cls.project_token, 'Foo token', 'string')
        # ))

        # Confirm that the JavaScript was pulled in.
        fragment.add_javascript.assert_called_once_with(
            render_template(DummyResource(STATIC_FILES['studio']['js']))
        )

        fragment.initialize_js.assert_called_once_with(STATIC_FILES['studio']['js_class'])

        # Confirm that the css was pulled in.
        fragment.add_css.assert_called_once_with(
            render_template(DummyResource(STATIC_FILES['studio']['css']))
        )

        css_template_arg = render_template.call_args_list[1][0][0]
        self.assertEqual(css_template_arg, STATIC_FILES['studio']['css'])

    def test_save_launchcontainer(self):
        """
        Tests save launchcontainer block on studio.
        """
        proj_str = 'Baz Project shortname'
        proj_friendly_str = 'Baz Project Friendly Name'
        block = self.make_one()
        block.studio_submit(mock.Mock(body='{}'))
        self.assertEqual(block.display_name, "Container Launcher")
        self.assertEqual(block.project, 'Foo project')
        self.assertEqual(block.project_friendly, 'Foo Project Friendly Name')
        block.studio_submit(mock.Mock(method="POST", body=json.dumps({
            "project": proj_str,
            "project_friendly": proj_friendly_str})).encode('utf-8'))
        self.assertEqual(block.display_name, "Container Launcher")

    @patch_with_env_token_wharf_url(WHARF_ENDPOINT_GOOD)
    def test_api_url_set_from_env_tokens(self):
        """
        A valid URL at ENV_TOKENS[WHARF_URL_KEY] should be used as
        the URL for requests.
        """
        block = self.make_one()
        self.assertEqual(block.get_wharf_url(), WHARF_ENDPOINT_GOOD)

    @patch_with_env_token_wharf_url(None)
    def test_api_url_not_set(self):
        """
        If ENV_TOKENS[WHARF_URL_KEY] is not a valid url, an error should
        be raised because no good URL exists.
        """
        block = self.make_one()
        with self.assertRaises(ImproperlyConfigured):
            block.get_wharf_url()

    @skipUnless(site_config_client_api, 'Needs tahoe_sites.api to be loaded')
    @patch('launchcontainer.launchcontainer.get_site_by_course')
    def test_url_from_tahoe_site_config(self, mock_get_site_by_course):
        """
        Test getting URL from Tahoe Open edX site config client.
        """
        mock_get_site_by_course.return_value = {'id': 'dummy'}
        with override_site_config("secret", **{WHARF_URL_KEY: WHARF_ENDPOINT_GOOD}):
            block = self.make_one()
            self.assertEqual(block.get_wharf_url(), WHARF_ENDPOINT_GOOD)
