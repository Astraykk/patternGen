# -*- coding:utf-8 -*-
import os
import sys
import bs4

# DIRECTORY = '/home/linaro/mysite/uploads'
DIRECTORY = sys.path[0]


def batch_test(i_file_list, o_file_list):
	app_path = '/home/linaro/BR0101/z7_v4_com/z7_v4_ip_app'
	for i in range(len(i_file_list)):
		i_file = i_file_list[i]
		o_file = o_file_list[i]
		msg = os.popen('sudo {} {} {} 1 1 1'.format(app_path, i_file, o_file)).read()
		print(msg)


def get_file_list(path, tfo):
	tfo_path = os.path.join(DIRECTORY, tfo)
	i_list = []
	o_list = []
	# print(path)
	with open(tfo_path, "r") as f:
		soup = bs4.BeautifulSoup(f.read(), "xml")
	for test_tag in soup.find_all('TEST'):
		base_path = os.path.join(DIRECTORY, test_tag['name'])
		i_list.append(base_path + '.ptn')
		o_list.append(base_path + '.trf')
	return i_list, o_list
