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
    def add_row(accum, new):
        row = {k: v + float(new[k]) for k, v in accum.items() if k not in ['Component', 'count']}
        count = accum['count'] + 1
        return dict(row, **{'count': count})

    runs = []
    for run_file in [f for f in os.listdir(logs_dir) if os.path.isfile(os.path.join(logs_dir, f))]:
        with open(os.path.join(logs_dir, run_file), 'rb') as run:
            run_dict = {}
            reader = csv.DictReader(run)
            column_readers = split_reader(reader)
            for k,v in column_readers.items():
                init = dict({k: 0}, **{'count': 0})
                run_total = reduce(add_row, v, init)
                if not run_total['count'] == 0:
                    run_dict[k] = run_total[k] / run_total['count']
            runs.append(run_dict)
    init = dict({fn: 0 for fn in runs[0].keys()}, **{'count': 0})
    runs_total = reduce(add_row, runs, init)
    return OrderedDict(sorted({k: v / len(runs) for k, v in runs_total.items() if not k == 'count'}.items(), key=lambda x: x[0]))

def split_reader(reader):
    column_dicts = {fn: [] for fn in reader.fieldnames if not fn.split('[')[0].strip() == 'Time'}
    for row in reader:
        for k,v in row.items():
            if not k.split('[')[0].strip() == 'Time' and not v == '':
                column_dicts[k].append({k:v})
    return column_dicts

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
