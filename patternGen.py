import re, sys, os, struct
import bs4
from bs4 import BeautifulSoup


directory = os.path.join(sys.path[0], "pin_test")
signal = {}


def name_check(file, name):
	filename = os.path.splitext(file)[0]
	if filename == name:
		print(file + " name check pass!")
	else:
		print(file + " name mismatch!")


def get_soup(file):
	path = os.path.join(directory, file)
	with open(path, "r") as f:
		soup = BeautifulSoup(f.read(), "xml")
	return soup


def write_testbench(fw, pos_dict):
	if not pos_dict:
		return
	numbers = [0] * 16
	for key, value in pos_dict.items():
		if key:
			numbers[key[0]-1] += 2 ** key[1] * int(value)
	for num in numbers:
		fw.write(struct.pack('B', num))
	# print("write success")


def write_mask():
	"""
	Run at the beginning of the process, and anytime en_tri changes.
	Write mask (pin input/output/inout status) to file.
	:return:
	"""
	pass


def write_operator():
	pass


"""File Parsers"""


def tcf_parser(file, sig2pin):
	soup = get_soup(file)
	name_check(file, soup.TCF['name'])
	for key, value in sig2pin.items():
		# FRAME & ASSEMBLY tag
		connect_tag = soup.find(pogo=value[:3])
		# TODO: Change the search parameter, or change attr 'name' to 'id'.
		# assembly_name = connect_tag['assembly']                 # should search by 'AS0101',
		wire_tag = soup.find('ASSEMBLY').find(pogopin=value[3:])  # not this
		# print(wire_tag)
		channel = connect_tag['plug'] + wire_tag['plugpin']

		# SIGMAP tag
		mapping_tag = soup.find(channel=channel)
		byte = int(mapping_tag['byte'])
		bit = int(mapping_tag['bit'])
		sig2pin[key] = (byte, bit)


"""
def tcf_parser(file, sig2pin):
	soup = get_soup(file)
	name_check(file, soup.TCF['name'])
	# FRAME tag
	for key, value in sig2pin.items():
		# FRAME tag
		channel = soup.find(pogo=value[:3])['plug'] + value[3:]
		# SIGMAP tag
		mapping_tag = soup.find(channel=channel)
		byte = int(mapping_tag['byte'])
		bit = int(mapping_tag['bit'])
		sig2pin[key] = (byte, bit)
"""


def lbf_parser(file, sig2pin):
	soup = get_soup(file)
	name_check(file, soup.LBF['name'])
	# dut_tag = soup.find('DUT').children
	for key in sig2pin:
		sig2pin[key] = soup.find(pin=sig2pin[key])['channel']
	# print(sig2pin)
	return sig2pin


def itm_parser(file):
	soup = get_soup(file)
	name_check(file, soup.ITEM['name'])
	return soup.find('CYCLE')['period']


def pio_parser(file):
	pio_dict = {}
	path = os.path.join(directory, file)
	regex = re.compile(r'NET\s+"(.+)"\s+DIR\s+=\s+(input|output|inout)(.*);', re.I)
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
					pio_dict[m.group(1)] = (io, tri)
	print(pio_dict)
	return pio_dict


def ucf_parser(file):
	sig2pin = {}
	path = os.path.join(directory, file)
	regex = re.compile('NET "(.+)" LOC = (.+);', re.I)
	with open(path, "r") as f:
		for line in f.readlines():
			m = regex.match(line)
			if m:
				sig2pin[m.group(1)] = m.group(2)
	return sig2pin


def vcd_parser(file, sig_dict):
	tick = -1
	def_state = True
	sym_dict = {}  # {symbolic_in_vcd: signal_name}
	pos_dict = {}  # {position(bit): signal(1|0|z|x)}
	path = os.path.join(directory, file)
	write_path = os.path.join(directory, os.path.splitext(file)[0] + ".bin")
	regex1 = re.compile(r'\$var .+ \d+ (.) (.+) \$end', re.I)   # match signal name
	regex2 = re.compile(r'#(\d+)')                              # match period
	regex3 = re.compile(r'([0|1|x|z])(.)')                      # match testbench
	with open(path, "r") as f, open(write_path, "wb") as fw:
		for line in f.readlines():
			# end of file
			if line == '$dumpoff':
				break

			# definition stage, return {symbol:signal, }
			if def_state:
				m1 = regex1.match(line)
				if m1:
					sym_dict[m1.group(1)] = sig_dict.setdefault(m1.group(2), None)
				else:
					if re.match(r'\$upscope', line):
						def_state = False
				continue
			else:
				# write last tick to file
				m2 = regex2.match(line)
				if m2:
					vcd_tick = m2.group(1)
					while True:
						write_testbench(fw, pos_dict)  # Write testbench to binary file.
						tick = tick + 1
						if tick == int(vcd_tick):
							pos_dict = {}
							break
					continue

				# match testbench
				m3 = regex3.match(line)
				if m3:
					value = m3.group(1)
					key = m3.group(2)
					pos_dict[sym_dict[key]] = value
					# TODO: interrupt when en_tri signal changes.


def tfo_parser(file):
	"""
	TODO: Multiple TEST tag, different attr 'name' and 'path'.
	TODO: Return file_dict like {test1:{path:'path', file1:'file1', ...}, test2:{...}, ...}.
	:param file:
	:return file_dict:
	"""
	soup = get_soup(file)
	name_check(file, soup.TFO['name'])
	file_dict = {}
	test_tag = soup.find('TEST')
	for child in test_tag.children:
		if type(child) == bs4.element.Tag:
			file_dict[child.name] = child['name'] + '.' + child.name.lower()
	return file_dict


def prepare(file):
	pass


"""Main process and test"""


def main():
	period = itm_parser("pin_test.itm")
	signal = ucf_parser("pin_test.ucf")
	lbf_parser("LB0101.lbf", signal)
	tcf_parser("F93K.tcf", signal)
	print(signal)
	pio_dict = pio_parser("pin_test.pio")
	write_mask(pio_dict)
	vcd_parser("pin_test.vcd", signal)


def test():
	# tcf_parser("F93K.tcf")
	# print(itm_parser("pin_test.itm"))
	# tfo_parser("tfo_demo.tfo")

	pio_parser("pin_test.pio")
	signal = ucf_parser("pin_test.ucf")
	print(signal)
	lbf_parser("LB0101.lbf", signal)
	print(signal)
	tcf_parser("F93K.tcf", signal)
	print(signal)
	# vcd_parser("pin_test.vcd", signal)


test()
