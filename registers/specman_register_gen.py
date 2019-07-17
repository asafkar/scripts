#!/tools/bin/python3.6
import sys
import os
import RegisterFunctions
import settings
from prettytable import PrettyTable

# get arguments from user
curr_tag = None
file_name = None
try:
    print("Specman Register Generator - Running, Be Patient...")
    file_name = sys.argv[1]
    curr_tag = sys.argv[2]
except:
    if file_name is None:
        help()
        sys.exit("\n Error- Please specify an excel file")

# initialize setting class
regs_prefix = file_name.split("/")[-1].split(".")[0]
excel_filename = file_name.split("/")[-1]
settings.init(excel_filename, regs_prefix, curr_tag)

# Read Main Excel file to workbook object
wb = RegisterFunctions.file_to_wb(file_name)

# Parse excel from user, return list of registers
registers_list = RegisterFunctions.parse_wb(wb)

''' Code for outputting results: '''
# Human readable file = desc_file
# File to be parsed by Specman = spec_file

desc_file = open((os.getcwd() + "/" + settings.regs_prefix + "_descriptions.txt"), "w")
spec_file = open((os.getcwd() + "/" + settings.regs_prefix + "_specman_reg_info.txt"), "w")
spec_reg_list_file = open((os.getcwd() + "/" + settings.regs_prefix + "_spec_reg_list.e"), "w")

spec_reg_list_file.write("<' \nstruct reg_name_s {\n  addr:  uint;\n  name:  string;  }; \n")
spec_reg_list_file.write("extend sys {\n !reg_names_l: list(key: name) of reg_name_s; \n")
spec_reg_list_file.write("  post_generate() is also {\n")
spec_reg_list_file.write("      var temp_reg_name : reg_name_s;\n")

# go over all registers in reg_list, writing each one to both files
for reg in registers_list:
    spec_reg_list_file.write(
        "      gen temp_reg_name keeping {it.addr ==" + hex(int(reg.addr)) + " ; it.name == \"" + str(
            reg.name) + "\" };\n")
    spec_reg_list_file.write("      reg_names_l.add(temp_reg_name);\n")
    spec_file_line = "register " + str(reg.name) + " " + hex(int(reg.addr)) + " " + str(reg.RW) + " "

    desc_file.write("Register: " + reg.name + "\n")
    desc_file.write("address : " + hex(int(reg.addr)) + "\n")
    desc_file.write("Fields: \n")

    t = PrettyTable(['Name', 'bits', 'reset_val', 'Comments'])  # table object for printing

    # when writing to spec_file, add "reserved" bits for fields which aren't defined
    last_field_bit = 0
    rsvd_idx = 0

    for field in reg.fields:
        # code for finding gaps in field bits:
        high_num = int(field.bits.strip("[]").split(":")[0])
        low_num = int(field.bits.strip("[]").split(":")[1])
        dist = low_num - last_field_bit
        if dist > 0:
            spec_file_line += "rsvd" + str(rsvd_idx) + " " + str(low_num - 1) + " " + str(last_field_bit) + " 0 "
            rsvd_idx += 1
        spec_file_line += str(field.name) + " " + str(high_num) + " " + str(low_num) + " " + str(field.reset_val) + " "
        last_field_bit = high_num + 1

        t.add_row([field.name, str(field.bits), field.reset_val, field.comment])
        # desc_file.write("\t name " + field.name + " bits " + str(field.bits) + "\n" )
    desc_file.write(t.get_string())
    desc_file.write(" \n\n\n")

    spec_file.write(spec_file_line + "\n")

spec_reg_list_file.write("\n };\n }; \n'>")

desc_file.close()
spec_file.close()
spec_reg_list_file.close()


