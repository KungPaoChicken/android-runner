class Profiler(object):
    @staticmethod
    def dependencies():
        """Returns list of needed app dependencies,like com.quicinc.trepn, [] if none"""
        raise NotImplementedError

    def __init__(self, config, paths):
        raise NotImplementedError

    def load(self, device):
        """Load (and start) the profiler process on the device"""
        raise NotImplementedError

    def start_profiling(self, device, **kwargs):
        """Start the profiling process"""
        raise NotImplementedError

    def stop_profiling(self, device, **kwargs):
        """Stop the profiling process"""
        raise NotImplementedError

    def collect_results(self, device, path=None):
        """Collect the data and clean up extra files on the device"""
        raise NotImplementedError

    def unload(self, device):
        """Stop the profiler, removing configuration files on device"""
        raise NotImplementedError

    def set_output(self, output_dir):
        """Set the output directory before the start_profiling is called"""
        raise NotImplementedError

    def aggregate_subject(self):
        """Aggregate the data at the end of the subject"""
        raise NotImplementedError

    def aggregate_end(self, data_dir, output_dir):
        """Aggregate the data at the end of the experiment"""
        raise NotImplementedError
