import hashlib
import logging
import os
import sys
from random import randint

import lxml.etree as et

import paths


class Progress(object):
    def __init__(self, progress_file=None, config_file=None, config=None, load_progress=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        if load_progress:
            self.progress_xml_file = progress_file
            self.progress_xml_content = et.parse(self.progress_xml_file).getroot()
            self.check_config_hash(config_file)
        else:
            self.progress_xml_file = os.path.join(paths.OUTPUT_DIR, 'progress.xml')
            self.progress_xml_content = self.build_progress_xml(config, config_file)
            self.write_progress_to_file()

    def get_progress_xml_file(self):
        return self.progress_xml_file

    @staticmethod
    def file_to_hash(path):
        with open(path, 'r') as myfile:
            content_string = myfile.read().replace('\n', '')
        hashed_string_obj = hashlib.md5(content_string.encode())
        return hashed_string_obj.hexdigest()

    def check_config_hash(self, config_file):
        progress_config_hash = self.progress_xml_content.find('configHash').text
        if progress_config_hash == self.file_to_hash(config_file):
            return
        else:
            print('Current config.json and config.json from progress.xml are not the same, cannot continue')
            sys.exit()

    def build_progress_xml(self, config, config_file):
        config_hash_xml = '<configHash>{}</configHash>'.format(self.file_to_hash(config_file))
        output_dir_xml = '<outputDir>{}</outputDir>'.format(paths.OUTPUT_DIR)
        runs_to_run_xml = '<runsToRun>{}</runsToRun>'.format(self.build_runs_xml(config))
        runs_done_xml = '<runsDone></runsDone>'
        experiment_xml = '<experiment>{}{}{}{}</experiment>'.format(config_hash_xml, output_dir_xml,
                                                                    runs_to_run_xml, runs_done_xml)
        return et.fromstring(experiment_xml)

    @staticmethod
    def build_subject_xml(device, path, browser=None):
        device_xml = '<device>{}</device>'.format(device)
        path_xml = '<path>{}</path>'.format(path)
        if browser is not None:
            browser_xml = '<browser>{}</browser>'.format(browser)
            return '{}{}{}'.format(device_xml, path_xml, browser_xml)
        else:
            return '{}{}'.format(device_xml, path_xml)

    def build_runs_xml(self, config):
        runs_xml = ''
        run_id = 0
        for device in config['devices']:
            current_paths = config.get('paths', []) + config.get('apps', [])
            for path in current_paths:
                if config['type'] == 'web':
                    for browser in config['browsers']:
                        subject_xml = self.build_subject_xml(device, path, browser)
                        for run in range(config['replications']):
                            runs_xml = runs_xml + '<run runId="{}">{}<runCount>{}</runCount></run>'. \
                                format(run_id, subject_xml, run + 1)
                            run_id += 1
                else:
                    subject_xml = self.build_subject_xml(device, path)
                    for run in range(config['replications']):
                        runs_xml = runs_xml + '<run runId="{}">{}<runCount>{}</runCount></run>'. \
                            format(run_id, subject_xml, run + 1)
                        run_id += 1

        return runs_xml

    def write_progress_to_file(self):
        xml = self.progress_xml_content.getroottree()
        xml.write(self.progress_xml_file, pretty_print=True)

    def get_output_dir(self):
        return self.progress_xml_content.find('outputDir').text

    """Get a random run from the <runsToRuns> element"""

    def get_random_run(self):
        runs_to_run = self.progress_xml_content.find('runsToRun')
        count = len(runs_to_run.getchildren())
        random_index = randint(0, count - 1)
        next_run_xml = self.progress_xml_content.find('runsToRun')[random_index]
        return self.run_to_dict(next_run_xml)

    """Get the top run of the list"""

    def get_next_run(self):
        next_run_xml = self.progress_xml_content.find('runsToRun')[0]  # First run in list
        return self.run_to_dict(next_run_xml)

    """Turn a <run> element and its childeren into a dictionary"""

    def run_to_dict(self, run_xml):
        run = dict()
        run['runId'] = run_xml.get('runId')
        run['device'] = run_xml.find('device').text
        run['path'] = run_xml.find('path').text
        run['runCount'] = self.get_run_count(run_xml, run['device'], run['path'])
        browser = run_xml.find('browser')
        if browser is not None:
            run['browser'] = run_xml.find('browser').text
        return run

    def get_run_count(self, run_xml, device, path):
        runs_done = self.progress_xml_content.find('runsDone')
        browser_val = run_xml.find('browser')
        if browser_val is not None:
            browser_name = browser_val.text
            query = "run[device='{}' and path='{}' and browser='{}']".format(device, path, browser_name)
        else:
            query = "run[device='{}' and path='{}']".format(device, path)
        elements = runs_done.xpath(query)
        return len(elements) + 1

    """Marks run as finished"""

    def run_finished(self, run_id):
        runs_to_run = self.progress_xml_content.find('runsToRun')
        runs_done = self.progress_xml_content.find('runsDone')
        elements = runs_to_run.findall("run[@runId='{}']".format(run_id))
        for el in elements:
            runs_to_run.remove(el)
            runs_done.append(el)

    """Check if this subject already had it's first run"""

    def subject_first(self, device, path, browser=None):
        runs_done = self.progress_xml_content.find('runsDone')
        if browser is not None:
            elements = runs_done.xpath(
                "run[device='{}' and path='{}' and browser='{}']".format(device, path, browser))
        else:
            elements = runs_done.xpath(
                "run[device='{}' and path='{}']".format(device, path))
        if not elements:
            return True
        else:
            return False

    """Checks if all subject runs are done"""

    def subject_finished(self, device, path, browser=None):
        runs_to_run = self.progress_xml_content.find('runsToRun')
        if browser is not None:
            elements = runs_to_run.xpath(
                "run[device='{}' and path='{}' and browser='{}']".format(device, path, browser))
        else:
            elements = runs_to_run.xpath(
                "run[device='{}' and path='{}']".format(device, path))
        if not elements:
            return True
        else:
            return False

    """Check if this device already had it's first run"""

    def device_first(self, device):
        runs_done = self.progress_xml_content.find('runsDone')
        elements = runs_done.xpath("run[device='{}']".format(device))

        if not elements:
            return True
        else:
            return False

    """Checks if all device runs are done"""

    def device_finished(self, device):
        runs_to_run = self.progress_xml_content.find('runsToRun')
        elements = runs_to_run.xpath("run[device='{}']".format(device))

        if not elements:
            return True
        else:
            return False

    def experiment_finished_check(self):
        runs_to_run = self.progress_xml_content.find('runsToRun')
        count = len(runs_to_run.getchildren())
        if count == 0:
            return True
        else:
            return False
