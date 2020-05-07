import csv
import os
import sys
from collections import OrderedDict
from functools import reduce
import pdb


def list_subdir(a_dir):
    """List immediate subdirectories of a_dir"""
    # https://stackoverflow.com/a/800201
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]


def aggregate_android_final(logs_dir):
    def add_row(accum, new):
        row = {k: v + float(new[k]) for k, v in list(accum.items()) if k not in ['Component', 'count']}
        count = accum['count'] + 1
        return dict(row, **{'count': count})

    runs = []
    for run_file in [f for f in os.listdir(logs_dir) if os.path.isfile(os.path.join(logs_dir, f))]:
        with open(os.path.join(logs_dir, run_file), 'r') as run:
            reader = csv.DictReader(run)
            init = dict({fn: 0 for fn in reader.fieldnames if fn != 'datetime'}, **{'count': 0})
            run_total = reduce(add_row, reader, init)
            runs.append({k: v / run_total['count'] for k, v in list(run_total.items()) if k != 'count'})
    runs_total = reduce(lambda x, y: {k: v + y[k] for k, v in list(x.items())}, runs)
    return OrderedDict(
        sorted(list({'android_' + k: v / len(runs) for k, v in list(runs_total.items())}.items()), key=lambda x: x[0]))


def aggregate(data_dir):
    rows = []
    for device in list_subdir(data_dir):
        row = OrderedDict({'device': device})
        device_dir = os.path.join(data_dir, device)
        for subject in list_subdir(device_dir):
            row.update({'subject': subject})
            subject_dir = os.path.join(device_dir, subject)
            if os.path.isdir(os.path.join(subject_dir, 'AndroidPlugin')):
                row.update(aggregate_android_final(os.path.join(subject_dir, 'AndroidPlugin')))
                rows.append(row.copy())
            else:
                for browser in list_subdir(subject_dir):
                    row.update({'browser': browser})
                    browser_dir = os.path.join(subject_dir, browser)
                    if os.path.isdir(os.path.join(browser_dir, 'AndroidPlugin')):
                        row.update(aggregate_android_final(os.path.join(browser_dir, 'AndroidPlugin')))
                        rows.append(row.copy())
    return rows


def write_to_file(filename, rows):
    with open(filename, 'w') as f:
        writer = csv.DictWriter(f, list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


# noinspection PyUnusedLocal
def main(dummy, data_dir, result_file):
    print(('Output file: {}'.format(result_file)))
    rows = aggregate(data_dir)
    write_to_file(result_file, rows)


if __name__ == '__main__':
    if len(sys.argv) == 3:
        # noinspection PyArgumentList
        main(None, sys.argv[1], sys.argv[2])
