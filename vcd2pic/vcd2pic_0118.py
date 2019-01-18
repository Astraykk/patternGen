import re
import enum
import os
import sys
import getopt
from PIL import Image, ImageDraw, ImageFont
#constants for state shift
class State(enum.Enum):
	I_X_X = 0
	I_Z_X = 1
	I_0_X = 2
	I_1_X = 3
	I_X_Z = 4
	I_Z_Z = 5
	I_0_Z = 6
	I_1_Z = 7
	I_X_0 = 8
	I_Z_0 = 9
	I_0_0 = 10
	I_1_0 = 11
	I_X_1 = 12
	I_Z_1 = 13
	I_0_1 = 14
	I_1_1 = 15
	I_BUS_X = 16
	I_BUS_Z = 17
	I_BUS_KEEP = 18
	I_BUS_TRAN = 19
	I_BUS_INIT = 20
def vcd2pic(vcd_location, pic_location):
	with open(vcd_location) as vcd:
		inputs = []
		outputs = []
		for each_line in vcd:
			word = each_line.strip().split()
			if not word:
				continue
			#print(word)
			if word[0] == '$date':
				date = vcd.readline()
				#print(date)
			if word[0] == '$version':
				version = vcd.readline()
				#print(version)
			if word[0] == '$timescale':
				timescale = vcd.readline()
				timescale_value = re.search(r'\d',timescale).group()
				timescale_scale = re.search(r'[a-z]{1,2}',timescale).group()
				'''
				print(timescale)
				print(timescale_value)
				print(timescale_scale)
				'''
			if word[0] == '$scope':
				module_name = word[2]
				#print(module_name)
			if word[0] == '$var':
				if word[1] == "reg":
					inputs.append({'name':word[4],'sign':word[3],'timescale':word[2],'wave':[],'state':[]})
				if word[1] == "wire":
					outputs.append({'name':word[4],'sign':word[3],'timescale':word[2],'wave':[],'state':[]})
			line = each_line
			#print('line',line)
			isno1timestamp = False
			unittime = '0'
			# if #1 follows #0, unittime=1
			# if #10 follows #0, unittime=10
			# and so on so forth
			while re.search(r'^#',line):
				time = re.search(r'\d+',line).group()
				#print('time',time)
				line = vcd.readline()
				#print('line',line)
				if line == '$dumpvars\n':
					waveout = inputs + outputs
					line = vcd.readline()
					#print('line',line)
				for i in range(len(waveout)):
					if int(time) != 0:
						#print('appending on new cycle')
						waveout[i]['wave'].append(waveout[i]['wave'][-1])
						if not isno1timestamp:
							#print('reducing')
							isno1timestamp = True
							unittime = time
							def reduce_timescale(time,t_scale):
								t_grades = ['p','n','u','m','','k','M','G']
								reduced_time = time.rstrip('0')
								promotionnum = (len(time) - len(reduced_time)) // 3
								if(promotionnum == 0):
									return int(time),t_scale
								else:
									newscale = t_grades.index(t_scale[0]) + promotionnum
									t_scale = t_grades[newscale] + t_scale[-1]
									reduced_time = time[:-promotionnum * 3]
									return int(reduced_time),t_scale
							unittimeint,timescale_scale = reduce_timescale(unittime,timescale_scale)
							#print(unittime,timescale_scale)
				#print(waveout)
				while (re.search(r'^[bodh]?[0-9a-fxz]+',line,re.I)):
					sign = re.search(r'([bodh]?)([0-9a-fxz]+)(\s?)(.)',line,re.I)
					#print(sign.group())
					for i in range(len(waveout)):
						if sign.group(4) == waveout[i]['sign']:
							#print('old:',waveout[i])
							#print(sign.group(4))
							if int(time) == 0:
								waveout[i]['wave'].append(sign.group(2))
							else:
								waveout[i]['wave'][-1] = sign.group(2)
							#print('new:',waveout[i])
					line = vcd.readline()
					#print('line',line)
				if line == '$end\n':
					line = vcd.readline()
					#print('line',line)
					continue
	for i in range(len(waveout)):
		if(waveout[i]['timescale'] == '1'):
			for j in range(len(waveout[i]['wave'])):
				if j == 0:
					now_wave = waveout[i]['wave'][j]
					if now_wave == 'x':
						waveout[i]['state'].append(State.I_X_X)
					elif now_wave == 'z':
						waveout[i]['state'].append(State.I_Z_Z)
					elif now_wave == '0':
						waveout[i]['state'].append(State.I_0_0)
					elif now_wave == '1':
						waveout[i]['state'].append(State.I_1_1)
				else:
					b_wave = waveout[i]['wave'][j - 1]
					now_wave = waveout[i]['wave'][j]
					if b_wave == 'x' and now_wave == 'x':
						waveout[i]['state'].append(State.I_X_X)
					elif b_wave == 'z' and now_wave == 'x':
						waveout[i]['state'].append(State.I_Z_X)
					elif b_wave == '0' and now_wave == 'x':
						waveout[i]['state'].append(State.I_0_X)
					elif b_wave == '1' and now_wave == 'x':
						waveout[i]['state'].append(State.I_1_X)
					elif b_wave == 'x' and now_wave == 'z':
						waveout[i]['state'].append(State.I_X_Z)
					elif b_wave == 'z' and now_wave == 'z':
						waveout[i]['state'].append(State.I_Z_Z)
					elif b_wave == '0' and now_wave == 'z':
						waveout[i]['state'].append(State.I_0_Z)
					elif b_wave == '1' and now_wave == 'z':
						waveout[i]['state'].append(State.I_1_Z)
					elif b_wave == 'x' and now_wave == '0':
						waveout[i]['state'].append(State.I_X_0)
					elif b_wave == 'z' and now_wave == '0':
						waveout[i]['state'].append(State.I_Z_0)
					elif b_wave == '0' and now_wave == '0':
						waveout[i]['state'].append(State.I_0_0)
					elif b_wave == '1' and now_wave == '0':
						waveout[i]['state'].append(State.I_1_0)
					elif b_wave == 'x' and now_wave == '1':
						waveout[i]['state'].append(State.I_X_1)
					elif b_wave == 'z' and now_wave == '1':
						waveout[i]['state'].append(State.I_Z_1)
					elif b_wave == '0' and now_wave == '1':
						waveout[i]['state'].append(State.I_0_1)
					elif b_wave == '1' and now_wave == '1':
						waveout[i]['state'].append(State.I_1_1)
		else:
			for j in range(len(waveout[i]['wave'])):
				if j == 0:
					waveout[i]['state'].append(State.I_BUS_INIT)
					#print('start bus')
				else:
					b_wave = waveout[i]['wave'][j - 1]
					now_wave = waveout[i]['wave'][j]
					if b_wave == now_wave:
						waveout[i]['state'].append(State.I_BUS_KEEP)
					else:
						waveout[i]['state'].append(State.I_BUS_TRAN)
	#print(waveout)
	#print(timescale_scale)
	
	red = (255, 0, 0)
	green = (0, 255, 0)
	blue = (0, 0, 255)
	tint_green = (0, 80, 0)
	tint_write = (255, 255, 255)
	unit_width = 40
	width = unit_width * (len(waveout[0]['state']) + 3)
	unit_height = 20
	height = unit_height * (len(waveout) + 1)

	image = Image.new('RGB', (width, height), (0, 0, 0))

	draw = ImageDraw.Draw(image)

	font = ImageFont.truetype('arial.ttf', 12)

	def to_zero(x_st, y_st, x_off, y_off, prev_v):
		#draw the 1st column
		if prev_v == 'x':
			for y in range(y_st + int(0.6 * y_off), y_st + y_off):
				draw.point((x_st, y), fill=green)
		elif prev_v == 'z':
			for y in range(y_st + int(0.6 * y_off), y_st + y_off):
				draw.point((x_st, y), fill=green)
		elif prev_v == '0':
			draw.point((x_st, y_st + y_off - 1), fill=green)
		elif prev_v == '1':
			for y in range(y_st + int(0.2 * y_off), y_st + y_off):
				draw.point((x_st, y), fill=green)
		#draw the rest
		for x in range(x_st + 1, x_st + x_off):
			draw.point((x, y_st + y_off - 1), fill=green)

	def to_one(x_st, y_st, x_off, y_off, prev_v):
		#draw the 1st column
		if prev_v == 'x':
			for y in range(y_st + int(0.2 * y_off), y_st + int(0.6 * y_off) + 1):
				draw.point((x_st, y), fill=green)
		elif prev_v == 'z':
			for y in range(y_st + int(0.2 * y_off), y_st + int(0.6 * y_off) + 1):
				draw.point((x_st, y), fill=green)
		elif prev_v == '0':
			for y in range(y_st + int(0.2 * y_off), y_st + y_off):
				draw.point((x_st, y), fill=green)
		elif prev_v == '1':
			for y in range(y_st + int(0.2 * y_off), y_st + y_off):
				draw.point((x_st, y), fill=tint_green)
			draw.point((x_st, y_st + int(0.2 * y_off)), fill=green)
		#draw the rest
		for x in range(x_st + 1, x_st + x_off):
			for y in range(y_st + int(0.2 * y_off), y_st + y_off):
				if y > y_st + int(0.2 * y_off):
					draw.point((x, y), fill=tint_green)
				elif y == y_st + int(0.2 * y_off):
					draw.point((x, y), fill=green)

	def to_x(x_st, y_st, x_off, y_off, prev_v):
		#draw the 1st column
		if prev_v == 'x':
			draw.point((x_st, int(y_st + 0.6 * y_off)), fill=red)
		elif prev_v == 'z':
			draw.point((x_st, int(y_st + 0.6 * y_off)), fill=red)
		elif prev_v == '0':
			for y in range(y_st + int(0.6 * y_off), y_st + y_off):
				draw.point((x_st, y), fill=red)
		elif prev_v == '1':
			for y in range(y_st + int(0.2 * y_off), y_st + int(0.6 * y_off) + 1):
				draw.point((x_st, y), fill=red)
		#draw the rest
		for x in range(x_st + 1, x_st + x_off):
			draw.point((x, y_st + int(0.6 * y_off)), fill=red)

	def to_z(x_st, y_st, x_off, y_off, prev_v):
		#draw the 1st column
		if prev_v == 'x':
			draw.point((x_st, int(y_st + 0.6 * y_off)), fill=blue)
		elif prev_v == 'z':
			draw.point((x_st, int(y_st + 0.6 * y_off)), fill=blue)
		elif prev_v == '0':
			for y in range(y_st + int(0.6 * y_off), y_st + y_off):
				draw.point((x_st, y), fill=blue)
		elif prev_v == '1':
			for y in range(y_st + int(0.2 * y_off), y_st + int(0.6 * y_off) + 1):
				draw.point((x_st, y), fill=blue)
		#draw the rest
		for x in range(x_st + 1, x_st + x_off):
			draw.point((x, y_st + int(0.6 * y_off)), fill=blue)

	def bus_body(x_st, y_st, x_off, y_off, color=green):
		y = y_st + int(y_off * 0.2)
		for x in range(x_st + 2,x_st + x_off - 2):
			draw.point((x, y), fill=color)
		y = y_st + y_off
		for x in range(x_st + 2,x_st + x_off - 2):
			draw.point((x, y), fill=color)

	def bus_continous(x_st, y_st, x_off, y_off, color=green):
		y = y_st + int(y_off * 0.2)
		for x in range(x_st - 2,x_st + 2):
			draw.point((x, y), fill=color)
		y = y_st + y_off
		for x in range(x_st - 2,x_st + 2):
			draw.point((x, y), fill=color)
			
	def bus_cross(x_st, y_st, x_off, y_off, order, color=green):
		'''
		note:
		parameter order must be one of 
		[0, 1] --forward
		or [-1, 0] --backward
		'''
		for x in order:
			if x == 0:
				for y in range(y_st + int(y_off * 0.4), y_st + int(y_off * 0.8)):
					draw.point((x_st + x, y), fill=color)
			else:
				for y in range(y_st + int(y_off * 0.2), y_st + int(y_off * 0.4)):
					draw.point((x_st + x, y), fill=color)
				for y in range(y_st + int(y_off * 0.8), y_st + int(y_off * 1.0)):
					draw.point((x_st + x, y), fill=color)	

	def draw_time(x_st, y_st, x_off, y_off, time, scale):
		for x in range(x_st,x_st + x_off):
			if x == x_st:
				for y in range(y_st + int(y_off * 0.6), y_st + y_off):
					draw.point((x, y), fill=tint_write)
			elif x == x_st + x_off / 2:
				for y in range(y_st + int(y_off * 0.85),y_st + y_off):
					draw.point((x, y), fill=tint_write)
			else:
				draw.point((x,y_st + y_off - 1), fill=tint_write)
		draw.text((x_st,y_st), text='%d' % time + scale, font=font, fill=tint_write)

	def draw_name(x_st, y_st, x_off, y_off, name):
		draw.text((x_st + x_off / 4,y_st + y_off / 10), text=name, font=font, fill=tint_write)
	for i in range(len(waveout[0]['state'])):
		draw_time((i + 2) * unit_width,0, unit_width, unit_height, i * unittimeint,timescale_scale)
	for i in range(len(waveout) + 1):
		if i == 0:
			draw_name(0,i * unit_height, unit_width, unit_height,"name")
		else:
			draw_name(0,i * unit_height, unit_width, unit_height, waveout[i - 1]["name"])
		
	def get_bus_color(wave):
		if 'x' in wave:
			return red
		elif 'z' in wave:
			return blue
		else:
			return green

	for i in range(len(waveout)):
		for j in range(len(waveout[i]['state'])-1):
			if waveout[i]['state'][j] == State.I_X_X:
				to_x((j + 2) * unit_width, (i + 1) * unit_height,unit_width,unit_height, 'x')
			elif waveout[i]['state'][j] == State.I_Z_X:
				to_x((j + 2) * unit_width, (i + 1) * unit_height,unit_width,unit_height, 'z')
			elif waveout[i]['state'][j] == State.I_0_X:
				to_x((j + 2) * unit_width, (i + 1) * unit_height,unit_width,unit_height, '0')
			elif waveout[i]['state'][j] == State.I_1_X:
				to_x((j + 2) * unit_width, (i + 1) * unit_height,unit_width,unit_height, '1')
			elif waveout[i]['state'][j] == State.I_X_Z:
				to_z((j + 2) * unit_width, (i + 1) * unit_height,unit_width,unit_height, 'x')
			elif waveout[i]['state'][j] == State.I_Z_Z:
				to_z((j + 2) * unit_width, (i + 1) * unit_height,unit_width,unit_height, 'z')
			elif waveout[i]['state'][j] == State.I_0_Z:
				to_z((j + 2) * unit_width, (i + 1) * unit_height,unit_width,unit_height, '0')
			elif waveout[i]['state'][j] == State.I_1_Z:
				to_z((j + 2) * unit_width, (i + 1) * unit_height,unit_width,unit_height, '1')
			elif waveout[i]['state'][j] == State.I_X_0:
				to_zero((j + 2) * unit_width, (i + 1) * unit_height,unit_width,unit_height, 'x')
			elif waveout[i]['state'][j] == State.I_Z_0:
				to_zero((j + 2) * unit_width, (i + 1) * unit_height,unit_width,unit_height, 'z')
			elif waveout[i]['state'][j] == State.I_0_0:
				to_zero((j + 2) * unit_width, (i + 1) * unit_height,unit_width,unit_height, '0')
			elif waveout[i]['state'][j] == State.I_1_0:
				to_zero((j + 2) * unit_width, (i + 1) * unit_height,unit_width,unit_height, '1')
			elif waveout[i]['state'][j] == State.I_X_1:
				to_one((j + 2) * unit_width, (i + 1) * unit_height,unit_width,unit_height, 'x')
			elif waveout[i]['state'][j] == State.I_Z_1:
				to_one((j + 2) * unit_width, (i + 1) * unit_height,unit_width,unit_height, 'z')
			elif waveout[i]['state'][j] == State.I_0_1:
				to_one((j + 2) * unit_width, (i + 1) * unit_height,unit_width,unit_height, '0')
			elif waveout[i]['state'][j] == State.I_1_1:
				to_one((j + 2) * unit_width, (i + 1) * unit_height,unit_width,unit_height, '1')
			elif waveout[i]['state'][j] == State.I_BUS_KEEP:
				color = get_bus_color(waveout[i]['wave'][j])
				bus_body((j + 2) * unit_width, (i + 1) * unit_height,unit_width,unit_height, color)
				bus_continous((j + 2) * unit_width, (i + 1) * unit_height,unit_width,unit_height, color)
			elif waveout[i]['state'][j] == State.I_BUS_TRAN:
				color = get_bus_color(waveout[i]['wave'][j - 1])
				bus_cross((j + 2) * unit_width - 1, (i + 1) * unit_height,unit_width,unit_height,[-1,0], color)
				color = get_bus_color(waveout[i]['wave'][j])
				bus_cross((j + 2) * unit_width, (i + 1) * unit_height,unit_width,unit_height,[0,1], color)
				draw_name((j + 2) * unit_width-7, (i + 1) * unit_height+int(unit_height * 0.2), unit_width, unit_height,waveout[i]['wave'][j])
				bus_body((j + 2) * unit_width, (i + 1) * unit_height,unit_width,unit_height, color)
			elif waveout[i]['state'][j] == State.I_BUS_INIT:
				color = get_bus_color(waveout[i]['wave'][j])
				bus_body((j + 2) * unit_width, (i + 1) * unit_height,unit_width,unit_height, color)
				bus_cross((j + 2) * unit_width, (i + 1) * unit_height,unit_width,unit_height,[0,1], color)
				draw_name((j + 2) * unit_width-7, (i + 1) * unit_height+int(unit_height * 0.2), unit_width, unit_height,waveout[i]['wave'][j])
			else:
				pass#raise ValueError(1)

	image.show()
	image.save(pic_location, 'jpeg')
	''''''

if __name__ == '__main__':
	args=sys.argv[1:]
	directory = os.getcwd()
	vcd = os.path.join(directory, args[0])
	pic = os.path.join(directory, args[1])
	vcd2pic(vcd,pic)
