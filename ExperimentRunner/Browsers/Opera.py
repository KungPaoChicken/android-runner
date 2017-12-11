import Browser


class Opera(Browser):
    def __init__(self, basedir, config):
        super(Opera, self).__init__(basedir, config)
        self.package_name = 'com.opera.browser'
        self.main_activity = 'com.opera.Opera'
