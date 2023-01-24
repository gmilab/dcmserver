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


class MyHandler(FileSystemEventHandler):
    def __init__(self, dest_dir) -> None:
        self.dest_dir = dest_dir
        super().__init__()

    def on_closed(self, event):
        logging.info('File closed: {}'.format(event.src_path))
        run_one_file(event.src_path, self.dest_dir)


def run_one_file(path: str, dest_dir: str):
    # read dicom header
    ds = pydicom.dcmread(path, stop_before_pixels=True)

    # get and format needed fields
    alphanum = lambda v: find_non_alpha.sub('_', str(v).strip())
    fields = {
        'id': alphanum(ds.PatientID),
        'name': alphanum(ds.PatientName),
        'snum': int(ds.SeriesNumber),
        'sdesc': alphanum(ds.SeriesDescription),
        'inum': int(ds.InstanceNumber),
    }

    # construct destination directory
    dir_name = os.path.join(dest_dir, 
                            '{}+{}'.format(fields['id'], fields['name']),
                            '{:03d}-{}'.format(fields['snum'], fields['sdesc']))
    
    if not os.path.exists(dir_name):
        logging.info('Creating directory: {}'.format(dir_name))
        os.makedirs(dir_name)

    # construct destination file name
    file_name = os.path.join(dir_name,
                                '{:05d}.dcm'.format(fields['inum']))
    
    # ensure file doesn't already exist, or else append a number
    inc_num = 0
    while os.path.exists(file_name) and inc_num < 9999:
        inc_num += 1
        file_name = os.path.join(dir_name,
                                    '{:05d}_{:04d}.dcm'.format(fields['inum'], inc_num))
    
    # move file
    logging.info('Moving file: {} -> {}'.format(path, file_name))
    shutil.move(path, file_name)

    return file_name

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
                run_one_file(f, args.dest_dir)

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
