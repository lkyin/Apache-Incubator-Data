import os
import shutil, errno

nested_path = './mbox/incubator/'
mpath = './mbox/'

projects = os.listdir(nested_path)

for project in projects:
	if '-' not in project:
		continue
	proj_name, foldername = project.split('-')
	if not os.path.exists(mpath+proj_name+os.sep+foldername):
		os.makedirs(mpath+proj_name+os.sep+foldername)
	mboxes = os.listdir(nested_path+project)
	for mbox in mboxes:
		ori_path = nested_path+project+os.sep+mbox
		des_path = mpath+proj_name+os.sep+foldername+os.sep+mbox
		shutil.copyfile(ori_path, des_path)
	print('{}/{} copied!'.format(proj_name, foldername))








