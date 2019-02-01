# -*- coding:utf-8 -*-
import os
import sys
import bs4

DIRECTORY = '/home/linaro/mysite/uploads'
app_path = '/home/linaro/BR0101/z7_v4_com/z7_v4_ip_app'
base_command = 'sudo {} {} {} 1 1 1'
if not os.path.exists(DIRECTORY):
	DIRECTORY = sys.path[0]
if not os.path.exists(app_path):
	app_path = '/home/keylab/BR0101/z7_v4_com/z7_v4_ip_app.py'
	base_command = 'python3 {} {} {}'


def batch_test(i_file_list, o_file_list):
	for i in range(len(i_file_list)):
		i_file = i_file_list[i]
		o_file = o_file_list[i]
		msg = os.popen(base_command.format(app_path, i_file, o_file)).read()
		print(msg)


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


if __name__ == "__main__":
	if len(sys.argv) == 2:
		i_list, o_list = get_file_list(sys.argv[1])
		batch_test(i_list, o_list)
