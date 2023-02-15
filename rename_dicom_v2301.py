#!/usr/bin/python

import pydicom
import argparse
import json
import os.path
import shutil
import os
import re
import logging
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

find_non_alpha = re.compile('[^0-9a-zA-Z_\-]+')
dest_permissions = 0o775


class MyHandler(FileSystemEventHandler):
    def __init__(self, dest_dir) -> None:
        self.dest_dir = dest_dir
        super().__init__()

    def on_closed(self, event):
        logging.info('File closed: {}'.format(event.src_path))
        try:
            run_one_file(event.src_path, self.dest_dir)
        except Exception as ex:
            logging.error('Error on file {}'.format(event.src_path), exc_info=ex)

def make_and_chmodown_dir_if_not_exist(dir_name):
    if not os.path.exists(dir_name):
        logging.info('Creating directory: {}'.format(dir_name))
        os.makedirs(dir_name)
        os.chmod(dir_name, dest_permissions)
        shutil.chown(dir_name, user='dcmserver', group='gmidata_dicom')

def get_acquisition_date(ds: pydicom.dataset.FileDataset) -> str:
    if 'AcquisitionDate' in ds:
        return ds.AcquisitionDate
    elif 'AcquisitionDateTime' in ds:
        return ds.AcquisitionDateTime[:8]
    elif 'SeriesDate' in ds:
        return ds.SeriesDate
    elif 'StudyDate' in ds:
        return ds.StudyDate
    else:
        return '00000000'

def run_one_file(path: str, dest_dir: str):
    # read dicom header
    ds = pydicom.dcmread(path, stop_before_pixels=True)

    # get and format needed fields
    alphanum = lambda v: find_non_alpha.sub('_', str(v).strip())
    fields = {
        'id': alphanum(ds.PatientID) if hasattr(ds, 'PatientID') else 'NOID',
        'name': alphanum(ds.PatientName) if hasattr(ds, 'PatientName') else 'NONAME',
        'snum': int(ds.SeriesNumber) if hasattr(ds, 'SeriesNumber') else 0,
        'sdesc': alphanum(ds.SeriesDescription) if hasattr(ds, 'SeriesDescription') else 'UNKNOWN',
        'inum': int(ds.InstanceNumber) if hasattr(ds, 'InstanceNumber') else 0,
        'adate': alphanum(get_acquisition_date(ds)),
    }

    # construct destination directory
    subj_dir = os.path.join(dest_dir, 
                            '{}+{}'.format(fields['id'], fields['name']))
    make_and_chmodown_dir_if_not_exist(subj_dir)


    series_dir = os.path.join(subj_dir,
                            '{}+{:03d}-{}'.format(fields['adate'], fields['snum'], fields['sdesc']))
    make_and_chmodown_dir_if_not_exist(series_dir)

    # construct destination file name
    dest_name = os.path.join(series_dir,
                                '{:05d}.dcm'.format(fields['inum']))
    
    # ensure file doesn't already exist, or else append a number
    inc_num = 0
    while os.path.exists(dest_name) and inc_num < 9999:
        inc_num += 1
        dest_name = os.path.join(series_dir,
                                    '{:05d}_{:04d}.dcm'.format(fields['inum'], inc_num))
    
    # move file
    logging.info('Moving file: {} -> {}'.format(path, dest_name))
    # shutil.move(path, dest_name)
    os.system('/bin/mv "{}" "{}"'.format(path, dest_name))
    os.chmod(dest_name, dest_permissions)

    return dest_name

# main
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Read DICOM header and move files accordingly to the correct destination.')
    parser.add_argument('--watch', action='store_true', help='Watch for new files in source directory')
    parser.add_argument('--verbose', action='store_true', help='Be verbose with filenames and actions')
    parser.add_argument('source_dir', type=str, help='Path to source directory')
    parser.add_argument('dest_dir', type=str, help='Path to destination directory')
    parser.add_argument('files', type=str, nargs='*', help='List of files to process')

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


    if args.watch:
        # watch for new files
        logging.info('Watching for new files in: {}'.format(args.source_dir))
        observer = Observer()
        observer.schedule(MyHandler(dest_dir=args.dest_dir), path=args.source_dir, recursive=False)
        observer.start()

        try:            
            # process all files in the directory right now
            files = [os.path.join(args.source_dir, f) for f in os.listdir(args.source_dir) if os.path.isfile(os.path.join(args.source_dir, f))]
            for f in files:
                try:
                    run_one_file(f, args.dest_dir)
                except Exception as ex:
                    logging.error('Error on file {}'.format(f), exc_info=ex)

            # keep running
            while True:
                time.sleep(5)

        finally:
            observer.stop()
            observer.join()

    else:
        # process files
        for f in args.files:
            run_one_file(f, args.dest_dir)
