import pytest
import paths
import os.path as op
import lxml.etree as et
from ExperimentRunner.util import load_json
from ExperimentRunner.Progress import Progress


class TestProgressSetup(object):
    @pytest.fixture()
    def test_config(self):
        fixture_dir = op.join(op.dirname(op.realpath(__file__)), "fixtures")
        return op.join(fixture_dir, "test_config.json")

    @pytest.fixture()
    def test_progress(self):
        fixture_dir = op.join(op.dirname(op.realpath(__file__)), "fixtures")
        return op.join(fixture_dir, 'test_progress.xml')

    def test_progress_init(self, tmp_path, test_config, test_progress):
        paths.OUTPUT_DIR = tmp_path.as_posix()
        progress = Progress(config_file=test_config, config=load_json(test_config))
        with open(test_progress, 'r') as f:
            expected_xml = f.read()
        with open(progress.progress_xml_file, 'r') as f:
            result_xml = f.read()
        expected_stripped = expected_xml.split("<outputDir>")[0] + expected_xml.split("</outputDir>")[1]
        result_split = result_xml.split("<outputDir>")[0] + result_xml.split("</outputDir>")[1]
        assert expected_stripped == result_split

    def test_progress_resume(self, tmp_path, test_config, test_progress):
        paths.OUTPUT_DIR = tmp_path.as_posix()
        progress = Progress(config_file=test_config, progress_file=test_progress, load_progress=True)
        progress.progress_xml_file = op.join(paths.OUTPUT_DIR, "progress.xml")
        progress.write_progress_to_file()
        with open(test_progress, 'r') as f:
            expected_xml = f.read()
        with open(progress.progress_xml_file, 'r') as f:
            result_xml = f.read()
        expected_stripped = expected_xml.split("<outputDir>")[0] + expected_xml.split("</outputDir>")[1]
        result_stripped = result_xml.split("<outputDir>")[0] + result_xml.split("</outputDir>")[1]
        assert expected_stripped == result_stripped


class TestProgressMethods(object):
    @pytest.fixture()
    def test_config(self):
        fixture_dir = op.join(op.dirname(op.realpath(__file__)), "fixtures")
        return op.join(fixture_dir, "test_config.json")

    @pytest.fixture()
    def test_progress(self):
        fixture_dir = op.join(op.dirname(op.realpath(__file__)), "fixtures")
        return op.join(fixture_dir, 'test_progress.xml')

    @pytest.fixture()
    def current_progress(self, tmp_path, test_config):
        paths.OUTPUT_DIR = tmp_path.as_posix()
        return Progress(config_file=test_config, config=load_json(test_config))

    @pytest.fixture()
    def current_progress_resume(self, tmp_path, test_config, test_progress):
        paths.OUTPUT_DIR = tmp_path.as_posix()
        progress = Progress(config_file=test_config, progress_file=test_progress, load_progress=True)
        progress.progress_xml_file = op.join(paths.OUTPUT_DIR, "progress.xml")
        return progress

    @pytest.fixture()
    def config_web_dict(self):
        return {'devices': ['device1'], 'paths': ['path1'], 'type': 'web', 'browsers': ['browser1'], 'replications': 1}

    @pytest.fixture()
    def config_native_dict(self):
        return {'devices': ['device1'], 'paths': ['path1'], 'type': 'native', 'replications': 1}

    def same_subject(self, run, next_run):
        next_run.pop('runId')
        run.pop('runId')
        next_run.pop('runCount')
        run.pop('runCount')
        return next_run == run

    def test_ordered_next(self, current_progress):
        ids = list()
        for _ in range(50):
            ids.append(current_progress.get_next_run()['runId'])
        unique_values = len(set(ids))
        assert unique_values == 1

    def test_random_next(self, current_progress):
        ids = list()
        for _ in range(50):
            ids.append(current_progress.get_random_run()['runId'])
        unique_values = len(set(ids))
        assert unique_values > 1

    def test_get_progress_xml_file(self, current_progress):
        progress_file = current_progress.get_progress_xml_file()

        assert op.isfile(progress_file)
        assert progress_file[-3:] == "xml"

    def test_file_to_hash(self, current_progress, test_config):
        expected_hash = "7d490f79d238b64084ca72959cae6738"
        current_hash = current_progress.file_to_hash(test_config)
        assert current_hash == expected_hash

    def test_check_config_hash(self, current_progress, capsys, test_config, test_progress):
        assert current_progress.check_config_hash(test_config) is None

        with pytest.raises(SystemExit) as wrapper_result:
            current_progress.check_config_hash(test_progress)

        #Prevent output during testing
        out, err = capsys.readouterr()
        assert wrapper_result.type == SystemExit

    def test_run_to_dict(self, current_progress):
        run_dict = current_progress.run_to_dict(et.fromstring('<run runId="0"><device>device</device><path>path</path>'
                                                              '<browser>browser</browser><runCount>1</runCount></run>'))
        expected_dict = {'runId': '0', 'device': 'device', 'path': 'path', 'browser': 'browser', 'runCount': '1'}
        assert run_dict == expected_dict

    def test_build_runs_xml(self, current_progress, config_web_dict, config_native_dict):
        runs_xml_web = current_progress.build_runs_xml(config_web_dict)
        runs_xml_native = current_progress.build_runs_xml(config_native_dict)
        expected_runs_web = '<run runId="0"><device>device1</device><path>path1</path><browser>browser1</browser>' \
                            '<runCount>1</runCount></run>'
        expected_runs_native = '<run runId="0"><device>device1</device><path>path1</path><runCount>1</runCount></run>'
        assert runs_xml_web == expected_runs_web
        assert runs_xml_native == expected_runs_native

    def test_get_output_dir(self, current_progress_resume):
        assert current_progress_resume.get_output_dir() == "test/output/dir"

    def test_subject_first(self, current_progress):
        run = current_progress.get_next_run()
        subject_first = current_progress.subject_first(run['device'], run['path'], run['browser'])
        assert subject_first is True

        subject_first_native = current_progress.subject_first(run['device'], run['path'])
        assert subject_first_native is True

        current_progress.run_finished(run['runId'])
        run = current_progress.get_next_run()
        subject_first = current_progress.subject_first(run['device'], run['path'], run['browser'])
        assert subject_first is False

    def test_subject_finished(self, current_progress):
        run = current_progress.get_next_run()
        subject_finished = current_progress.subject_finished(run['device'], run['path'], run['browser'])
        assert subject_finished is False

        subject_finished_native = current_progress.subject_finished(run['device'], run['path'])
        assert subject_finished_native is False

        current_progress.run_finished(run['runId'])
        next_run = current_progress.get_next_run()
        while self.same_subject(run.copy(), next_run.copy()):
            run = next_run.copy()
            current_progress.run_finished(run['runId'])
            next_run = current_progress.get_next_run()

        subject_finished = current_progress.subject_finished(run['device'], run['path'], run['browser'])
        assert subject_finished is True

    def test_run_finished(self, current_progress):
        run = current_progress.get_next_run()
        next_run = current_progress.get_next_run()
        assert run == next_run

        current_progress.run_finished(run['runId'])
        next_run = current_progress.get_next_run()
        assert run != next_run

    def test_experiment_finished_check(self, current_progress):
        experiment_finished = current_progress.experiment_finished_check()
        assert experiment_finished is False

        for _ in range(9):
            run = current_progress.get_next_run()
            current_progress.run_finished(run['runId'])

        experiment_finished = current_progress.experiment_finished_check()
        assert experiment_finished is True

    def test_device_first(self, current_progress):
        run = current_progress.get_next_run()
        device_first = current_progress.device_first(run['device'])
        assert device_first is True

        current_progress.run_finished(run['runId'])
        run = current_progress.get_next_run()
        device_first = current_progress.device_first(run['device'])
        assert device_first is False

    def test_device_finished(self, current_progress):
        run = current_progress.get_next_run()
        device_finished = current_progress.device_finished(run['device'])
        assert device_finished is False

        while not current_progress.experiment_finished_check():
            run = current_progress.get_next_run()
            current_progress.run_finished(run['runId'])

        device_finished = current_progress.device_finished(run['device'])
        assert device_finished is True

