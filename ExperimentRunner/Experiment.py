import logging
import os.path as op
import time

import paths
import Tests
from threading import Thread
from os import walk, remove, rmdir
from Devices import Devices
from Profilers import Profilers
from Scripts import Scripts
from util import ConfigError, makedirs, slugify_dir


class Experiment(object):
    def __init__(self, config, progress):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.progress = progress
        self.basedir = None
        self.random = config.get('randomization', False)
        if 'devices' not in config:
            raise ConfigError('"device" is required in the configuration')
        adb_path = config.get('adb_path', 'adb')
        self.devices = Devices(config['devices'], adb_path=adb_path)
        self.replications = Tests.is_integer(config.get('replications', 1))
        self.paths = config.get('paths', [])
        self.profilers = Profilers(config.get('profilers', {}))
        monkeyrunner_path = config.get('monkeyrunner_path', 'monkeyrunner')
        self.scripts = Scripts(config.get('scripts', {}), monkeyrunner_path=monkeyrunner_path)
        self.time_between_run = Tests.is_integer(config.get('time_between_run', 0))
        Tests.check_dependencies(self.devices, self.profilers.dependencies())
        self.output_root = paths.OUTPUT_DIR
        self.result_file_structure = None

    def prepare(self, device):
        """Prepare the device for experiment"""
        self.logger.info('Device: %s' % device)
        self.profilers.load(device)
        device.unplug()

    def cleanup(self, device):
        """Cleans up the changes on the devices"""
        device.plug()
        self.profilers.stop_profiling(device)
        self.profilers.unload(device)

    def get_progress_xml_file(self):
        return self.progress.progress_xml_file

    def update_progress(self):
        self.progress.write_progress_to_file()
        result_data_path = op.join(paths.BASE_OUTPUT_DIR, 'data')
        self.result_file_structure = walk(result_data_path)

    def start(self):
        interrupted = False
        try:
            result_data_path = op.join(paths.BASE_OUTPUT_DIR, 'data')
            self.result_file_structure = walk(result_data_path)
            while not self.progress.experiment_finished_check():
                current_run = self.get_experiment()
                self.prepare_output_dir(current_run)

                self.first_run_device(current_run)
                self.first_run(current_run)
                if 'browser' in current_run:
                    self.run(self.devices.get_device(current_run['device']), current_run['path'],
                             int(current_run['runCount']), current_run['browser'])
                else:
                    self.run(self.devices.get_device(current_run['device']), current_run['path'],
                             int(current_run['runCount']), None)
                self.progress.run_finished(current_run['runId'])
                self.last_run(current_run)
                self.last_run_device(current_run)
                a = Thread(target=self.update_progress)
                a.start()
                a.join()
        except Exception, e:
            import traceback
            print(traceback.format_exc())
            self.logger.error('%s: %s' % (e.__class__.__name__, e.message))
        except KeyboardInterrupt:
            interrupted = True
        finally:
            self.check_result_files(self.result_file_structure)
            for device in self.devices:
                self.cleanup(device)
            if interrupted:
                raise KeyboardInterrupt
        self.aggregate_end()

    def check_result_files(self, correct_file_structure):
        result_data_path = op.join(paths.BASE_OUTPUT_DIR, 'data')
        current_file_structure = walk(result_data_path)
        correct_file_list = self.walk_to_list(correct_file_structure)
        current_file_list = self.walk_to_list(current_file_structure)
        for path in current_file_list:
            if path not in correct_file_list:
                if op.isfile(path):
                    remove(path)
                else:
                    rmdir(path)

    def walk_to_list(self, walk_result):
        walk_list = list()
        for (path, dirs, files) in walk_result:
            for dir in dirs:
                walk_list.append(op.join(path, dir))
            for file in files:
                walk_list.append(op.join(path, file))
        walk_list.reverse()
        return walk_list

    def get_experiment(self):
        if self.random:
            return self.progress.get_random_run()
        else:
            return self.progress.get_next_run()

    def first_run_device(self, current_run):
        self.prepare(self.devices.get_device(current_run['device']))
        self.before_experiment(self.devices.get_device(current_run['device']))

    def first_run(self, current_run):
        self.before_first_run(self.devices.get_device(current_run['device']), current_run['path'])

    def last_run_device(self, current_run):
        if self.progress.device_finished(current_run['device']):
            self.after_experiment(self.devices.get_device(current_run['device']))

    def last_run(self, current_run):
        if self.progress.subject_finished(current_run['device'], current_run['path']):
            self.after_last_run(self.devices.get_device(current_run['device']), current_run['path'])
            self.aggregate_subject()

    def prepare_output_dir(self, current_run):
        paths.OUTPUT_DIR = op.join(paths.BASE_OUTPUT_DIR, 'data/', current_run['device'], slugify_dir(current_run['path']))
        makedirs(paths.OUTPUT_DIR)

    """   def start(self):
        #Runs the experiment
        for device in self.devices:
            try:
                paths.OUTPUT_DIR = op.join(self.output_root, 'data/', device.name)
                makedirs(paths.OUTPUT_DIR)
                self.prepare(device)
                self.before_experiment(device)
                for path in self.paths:
                    self.before_first_run(device, path)
                    for run in range(self.replications):
                        self.run(device, path, run)
                    self.after_last_run(device, path)
                    self.aggregate_subject()
                self.after_experiment(device)
            except Exception, e:
                import traceback
                print(traceback.format_exc())
                self.logger.error('%s: %s' % (e.__class__.__name__, e.message))
            finally:
                self.cleanup(device)
        self.aggregate_end()
    """
    def run(self, device, path, run, dummy):
        self.before_run(device, path, run)
        self.start_profiling(device, path, run)
        self.interaction(device, path, run)
        self.stop_profiling(device, path, run)
        self.after_run(device, path, run)

    def before_experiment(self, device, *args, **kwargs):
        """Hook executed before the start of experiment"""
        self.scripts.run('before_experiment', device, *args, **kwargs)

    def before_first_run(self, device, path, *args, **kwargs):
        """Hook executed before the first run for a subject"""
        pass

    def before_run(self, device, path, run, *args, **kwargs):
        """Hook executed before a run"""
        self.profilers.set_output()
        self.logger.info('Run %s of %s' % (run, self.replications))
        device.shell('logcat -c')
        self.logger.info('Logcat cleared')
        self.scripts.run('before_run', device, *args, **kwargs)

    def after_launch(self, device, path, run, *args, **kwargs):
        self.scripts.run('after_launch', device, *args, **kwargs)

    def start_profiling(self, device, path, run, *args, **kwargs):
        self.profilers.start_profiling(device)

    def interaction(self, device, path, run, *args, **kwargs):
        """Interactions on the device to be profiled"""
        self.scripts.run('interaction', device, *args, **kwargs)

    def stop_profiling(self, device, path, run, *args, **kwargs):
        self.profilers.stop_profiling(device)

    def before_close(self, device, path, run, *args, **kwargs):
        self.scripts.run('before_close', device, *args, **kwargs)

    def after_run(self, device, path, run, *args, **kwargs):
        """Hook executed after a run"""
        self.scripts.run('after_run', device, *args, **kwargs)
        self.profilers.collect_results(device)
        self.logger.debug('Sleeping for %s milliseconds' % self.time_between_run)
        time.sleep(self.time_between_run / 1000.0)

    def after_last_run(self, device, path, *args, **kwargs):
        """Hook executed after the last run of a subject"""
        pass

    def after_experiment(self, device, *args, **kwargs):
        """Hook executed after the end of experiment"""
        self.logger.info('Experiment completed, start cleanup')
        self.scripts.run('after_experiment', device, *args, **kwargs)

    def aggregate_subject(self):
        self.profilers.aggregate_subject()

    def aggregate_end(self):
        self.profilers.aggregate_end(self.output_root)

