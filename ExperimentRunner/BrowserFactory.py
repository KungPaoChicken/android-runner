from Browsers import Chrome, Firefox, Opera


class BrowserFactory(object):
    @staticmethod
    def get_browser(name):
        if name == "chrome":
            return Chrome
        if name == "firefox":
            return Firefox
        if name == "opera":
            return Opera
        return Exception("No Browser found")
