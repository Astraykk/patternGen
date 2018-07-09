#!/usr/bin/python3.5
import binascii
from crc32c import crc32
import struct
import time
END = 1605109


def timer(func):
	# decorator without parameter
	def _timer():
		start_time = time.time()
		func()
		end_time = time.time()
		print("\nTotal time: " + str(end_time-start_time))
	return _timer


def ascii2bin(start, end):
	content = b''
	with open("pin_test.rbt", 'r') as f, open('out.bin', 'wb') as fw:
		# lines = f.readlines()
		for line in f.readlines()[start:end]:
			byte = struct.pack('<I', int(line, 2))
			fw.write(byte)
			# content += byte
	# return content

@timer
def test():
	ascii2bin(7, END+2)
	with open('out.bin', 'rb') as f:
		content = f.read()
		# print(type(content))
		# print(len(content)/4)
		# print(content[0:4])
		# print(content[4:8])
		# print(content[(END-7)*4:])
		# print(content[-8])
		# for item in content[:-4:-1]:
		# 	print("0x%x" % item)
		for start in [7, 8, 9]:
			for end in [END, END+1, END+2]:

				crc = crc32(content[(start-7)*4:(end-7)*4]) & 0xffffffff
				print('start = %d, end = %d:' % (start, end))
				if crc == 0xfe45c2b8:
					print('Match!')
				else:
					print('Mismatch...crc = 0x%x' % crc)


test()

