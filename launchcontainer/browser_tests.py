import unittest

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = 'http://localhost:8001'
USERNAME = 'YOUR_USERNAME'
PASSWORD = 'YOUR_PASSWORD'


class TestLaunchContainer(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(10)

    def tearDown(self):
        self.driver.close()

    def test_login(self):
        """I can login at /signin."""

        self.driver.get('{}/signin'.format(BASE_URL))
        assert "Sign In".lower() in self.driver.title.lower()

        username_input = self.driver.find_element_by_name('email')
        username_input.send_keys(USERNAME)
        password_input = self.driver.find_element_by_name('password')
        password_input.send_keys(PASSWORD)
        login_submit = self.driver.find_element_by_name('submit')
        login_submit.click()

        # This implicitly asserts that the page has changed.
        try:
            WebDriverWait(self.driver, 5).until(
                EC.title_contains("Studio Home")
            )
        except TimeoutException:
            raise AssertionError(
                "The page was not loaded. Current title: {}".format(self.driver.title)
            )
        finally:
            self.driver.quit()
