import sys
import os
import csv
from collections import OrderedDict


def list_subdir(a_dir):
    """List immediate subdirectories of a_dir"""
    # https://stackoverflow.com/a/800201
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]


def aggregate_trepn_final(logs_dir):
    def format_stats(accum, new):
        column_name = new['Name']
        if '[' in new['Type']:
            column_name += ' [' + new['Type'].split('[')[1]
        accum.update({column_name: float(new['Average'])})
        return accum
    runs = []
    for run_file in [f for f in os.listdir(logs_dir) if os.path.isfile(os.path.join(logs_dir, f))]:
        with open(os.path.join(logs_dir, run_file), 'rb') as run:
            contents = run.read()   # Be careful with large files, this loads everything into memory
            system_stats = contents.split('System Statistics:')[1].strip().splitlines()
            reader = csv.DictReader(system_stats)
            runs.append(reduce(format_stats, reader, {}))
    runs_total = reduce(lambda x, y: {k: v + y[k] for k, v in x.items()}, runs)
    return OrderedDict(sorted({k: v / len(runs) for k, v in runs_total.items()}.items(), key=lambda x: x[0]))


def aggregate(data_dir):
    rows = []
    for device in list_subdir(data_dir):
        row = OrderedDict({'device': device})
        device_dir = os.path.join(data_dir, device)
        for subject in list_subdir(device_dir):
            row.update({'subject': subject})
            subject_dir = os.path.join(device_dir, subject)
            if os.path.isdir(os.path.join(subject_dir, 'trepn')):
                row.update(aggregate_trepn_final(os.path.join(subject_dir, 'trepn')))
                rows.append(row.copy())
            else:
                for browser in list_subdir(subject_dir):
                    row.update({'browser': browser})
                    browser_dir = os.path.join(subject_dir, browser)
                    if os.path.isdir(os.path.join(browser_dir, 'trepn')):
                        row.update(aggregate_trepn_final(os.path.join(browser_dir, 'trepn')))
                        rows.append(row.copy())
    return rows


def write_to_file(filename, rows):
    with open(filename, 'w') as f:
        writer = csv.DictWriter(f, rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def main(dummy, data_dir, result_file):
    print('Output file: {}'.format(result_file))
    rows = aggregate(data_dir)
    write_to_file(result_file, rows)


if __name__ == '__main__':
    if len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])
