#!/tools/bin/python3.6
import Classes
import RegisterFunctions
import os

def gen_specman_register(reg):
    output=[]

    output.append("\n")


def gen_specman_file(reg_list, regs_prefix):
    spec_regs_file = open((os.getcwd() + "/" + regs_prefix + "_spec_regs.e"), "w")
    reg_defs_file  = open((os.getcwd() + "/" + regs_prefix + "_reg_defs.e"), "w")

    # reg_defs_file.write(cur_line + "\n")
    # spec_regs_file.write();

    for reg in reg_list:
        cur_line = regs_prefix + "_" + reg.name + "   " + hex(int(str(reg.addr)))
        reg_defs_file.write(cur_line + "\n")
        spec_regs_file.write(gen_specman_register(reg))

    reg_defs_file.close()
    spec_regs_file.close()