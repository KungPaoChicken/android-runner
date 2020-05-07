import pytest
from mock import Mock, patch

from AndroidRunner.BrowserFactory import BrowserFactory
from AndroidRunner.Browsers import Browser, Chrome, Firefox, Opera


class TestBrowsers(object):
    @pytest.fixture()
    def browser(self):
        return Browser.Browser(None)

    def test_get_browser_chrome(self):
        assert isinstance(BrowserFactory.get_browser('chrome'), Chrome.Chrome.__class__)

    def test_get_browser_opera(self):
        assert isinstance(BrowserFactory.get_browser('opera'), Opera.Opera.__class__)

    def test_get_browser_firefox(self):
        assert isinstance(BrowserFactory.get_browser('firefox'), Firefox.Firefox.__class__)

    def test_get_browser_fake(self):
        with pytest.raises(Exception) as except_result:
            BrowserFactory.get_browser("fake_browser")
        assert "No Browser found" in str(except_result.value)

    def test_browsers_to_string_browser(self, browser):
        assert browser.to_string() == ''

    def test_browsers_to_string_opera(self, browser):
        assert BrowserFactory.get_browser('opera')(None).to_string() == 'com.opera.browser'

    def test_browsers_to_string_chrome(self, browser):
        assert BrowserFactory.get_browser('chrome')(None).to_string() == 'com.android.chrome'

    def test_browsers_to_string_firefox(self, browser):
        assert BrowserFactory.get_browser('firefox')(None).to_string() == 'org.mozilla.firefox'

    @patch('AndroidRunner.Browsers.Browser.Browser.__init__')
    def test_chrome_init(self, mock_browser):
        mock_config = Mock()
        chrome_browser = Chrome.Chrome(mock_config)

        mock_browser.assert_called_once_with(mock_config)
        chrome_browser.package_name = 'com.android.chrome'
        chrome_browser.main_activity = 'com.google.android.apps.chrome.Main'

    @patch('AndroidRunner.Browsers.Browser.Browser.__init__')
    def test_firefox_init(self, mock_browser):
        mock_config = Mock()
        firefox_browser = Firefox.Firefox(mock_config)

        mock_browser.assert_called_once_with(mock_config)
        firefox_browser.package_name = 'org.mozilla.firefox'
        firefox_browser.main_activity = 'org.mozilla.gecko.BrowserApp'

    @patch('AndroidRunner.Browsers.Browser.Browser.__init__')
    def test_opera_init(self, mock_browser):
        mock_config = Mock()
        opera_browser = Opera.Opera(mock_config)

        mock_browser.assert_called_once_with(mock_config)
        opera_browser.package_name = 'com.opera.browser'
        opera_browser.main_activity = 'com.opera.Opera'

    @patch('logging.Logger.info')
    def test_start(self, mock_log, browser):
        mock_package_name = Mock()
        browser.package_name = mock_package_name
        mock_main_activity = Mock()
        browser.main_activity = mock_main_activity
        mock_device = Mock()
        mock_device.id = "fake_device"
        browser.start(mock_device)
        mock_log.assert_called_once_with('fake_device: Start')
        mock_device.launch_activity.assert_called_once_with(mock_package_name, mock_main_activity, from_scratch=True,
                                                            force_stop=True,
                                                            action='android.intent.action.VIEW')

    @patch('logging.Logger.info')
    def test_load_url(self, mock_log, browser):
        mock_package_name = Mock()
        browser.package_name = mock_package_name
        mock_main_activity = Mock()
        browser.main_activity = mock_main_activity
        mock_device = Mock()
        mock_device.id = "fake_device"
        browser.load_url(mock_device, 'test.url')
        mock_log.assert_called_once_with('fake_device: Load URL: test.url')
        mock_device.launch_activity.assert_called_once_with(mock_package_name, mock_main_activity, data_uri='test.url',
                                                            action='android.intent.action.VIEW')

    @patch('logging.Logger.info')
    def test_stop_clear_data(self, mock, browser):
        mock_device = Mock()
        mock_device.id = "fake_device"
        browser.stop(mock_device, True)
        mock.assert_called_once_with('fake_device: Stop')
        mock_device.force_stop.assert_called_once_with("")
        mock_device.clear_app_data.assert_called_once_with("")
        assert mock_device.clear_app_data.call_count == 1

    @patch('logging.Logger.info')
    def test_stop(self, mock, browser):
        mock_device = Mock()
        mock_device.id = "fake_device"
        browser.stop(mock_device, False)

        mock_device.force_stop.assert_called_once_with("")
        mock.assert_called_with('fake_device: Stop')
        assert mock_device.clear_app_data.call_count == 0
