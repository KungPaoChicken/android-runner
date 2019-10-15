import logging


class Profiler(object):

    # noinspection PyUnusedLocal
    def __init__(self, config, paths):
        self.logger = logging.getLogger(self.__class__.__name__)
        pass

    def dependencies(self):
        """Returns list of needed app dependencies,like com.quicinc.trepn, [] if none"""
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

    def collect_results(self, device):
        """Collect the data and clean up extra files on the device, save data in location set by 'set_output' """
        raise NotImplementedError

    def unload(self, device):
        """Stop the profiler, removing configuration files on device"""
        raise NotImplementedError

    def set_output(self, output_dir):
        """Set the output directory before the start_profiling is called"""
        raise NotImplementedError

    def aggregate_subject(self):
        """Aggregate the data at the end of a subject, collect data and save data to location set by 'set output' """
        raise NotImplementedError

    def aggregate_end(self, data_dir, output_file):
        """Aggregate the data at the end of the experiment.
         Data located in file structure inside data_dir. Save aggregated data to output_file
        """
        raise NotImplementedError
