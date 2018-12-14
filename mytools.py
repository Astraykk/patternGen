#!/usr/bin/python3
def merge_ptn(ptn, *ptn_tuple):
	with open(ptn, 'rb+') as fw:
		for file in ptn_tuple:
			with open(file, 'rb') as fr:
				fw.write(fr.read())


def compare_ptn(file_1, file_2):
	line_cnt = 0
	with open(file_1, 'rb') as f1, open(file_2, 'rb') as f2:
		while True:
			line_cnt += 1
			line1 = f1.read(16)
			line2 = f2.read(16)
			if line1 != line2:
				print("Files differ at line %d\n" % line_cnt)
				print("{}: {}\n".format(file_1, line1))
				print("{}: {}\n".format(file_2, line2))
				break
			if not line1:
				break
		print("Comparison finished!")


if __name__ == "__main__":
	compare_ptn('counter/counter.ptn', 'counter/counter.ptn.bak1207')
