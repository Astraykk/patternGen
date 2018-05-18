import re, sys, os, struct
import bs4
from bs4 import BeautifulSoup
import time
import timeit

DIRECTORY = sys.path[0]
# TB_RELPATH = os.path.join(sys.path[0], "pin_test")
TB_RELPATH = "pin_test"
BS_RELPATH = "pin_test_bitstream"

# define operation code here
MASK_OP = 0x1
TESTBENCH_OP = 0x4
BITSTREAM_OP = None
# enddefine

# define other global constants
BIN_WIDTH = 128
BIN_BYTE_WIDTH = BIN_WIDTH / 8
BITSTREAM_WIDTH = 32
# enddefine

"""Tools"""


# decorator without parameter
def timer(func):
	def _timer():
		start_time = time.time()
		func()
		end_time = time.time()
		print("\nTotal time: " + str(end_time-start_time))
	return _timer


def name_check(file, name):
	filename = os.path.splitext(file)[0]
	if filename == name:
		print(file + " name check pass!")
	else:
		print(file + " name mismatch!")


def get_soup(relpath, file):
	path = os.path.join(DIRECTORY, relpath, file)
	with open(path, "r") as f:
		soup = BeautifulSoup(f.read(), "xml")
	return soup


def file_check(file_dict):
	"""
	Check file integrity.
	:return:
	"""
	pass


"""Write operation, mask, or testbench"""


def write_testbench(fw, pos_dict):
	if not pos_dict:
		# print("Nothing")
		return
	numbers = [0] * 16
	for key, value in pos_dict.items():
		if key:
			numbers[key[0]-1] += 2 ** key[1] * int(value)
			# numbers[key[0]-1] += int(value) << key[1]  # shift operation is faster?
	for num in numbers:
		fw.write(struct.pack('B', num))
	# print("write success")


def write_bitstream(fw, pos_dict, sig_dict, tick):
	pass


def write_operator(fw, operator, length):
	fw.write(struct.pack('B', operator))  # 1 byte
	for i in range(11):                   # length takes 4 bytes
		fw.write(struct.pack('B', 0xff))
	fw.write(struct.pack('>I', length))    # 4 bytes, big-endian


def write_tb_op(fw, tb_counter):
	if tb_counter:
		offset = - int((tb_counter + 1) * BIN_BYTE_WIDTH)
		fw.seek(offset, 1)    # locate the beginning of testbench
		write_operator(fw, TESTBENCH_OP, tb_counter)
		fw.seek(0, 2)         # return to end of file


def write_mask(fw, sig_dict, pio_dict, tb_counter):
	"""
	Run at the beginning of the process, and anytime en_tri changes.
	Write mask (pin input/output/inout status) to file.
	If there is any testbench written before, write op code for it.
	(Abandon) entri_dict: a dict contain the en_tri pin status, {en_tri1:0, en_tri2:1, ...}
	:return:
	"""
	numbers = [0xff] * 16
	write_tb_op(fw, tb_counter)
	write_operator(fw, MASK_OP, 1)
	for key, value in sig_dict.items():
		if pio_dict.setdefault(key, None) == 'input':  # TODO: maybe value in pio_dict should be 0/1?
			numbers[value[0]-1] -= 2 ** value[1]
	for num in numbers:
		fw.write(struct.pack('B', num))
	write_operator(fw, TESTBENCH_OP, 0)


"""File Parsers"""


class General(object):
	relpath = '.'
	pin2pos = {}
	file_list = []  # define file postion on the server (user doesn't have to upload)

	def __init__(self, relpath):
		self.relpath = relpath

	def pio_parser(self, file):
		pio_dict = {}
		entri_dict = {}
		path = os.path.join(DIRECTORY, self.relpath, file)
		regex = re.compile(r'NET\s+"(.+)"\s+DIR\s*=\s*(input|output|inout)(.*);', re.I)
		regex2 = re.compile(r'.*"(.*)"\s*')
		with open(path, "r") as f:
			for line in f.readlines():
				m = regex.match(line)
				if m:
					# print(m.groups())
					io = m.group(2).lower()
					pio_dict[m.group(1)] = io
					if io == 'inout':
						tri = regex2.match(m.group(3)).group(1)
						# print(1, tri)
						entri_dict[tri] = m.group(1)
		# print(pio_dict, entri_dict)
		return pio_dict, entri_dict

	def ucf_parser(self, file):
		sig2pin = {}
		path = os.path.join(DIRECTORY, self.relpath, file)
		regex = re.compile('NET "(.+)" LOC = (.+);', re.I)
		with open(path, "r") as f:
			for line in f.readlines():
				m = regex.match(line)
				if m:
					sig2pin[m.group(1)] = m.group(2)
		return sig2pin

	def lbf_parser(self, file):
		"""
		Difference from the outside version:
		return pin2channel instead of sig2channel.
		:param file:
		:return:
		"""
		soup = get_soup(self.relpath, file)
		name_check(file, soup.LBF['name'])

		pin2chl = {}
		# dut_tag = soup.find('DUT').children
		for tag in soup.find_all('channel'):
			pin2chl[tag['pin']] = tag['channel']
		return pin2chl

	def tcf_parser(self, file, pin2chl):
		soup = get_soup(relpath, file)
		name_check(file, soup.TCF['name'])
		for key, value in pin2chl.items():
			# FRAME & ASSEMBLY tag
			connect_tag = soup.find(pogo=value[:3])
			assembly_name = connect_tag['assembly']  # should search by 'AS0101',
			wire_tag = soup.find(code=assembly_name).find(pogopin=value[3:])  # not this
			# print(wire_tag)
			channel = connect_tag['plug'] + wire_tag['plugpin']

			# SIGMAP tag
			mapping_tag = soup.find(channel=channel)
			byte = int(mapping_tag['byte'])
			bit = int(mapping_tag['bit'])
			self.pin2pos[key] = (byte, bit)


# TODO: handle .tfo file, get file list.


def tcf_parser(relpath, file, sig2pin):
	soup = get_soup(relpath, file)
	name_check(file, soup.TCF['name'])
	for key, value in sig2pin.items():
		# FRAME & ASSEMBLY tag
		connect_tag = soup.find(pogo=value[:3])
		# TODO: Change the search parameter, or change attr 'name' to 'id'.
		assembly_name = connect_tag['assembly']                 # should search by 'AS0101',
		wire_tag = soup.find(code=assembly_name).find(pogopin=value[3:])  # not this
		# print(wire_tag)
		channel = connect_tag['plug'] + wire_tag['plugpin']

		# SIGMAP tag
		mapping_tag = soup.find(channel=channel)
		byte = int(mapping_tag['byte'])
		bit = int(mapping_tag['bit'])
		sig2pin[key] = (byte, bit)


def itm_parser(relpath, file):
	soup = get_soup(relpath, file)
	name_check(file, soup.ITEM['name'])
	return soup.find('CYCLE')['period']


def lbf_parser(relpath, file, sig2pin):
	soup = get_soup(relpath, file)
	name_check(file, soup.LBF['name'])
	# dut_tag = soup.find('DUT').children
	for key in sig2pin:
		sig2pin[key] = soup.find(pin=sig2pin[key])['channel']
	# print(sig2pin)
	return sig2pin


def tfo_parser(relpath, file):
	"""
	TODO: Multiple TEST tag, different attr 'name' and 'path'.
	TODO: Return file_dict like {test1:{path:'path', file1:'file1', ...}, test2:{...}, ...}.
	Format: {"lbf":"LB010tf1", dut:"LX200", "test":{"pin_test":{"path":".", }}}
	:param file:
	:return file_dict:
	"""
	soup = get_soup(relpath, file)
	name_check(file, soup.TFO['name'])
	file_dict = {}
	test_tag = soup.find('TEST')
	file_dict['relpath'] = test_tag['path']
	for child in test_tag.children:
		if type(child) == bs4.element.Tag:
			file_dict[child.name] = child['name'] + '.' + child.name.lower()
	return file_dict


def pio_parser(relpath, file):
	pio_dict = {}
	entri_dict = {}
	path = os.path.join(DIRECTORY, relpath, file)
	regex = re.compile(r'NET\s+"(.+)"\s+DIR\s*=\s*(input|output|inout)(.*);', re.I)
	regex2 = re.compile(r'.*"(.*)"\s*')
	with open(path, "r") as f:
		for line in f.readlines():
			m = regex.match(line)
			if m:
				# print(m.groups())
				io = m.group(2).lower()
				pio_dict[m.group(1)] = io
				if io == 'inout':
					tri = regex2.match(m.group(3)).group(1)
					# print(1, tri)
					entri_dict[tri] = m.group(1)
	# print(pio_dict, entri_dict)
	return pio_dict, entri_dict


def ucf_parser(relpath, file):
	sig2pin = {}
	path = os.path.join(DIRECTORY, relpath, file)
	regex = re.compile('NET "(.+)" LOC = (.+);', re.I)
	with open(path, "r") as f:
		for line in f.readlines():
			m = regex.match(line)
			if m:
				sig2pin[m.group(1)] = m.group(2)
	return sig2pin


def vcd_parser(relpath, file, sig_dict, pio_dict, entri_dict={}):
	tick = -1         # current tick
	tb_counter = -1    # length of testbench in operation code
	def_state = True  # definition state
	sym_dict = {}     # {symbolic_in_vcd: signal_name}
	pos_dict = {}     # {position(bit): signal(1|0|z|x)}
	path = os.path.join(DIRECTORY, relpath, file)
	write_path = os.path.join(DIRECTORY, relpath, os.path.splitext(file)[0] + ".bin")
	regex1 = re.compile(r'\$var .+ \d+ (.) (.+) \$end', re.I)   # match signal name
	regex2 = re.compile(r'#(\d+)')                              # match period
	regex3 = re.compile(r'([0|1|x|z])(.)')                      # match testbench

	if not os.path.exists(write_path):
		os.mknod(write_path)
	with open(path, "r") as f, open(write_path, "w+b") as fw:
		for line in f.readlines():
			# end of file
			if line == '$dumpoff':
				break

			# definition stage, return {symbol:signal, }
			if def_state:
				m1 = regex1.match(line)
				if m1:
					sym_dict[m1.group(1)] = m1.group(2)
				else:
					if re.match(r'\$upscope', line):
						def_state = False
				continue
			else:
				# write last tick to file
				m2 = regex2.match(line)
				if m2:
					vcd_tick = m2.group(1)
					while True:  # WARNING
						# if not pos_dict:  # ugly code
						# 	break
						# print(pos_dict)
						write_testbench(fw, pos_dict)  # Write testbench to binary file.
						print("#"+str(tick))
						tb_counter += 1
						tick += 1
						if tick == int(vcd_tick):
							# pos_dict = {}
							break
					continue

				# match testbench
				m3 = regex3.match(line)
				if m3:
					value = m3.group(1)
					key = m3.group(2)
					pos_dict[sig_dict.setdefault(sym_dict[key], None)] = value
					# print(sym_dict[key])
					# TODO: interrupt when en_tri signal changes.
					if sym_dict[key] in entri_dict:
						entri = sym_dict[key]  # TODO: change entri_dict
						# print(pos_dict[sig_dict[entri]])
						if pos_dict[sig_dict[entri]] == '1':
							pio_dict[entri_dict[entri]] = 'output'
						else:
							pio_dict[entri_dict[entri]] = 'input'
						# print(pio_dict)
						write_mask(fw, sig_dict, pio_dict, tb_counter)
						tb_counter = 0
		write_tb_op(fw, tb_counter)


"""Bitstream related"""


def get_sig_value(value=0, default=0, flag='const', tick=0):
	"""
	format:
		flag = 'const': value = 0/1, default = (don't care)
		flag = 'square': value = (don't care), default = 0/1
		flag = 'T': value=[[number1, 0/1], [number2, 0/1], ...], default = 0/1
	:param value:
	:param default:
	:param flag:
	:param tick:
	:return:
	"""
	if flag == 'const':
		return value
	if flag == 'square':
		return (tick + default) % 2
	if flag == 'T':
		if tick < value[0][0]:
			return default
		else:
			for t, v in value:
				if tick > t:
					return v


class BitstreamGen(General):
	atf_file = ''
	sig2val = {}    # {signal_name: {value, default, flag}, ...}
	btc2data = {}

	def __init__(self, relpath, atf_file):
		General.__init__(self, relpath)
		self.file_dict = self.atf_parser(atf_file)
		# TODO: get position dictionary
		self.pio_dict, whatever = General.pio_parser(self, self.file_dict['SPIO'])
		signal = General.ucf_parser(self, self.file_dict['SUCF'])
		lbf_parser(self.relpath, "LB0101.lbf.bak", signal)  # path of .lbf file???

	def atf_parser(self, file):
		soup = get_soup(self.relpath, file)
		name_check(file, soup.ATF['name'])
		# print(soup)

		file_dict = {}
		dwm_tag = soup.ATF.LIST.DWM
		file_dict['relpath'] = dwm_tag['path']
		for child in dwm_tag.children:
			if type(child) == bs4.element.Tag:
				file_dict[child.name] = child['name'] + '.' + child.name.lower()
		return file_dict

	def sbc_parser(self):
		file = self.file_dict['SBC']
		soup = get_soup(self.relpath, file)
		name_check(file, soup.SBC['name'])

		# Handle SIG tag
		for element in soup.find_all('SIG'):
			# print(element)
			ele_value = element['value']
			regex1 = re.compile(r'(const)([0|1])')  # flag = const
			m1 = regex1.search(ele_value)  # const has the highest priority
			if m1:
				flag, value = m1.groups()
			else:
				regex2 = re.compile(r'^(square)(\d+)T$')  # flag = square
				m2 = regex2.match(ele_value)
				if m2:
					flag, value = m2.groups()
					value = int(value)
				else:
					regex3 = re.compile(r'(\d+)T([0|1])')  # flag = T
					m3 = regex3.findall(ele_value)
					if m3:
						value = [map(int, x) for x in m3]
						flag = 'T'
					else:  # collect default
						flag = ''
						value = 0
			default = int(element['default'])
			self.sig2val[element['name']] = {'value': value, 'flag': flag, 'default': default}

		# Handle BTC tag
		btc_tag = soup.find('BTC')
		# print(btc_tag)
		self.btc2data['start'] = int(btc_tag['start'][:-1])
		for child in btc_tag.find_all('DATA'):
			# print(children)
			num = (int(child['byte']) - 1) * 8 + 7 - int(child['bit'])
			self.btc2data[num] = child['name']

	def rbt_generator(self):
		"""
		Generator, yield the position of bitstream.
		:return:
		"""
		file = self.file_dict['RBT']
		path = os.path.join(DIRECTORY, self.relpath, file)
		write_path = os.path.join(DIRECTORY, os.path.splitext(file)[0] + ".bin")

		with open(path, 'r') as f, open(write_path, 'wb+') as fw:
			for i in range(7):  # skip the first 7 lines
				f.readline()
			while f.readline():
				pos_dict = {}
				line = f.readline()
				for i in range(BITSTREAM_WIDTH):
					pos_dict[pin_dict[btc2data[i]]] = line[i]
				print(pos_dict)
				yield pos_dict

	def write(self):
		pass


"""Main process and test"""


def testbenchGen():
	pio_dict, entri_dict = pio_parser(TB_RELPATH, "pin_test.pio")
	print("pio_dict = " + str(pio_dict))
	print("entri_dict = " + str(entri_dict))
	signal = ucf_parser(TB_RELPATH, "pin_test.ucf")
	print(signal)
	lbf_parser(TB_RELPATH, "LB0101.lbf.bak", signal)
	print(signal)
	tcf_parser(TB_RELPATH, "F93K.tcf", signal)
	print("sig_dict = " + str(signal))
	vcd_parser(TB_RELPATH, "pin_test.vcd", signal, pio_dict, entri_dict)
	print("Finished")


def bitstreamGen():
	pio_dict, entri_dict = pio_parser(BS_RELPATH, "LX200.spio")
	print("pio_dict = " + str(pio_dict))
	signal = ucf_parser(BS_RELPATH, "LX200.sucf")
	print(signal)
	lbf_parser("LB0101.lbf.bak", signal)
	print(signal)


def main():
	pass


@timer
def test():
	SIG_dict, BTC_dict = sbc_parser(BS_RELPATH, 'LX200.sbc')
	print(SIG_dict)
	print(BTC_dict)
	sfile_dict = atf_parser(BS_RELPATH, 'pin_test.atf')
	print(sfile_dict)
	file_dict = tfo_parser(TB_RELPATH, 'tfo_demo.tfo')
	print(file_dict)
	pio_dict, entri_dict = pio_parser(BS_RELPATH, "LX200.spio")
	print("pio_dict = " + str(pio_dict))
	signal = ucf_parser(BS_RELPATH, "LX200.sucf")
	print(signal)


# bitstream = BitstreamGen(relpath=BS_RELPATH, atf_file='pin_test.atf')
# while input("\nPress q to exit:") == 'q':
# 	bitstream.rbt_generator()

test()
