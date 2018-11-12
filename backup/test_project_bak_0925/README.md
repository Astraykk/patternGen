Generate test pattern on BR0101!

使用方法：

from patternGen import PatternGen

pattern = PatternGen('/path/to/project', 'tfo_name.tfo', '-command')  # -legacy: txt格式

pattern.write()  # 写入ptn文件

pattern.trf2vcd('trf_file.trf', 'vcd_file.vcd')  # 转换成vcd格式
