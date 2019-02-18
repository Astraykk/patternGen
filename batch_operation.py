# -*- coding:utf-8 -*-
"""
Dependencies:
beautiful soup

Path:


Usage:
$ python batch_operation.py
Choose operation: build(0), test(1), trf2vcd(2)
(If you want execute multiple operations in a row, input the corresponding digits
like 01, 12, or 012)
build
Input project path:
pin_test
Input tfo file name:
tfo_demo.tfo
"""
import os
import sys
import bs4
from patternGen import PatternGen

DIRECTORY = '/home/linaro/mysite/uploads'
app_path = '/home/linaro/BR0101/z7_v4_com/z7_v4_ip_app'
base_command = 'sudo {} {} {} 1 1 1'
if not os.path.exists(DIRECTORY):
	DIRECTORY = sys.path[0]
if not os.path.exists(app_path):
	app_path = '/home/keylab/BR0101/z7_v4_com/z7_v4_ip_app.py'
	base_command = 'python3 {} {} {}'


def name_check(file, name):
	filename = os.path.splitext(file)[0]
	if filename == name:
		print(file + " name check pass!")
	else:
		print(file + " name mismatch!")


def get_soup(path, file):
	path = os.path.join(path, file)
	# print(path)
	with open(path, "r") as f:
		soup = bs4.BeautifulSoup(f.read(), "xml")
	return soup


def get_file_list(tfo):
	tfo_path = os.path.join(DIRECTORY, tfo)
	i_list = []
	o_list = []
	# print(path)
	with open(tfo_path, "r") as f:
		soup = bs4.BeautifulSoup(f.read(), "xml")
	for test_tag in soup.find_all('TEST'):
		project_path = test_tag['path']
		base_path = os.path.join(DIRECTORY, project_path, test_tag['name'])
		print(base_path)
		i_list.append(base_path + '.ptn')
		o_list.append(base_path + '.trf')
	return i_list, o_list


def tfo_parser(path, file):
	"""
	:param path:
	:param file:
	:return file_list_list:
	"""
	file_list_list = {}
	soup = get_soup(path, file)
	name_check(file, soup.TFO['name'])
	for test_tag in soup.find_all('TEST'):
		file_list = {
			'PTN': test_tag['name'] + '.ptn',
			'LBF': soup.TFO.LBF['type'] + '.lbf',
			'TCF': 'F93K.tcf'
		}
		project_name = test_tag['name']
		for child in test_tag.children:
			if type(child) == bs4.element.Tag:
				if child.name == 'DWM' or child.name == 'BIT':
					file_list[child.name] = child['name']
				else:
					file_list[child.name] = child['name'] + '.' + child.name.lower()
		file_list_list[test_tag['path']] = (project_name, file_list)
	print(file_list_list)
	return file_list_list


def batch_build(path, tfo):
	print('Start batch build')
	file_list_list = tfo_parser(path, tfo)
	for project_path, file_list in file_list_list.items():
		pattern = PatternGen(os.path.join(path, project_path), file_list=file_list)
		pattern.write()
	print('Batch build finished')


def batch_test(i_file_list, o_file_list):
	for i in range(len(i_file_list)):
		i_file = i_file_list[i]
		o_file = o_file_list[i]
		msg = os.popen(base_command.format(app_path, i_file, o_file)).read()
		print(msg)


def batch_trf2vcd():
	pass


if __name__ == "__main__":
	if len(sys.argv) == 2:
		i_list, o_list = get_file_list(sys.argv[1])
		batch_test(i_list, o_list)