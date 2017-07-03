from imp import load_source


class Runner:
    def __init__(self, scripts):
        self.scripts = {}
        for k, v in scripts.items():
            try:
                self.scripts[k] = load_source(k, v)
            except ImportError:
                raise ImportError("Cannot import %s" % v)

    def run(self, device, name, *args, **kwargs):
        current_activity = device.current_activity()
        return self.scripts[name].main(device.id, current_activity, *args, **kwargs)
