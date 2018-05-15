from xml.dom import minidom
import csv
import os.path as op


def parse_power_profile(power_profile, out_dir):
    filename = op.join(out_dir, 'power_profile.csv')
    xmlfile = minidom.parse(power_profile)
    itemlist = xmlfile.getElementsByTagName('item')
    for item in itemlist:
        rows = []
        itemname = item.attributes['name'].value
        itemvalue = item.childNodes[0].nodeValue
        rows.append(itemname)
        rows.append(itemvalue)
        with open(filename, 'a') as f:
            writer = csv.writer(f, rows)
            writer.writerow(rows)

    arraylist = xmlfile.getElementsByTagName('array')
    for array in arraylist:
        arrayname = array.attributes['name'].value
        valuelist = array.getElementsByTagName('value')
        for value in valuelist:
            rows = []
            val = value.childNodes[0].nodeValue
            rows.append(arrayname)
            rows.append(val)
            with open(filename, 'a') as f:
                writer = csv.writer(f, rows)
                writer.writerow(rows)
