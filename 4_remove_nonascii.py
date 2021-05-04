# coding: utf-8
import os
from tqdm import tqdm

# clear all non-ascii codes
nonascii = bytearray(range(0x80, 0x100))
base_path = './mbox'
new_path = './ascii_mbox'
project_list = os.listdir(base_path)

for proj in tqdm(project_list):
    if proj == 'asf-wide' or proj == 'incubator':
        continue
    mbox_id_set = set()
    project_path = base_path+os.sep+proj
    p_folders = os.listdir(project_path)
    for folder in p_folders:
        folder_path = project_path+os.sep+folder
        mboxes = os.listdir(folder_path)
        for mbox in mboxes:
            new_folder_path = new_path+os.sep+proj+os.sep+folder
            if not os.path.exists(new_folder_path):
                os.makedirs(new_folder_path)
            with open(folder_path+os.sep+mbox,'rb') as infile, open(new_folder_path+os.sep+mbox,'wb') as outfile:
                for line in infile: # b'\n'-separated lines (Linux, OSX, Windows)
                    outfile.write(line.translate(None, nonascii))