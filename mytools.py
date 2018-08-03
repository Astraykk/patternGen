#!/usr/bin/python3


def merge_ptn(ptn, *ptn_tuple):
	with open(ptn, 'rb+') as fw:
		for file in ptn_tuple:
			with open(file, 'rb') as fr:
				fw.write(fr.read())