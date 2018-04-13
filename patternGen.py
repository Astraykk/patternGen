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


def write_bin(fw, pos_dict):
	if not pos_dict:
		return
	numbers = [0] * 16
	for key, value in pos_dict.items():
		if key:
			# print(key, type(key))
			numbers[key[0]-1] += 2 ** key[1] * int(value)
			# print(number)
	for num in numbers:
		fw.write(struct.pack('B', num))
	# print("write success")


"""File Parsers"""


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
			# print(line)
			if def_state:
				m1 = regex1.match(line)
				# print(m1)
				if m1:
					# print(m1.groups())
					sym_dict[m1.group(1)] = sig_dict.setdefault(m1.group(2), None)
					# print(sym_dict)
				else:
					if re.match(r'\$upscope', line):
						def_state = False
						# print("definition finished")
				continue  # cotinue what?
			else:
				# print("match testbench")
				m2 = regex2.match(line)
				if m2:
					vcd_tick = m2.group(1)
					while True:
						write_bin(fw, pos_dict)  # Write testbench to binary file.
						tick = tick + 1
						if tick == int(vcd_tick):
							# print(pos_dict, "break")
							pos_dict = {}
							break
					continue

				m3 = regex3.match(line)
				if m3:
					value = m3.group(1)
					key = m3.group(2)
					pos_dict[sym_dict[key]] = value
		# write_bin(fw, pos_dict)


def tfo_parser(file):
	soup = get_soup(file)
	name_check(file, soup.TFO['name'])
	file_dict = {}
	test_tag = soup.find('TEST')
	for child in test_tag.children:
		if type(child) == bs4.element.Tag:
			file_dict[child.name] = child['name'] + '.' + child.name.lower()
	# print(file_dict)
	# print(file_dict['ITM'])
	return file_dict


def prepare(file):
	pass


def main():
	period = itm_parser("pin_test.itm")


def test():
	# tcf_parser("F93K.tcf")
	# print(itm_parser("pin_test.itm"))
	# tfo_parser("tfo_demo.tfo")

	signal = ucf_parser("pin_test.ucf")
	# print(signal)
	lbf_parser("LB0101.lbf", signal)
	print(signal)
	tcf_parser("F93K.tcf", signal)
	print(signal)
	# vcd_parser("pin_test.vcd", signal)
	pio_parser("pin_test.pio")


test()
