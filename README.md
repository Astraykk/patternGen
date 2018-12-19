Generate test pattern on BR0101!

Usage：

from patternGen import PatternGen

pattern = PatternGen('/path/to/project', 'tfo_name.tfo', '-command')
# -legacy: txt format

pattern.write()  # write ptn

pattern.trf2vcd('trf_file.trf', 'vcd_file.vcd')  # transform to vcd


/************************** Development log ********************************/

12/19/2018

Add sorted symbol-to-signal list for trf2vcd().
  - Now the output vcd file is ordered like the original file.
Add compare_trf() to compare trf with ptn, and generate reports.
  - In progress.

Repair the problem that bus signal cannot be identified in vcd_parser().