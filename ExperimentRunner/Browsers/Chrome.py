import Browser


class Chrome(Browser):
    def __init__(self, basedir, config):
        super(Chrome, self).__init__(basedir, config)
        self.package_name = 'com.android.chrome'
        self.main_activity = 'com.google.android.apps.chrome.Main'
