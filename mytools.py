#!/usr/bin/python3
import re
import sys


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


def timescale_op(ts):
	regex = re.compile(r'(\d+)(\w*)', re.I)
	m = regex.match(ts)
	if m:
		unit = m.group(2)
		if unit == 'p' or unit == 'ps':
			multiplier = 1
		elif unit == 'n' or unit == 'ns':
			multiplier = 1000
		else:
			multiplier = 1000000
		ts_int = int(m.group(1)) * multiplier
	else:
		ts_int = 1
	return ts_int


class VcdFile(object):
	# Define waveform state
	ZERO_ZERO = 1
	ZERO_ONE = 2
	ONE_ZERO = 3
	ONE_ONE = 4
	BUS_SINGLE = 5
	BUS_START = 6
	BUS_BODY = 7
	BUS_END = 8

	path = ''
	module_name = ''
	total_length = 0
	sym2sig = {}
	entri_dict = {}
	header = {'timescale': '1ps', 'version': 'ModelSim Version 10.1c', 'date': ''}
	wave_state = []
	vcd_info = []
	# vcd_info = [
	# 	{
	# 		'symbol': '!', 'sig': 'clk', 'type': 'single', 'wave_info': [0, 1, 0, 1],
	# 		'wave_state': [ZERO_ZERO, ZERO_ONE, ONE_ZERO, ZERO_ONE]
	# 	},
	# 	{
	# 		'symbol': '"', 'sig': 'a', 'type': 'bus', 'wave_info': ['0000', '0001', '0001', '0010', '0010', '0010', '0010'],
	# 		'wave_state': [BUS_SINGLE, BUS_START, BUS_END, BUS_START, BUS_BODY, BUS_BODY, BUS_END]
	# 	}
	# ]

	def __init__(self, path, period='1ps'):
		self.path = path
		self.period = period
		# self.get_header()
		self.get_vcd_info()

	def merge(self, *vcd_files):
		"""
		Merge multiple vcd files.
		:param vcd_ref: a VcdFile object
		:return: 
		"""
		for vcd_file in vcd_files:
			pass

	def get_header(self):
		self.header['timescale'] = int(timescale_op(self.period) / timescale_op('1ps'))

	def get_vcd_info(self):
		tick = 0
		timescale = int(timescale_op(self.period) / timescale_op(self.header['timescale']))
		regex1 = re.compile(r'\$var\s+\w+\s+\d+\s+(.)\s+(\w+)\s*(\[(\d+)(:?)(\d*)\])?\s+\$end', re.I)
		# regex2 = re.compile(r'\$enddefinitions \$end')
		regex2 = re.compile(r'#(\d+)')  # match period
		regex3 = re.compile(r'b?([0|1|x|z]+)\s*(.)')  # match testbench
		with open(self.path, "r") as f:
			content = f.read()  # TODO: match signal definitions here.
			self.module_name = re.findall(r'\$scope module (\w+) \$end', content)[0]
			f.seek(0)
			for line in f.readlines():
				# print(self.vcd_info)
				m3 = regex3.match(line)
				if m3:
					value, key = m3.group(1, 2)
					# print(key, value)
					i = ord(key) - 33  # ASCII value
					if key not in self.sym2sig:
						continue
					if isinstance(self.sym2sig[key], tuple):
						bus_ele = self.sym2sig[key]
						bus_width = bus_ele[1] - bus_ele[2]
						# print("{} {}".format(bus_width, bus_ele))
						# bus_signal = bus_width > 0 and 1 or -1
						value = '0' * (abs(bus_width) + 1 - len(value)) + value  # Fill 0 on the left
						# for i in range(0, bus_width + bus_signal, bus_signal):
						# 	bus_sig = '{}[{}]'.format(bus_ele[0], str(bus_ele[1] - i))
						# 	# print("tick={} {} {}".format(tick, bus_sig, self.sig2pos))
						# 	# print("i={}, value={}".format(i, value))
						# 	pos2val[self.sig2pos.setdefault(bus_sig, None)] = value[abs(i)]
					# print('ok')
					# print('signal = %s, value = %s' % (bus_sig, value[abs(i)]))
					# else:
					# 	if value == 'x':
					# 		value = x_val
					# 	if value == 'z':
					# 		value = z_val
					# 	pos2val[self.sig2pos.setdefault(self.sym2sig[key], None)] = value
					self.vcd_info[i]['wave_info'].append(value)
					continue

				# match next tick; write last tick to file
				m2 = regex2.match(line)
				if m2:
					vcd_tick_raw = int(m2.group(1))
					if vcd_tick_raw == 0 or vcd_tick_raw % timescale:  # small delay, skip the write operation
						continue
					else:
						vcd_tick = int(vcd_tick_raw / timescale)
					# if tick < vcd_tick:
					for sig_dict in self.vcd_info:
						last_val = sig_dict['wave_info'][-1]
						sig_dict['wave_info'] += [last_val] * (vcd_tick-len(sig_dict['wave_info']))
					continue

				m = regex1.match(line)
				if m:
					sym = m.group(1)
					if m.group(5):  # Combined bus
						msb = int(m.group(4))
						lsb = int(m.group(6))
						sig_type = 'bus'
						sig = m.group(2)
						self.sym2sig[sym] = (sig, msb, lsb)  # symbol => (bus, MSB, LSB)
					elif m.group(3):
						sig = m.group(2) + m.group(3)
						sig_type = 'single'
						self.sym2sig[sym] = sig
					# elif m.group(2) not in self.sig2pos.keys():
					# 	continue
					else:
						sig = m.group(2)
						sig_type = 'single'
						self.sym2sig[sym] = sig
					sig_dict = {'symbol': sym, 'signal': sig, 'type': sig_type, 'wave_info': [], 'wave_state': []}
					self.vcd_info.append(sig_dict)
					# print(self.vcd_info, len(self.vcd_info))
					continue
				if re.search(r'\$dumpoff', line):
					break
		print(f)

	def get_wave_info(self):
		pass

	def get_tick(self):
		pass

	def gen_waveform(self, path, mode):
		pass

	def gen_vcd(self, path):
		with open(path, 'w') as f:
			for header in ['date', 'version', 'timescale']:
				f.write('${}\n\t{}\n$end\n'.format(header, self.header[header]))
			f.write('$scope module {}_tb $end\n'.format(self.module_name))


def vcd_merge(vcd_ref, vcd_add, period=1):
	"""
	Extract signal definition; assign symbol; merge file.
	:param vcd_ref:
	:param vcd:
	:return:
	"""
	tick_ref = -1
	tick_add = -1
	x_val = 0  # default value of x
	z_val = 0
	pos2val = {}  # {position(bit): signal(1|0|z|x)}
	regex1 = re.compile(r'\$var\s+\w+\s+\d+\s+(.)\s+(\w+)\s*(\[(\d+)(:?)(\d*)\])?\s+\$end', re.I)
	regex2 = re.compile(r'#(\d+)')  # match period
	regex3 = re.compile(r'b?([0|1|x|z]+)\s*(.)')  # match testbench
	regex4 = re.compile(r'\$enddefinitions \$end')
	with open(vcd_ref, "r") as fr, open(vcd_add, 'r') as fa, open('vcd_final.vcd', 'w') as ff:
		pass


if __name__ == "__main__":
	# compare_ptn('counter/counter.ptn', 'counter/counter.ptn.bak1207')
	# vcd = VcdFile('pin_test/pin_test.vcd', period='1ps')
	vcd = VcdFile('counter/counter.vcd', period='1ps')
	# print(vcd.sym2sig)
	# print(vcd.vcd_info)
	# print(sys.getsizeof(vcd.vcd_info[0]['wave_info']))
	print(vcd.module_name)
