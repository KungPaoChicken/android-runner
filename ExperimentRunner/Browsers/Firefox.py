import Browser


class Firefox(Browser):
    def __init__(self, basedir, config):
        super(Firefox, self).__init__(basedir, config)
        self.package_name = 'org.mozilla.firefox'
        self.main_activity = 'org.mozilla.gecko.BrowserApp'
