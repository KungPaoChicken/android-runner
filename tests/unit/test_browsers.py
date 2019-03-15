import pytest
from mock import patch, Mock
from ExperimentRunner.BrowserFactory import BrowserFactory
from ExperimentRunner.Browsers import Browser, Chrome, Opera, Firefox


class TestBrowsers(object):
    @pytest.fixture()
    def browser(self):
        return Browser.Browser(None)

    def test_get_browser(self):
        assert isinstance(BrowserFactory.get_browser('opera'), Opera.Opera.__class__)
        assert isinstance(BrowserFactory.get_browser('chrome'), Chrome.Chrome.__class__)
        assert isinstance(BrowserFactory.get_browser('firefox'), Firefox.Firefox.__class__)

        with pytest.raises(Exception) as except_result:
            BrowserFactory.get_browser("fake_browser")
        assert "No Browser found" in except_result.value

    def test_browsers_to_string(self, browser):
        assert BrowserFactory.get_browser('opera')(None).to_string() == 'com.opera.browser'
        assert BrowserFactory.get_browser('chrome')(None).to_string() == 'com.android.chrome'
        assert BrowserFactory.get_browser('firefox')(None).to_string() == 'org.mozilla.firefox'
        assert browser.to_string() == ''

    @patch('logging.Logger.info')
    def test_start(self, mock, browser):
        mock_device = Mock()
        mock_device.id = "fake_device"
        browser.start(mock_device)
        mock.assert_called_once_with('fake_device: Start')
        mock_device.launch_activity.assert_called_once_with("", "", from_scratch=True, force_stop=True,
                                                            action='android.intent.action.VIEW')

    @patch('logging.Logger.info')
    def test_load_url(self, mock, browser):
        mock_device = Mock()
        mock_device.id = "fake_device"
        browser.load_url(mock_device, 'test.url')
        mock.assert_called_once_with('fake_device: Load URL: test.url')
        mock_device.launch_activity.assert_called_once_with("", "", data_uri='test.url',
                                                            action='android.intent.action.VIEW')

    @patch('logging.Logger.info')
    def test_stop(self, mock, browser):
        mock_device = Mock()
        mock_device.id = "fake_device"
        browser.stop(mock_device, True)
        mock.assert_called_once_with('fake_device: Stop')
        mock_device.force_stop.assert_called_once_with("")
        mock_device.clear_app_data.assert_called_once_with("")
        assert mock_device.clear_app_data.call_count == 1
        
        browser.stop(mock_device, False)
        mock.assert_called_with('fake_device: Stop')
        assert mock_device.clear_app_data.call_count == 1

