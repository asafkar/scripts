
import verilog_BNF
import pprint
import settings
import re
from anytree import Node, RenderTree
import multiprocessing as mp
import traceback


verilog_BNF.Verilog_BNF()
pp = pprint.PrettyPrinter(indent=2)


class VerilogModule(Node):
    def __init__(self, name, inst_type, parent=None, children=None, **kwargs):
        self.__dict__.update(kwargs)
        self.name = name
        self.parent = parent
        self.inst_type = inst_type
        if children:
            self.children = children

# This function will run on each file lines before being fed to the actual parser.
# It will take the compiler directives into consideration and replace them in the text
# If the function finds new defines, it will add them
# TODO currently the function doesn't handle nested ifdefs, will have to be run a few times, one for each nesting
def pre_process_text(txt_lines, defines):
    returned_txt_lines = []
    lines_iter = iter(txt_lines)
    if_else_queue = []
    changed_content = False
    depth_if = 1  # level of nested if
    delete = False
    skip_block = False
    for line in lines_iter:
        temp_line = line.strip()
        if temp_line.startswith("//"):  # skip comments
            continue

        # code for handling test-bench code which doesn't really compile
        if re.match("reg.*=", temp_line):  # skip register assignment (non synthesable)
            continue
        if "@(*)" in temp_line:
            line = line.replace("@(*)", "@(a)")
            temp_line = line.strip()

        if "@*" in temp_line:
            line = line.replace("@*", "@(a)")
            temp_line = line.strip()

        # code which replaces macros in line with blanks, which won't make parse errors
        if "`" in temp_line:
            if not "`define" in temp_line and not "`if" in temp_line and not "`else" \
                    in temp_line and not "`end" in temp_line:
                continue

        if "`define" in temp_line:
            # defines.append(temp_line.split("`define ")[1].split(" ")[1])
            defines.append(re.split("[\s$]", re.split("`define[\s]+", temp_line)[1])[0])
        elif "`ifdef" in temp_line or "`ifndef" in temp_line:
            changed_content = True
            skip_block = True
            if "`ifdef" in temp_line:
                if_ = True
                curr_if = temp_line.split("`ifdef ")[1]
            else:
                if_ = False
                curr_if = temp_line.split("`ifndef ")[1]
            if (curr_if in defines and if_) or (curr_if not in defines and not if_):
                if_else_queue.append(curr_if)
                delete = False
            else:  # if this ifdef isn't in the defines, skip this block until `endif \ `else
                depth_if = 1
                delete = True

            if skip_block:
                done_iter = False
                while not done_iter:
                    try:
                        line = next(lines_iter)
                    except StopIteration:  # if reached end of file
                        done_iter = True
                    temp_line = line.strip()
                    if temp_line.startswith("//"):
                        continue
                    # code which replaces macros in line with blanks, which won't make parse errors
                    if "`" in temp_line:
                        if "`define" not in temp_line and "`if" not in temp_line and "`else" \
                                not in temp_line and "`end" not in temp_line:
                            continue
                    if not delete:
                        returned_txt_lines.append(line)
                    if "`ifdef" in temp_line or "`ifndef" in temp_line:
                        depth_if += 1
                    if "`endif" in temp_line or "`else" in temp_line:
                        if depth_if == 1 and "`endif" in temp_line:
                            if not delete:  # if added this line already, delete it
                                _ = returned_txt_lines.pop()
                            break
                        elif depth_if == 1 and "`else" in temp_line:
                            if not delete:  # if added this line already, delete it
                                _ = returned_txt_lines.pop()
                            delete = not delete
                        elif "`endif" in temp_line:
                            depth_if -= 1
                skip_block = False
        else:
            returned_txt_lines.append(line)

    return returned_txt_lines, changed_content


def get_modules_from_file(file_name):

    # read all lines in file as bytes, decode them to remove errors, save as list
    infile = open(file_name, 'rb')
    print("Parsing file " + file_name)
    file_lines_decoded = []
    for line in infile:
        file_lines_decoded.append(line.decode(errors='ignore'))


    filelines, pre_process_ongoing = pre_process_text(file_lines_decoded, settings.defines_list)
    infile.close()

    # if there are still compiler directives, keeping 'peeling them off' recursively
    while pre_process_ongoing:  # keep on preprocessing until done handling all `macros
        filelines, pre_process_ongoing = pre_process_text(filelines, settings.defines_list)

    teststr = "".join(filelines)
    tokens = None
    try:
        tokens = verilog_BNF.parse_data(teststr)
    except:
        print("issues during parsing ", file_name)

    wr_str = pp.pformat(tokens)

    module_header_type = ""
    for ii, module_headers in enumerate(wr_str.split("__module_header\': [\'")):
        if ii == 0:
            continue
        module_header_type = module_headers.split("'")[0]

    main_model = VerilogModule("", module_header_type )
    module_names = []
    module_types = []

    # ## fixme find a more efficient way to do this:
    # print("module names:")
    for ii, modules in enumerate(wr_str.split("__module_name\': [\'")):
        if ii == 0:
            continue
        # print(modules.split("'")[0])
        module_names.append(modules.split("'")[0])

    # print("module types:")
    for ii, modules in enumerate(wr_str.split("__module_type\': [\'")):
        if ii == 0:
            continue
        # print(modules.split("'")[0])
        module_types.append(modules.split("'")[0])
        temp_model = VerilogModule(module_names[ii-1], module_types[ii-1], main_model)
    return main_model


# function for opening a single file and parsing it into a module and submodules
def create_single_module_tree_from_file(verilog_file):
    try:
        curr_model_l = get_modules_from_file(verilog_file)
    except Exception as e:
        print("Caught exception in thread with (filename = %s) " % verilog_file)
        traceback.print_exc()
        print()
        raise e
    return curr_model_l


# this function will scan the given list, and create a list of module and its submodules
def create_module_file_name_pairs(list_fname):
    global_defines = []
    # this is a list of modules and their submodules
    module_hierarchy_l = []

    infile = open(list_fname)
    filelines = infile.readlines()
    infile.close()
    verilog_files = []

    # run over whole list. If verilog file, add to verilog_files list.
    # If list file, open, add all items to filelines
    while filelines:
        temp_line = filelines.pop(0).strip()
        if temp_line.startswith("//") or temp_line.startswith("+"):
            continue
        if not settings.parse_vfiles and temp_line.endswith("vfiles"):
            continue
        if "fast_func" in temp_line or temp_line.endswith(".sv"):  # fixme!
            continue
        if temp_line.startswith("-f"):
            temp_file = open(temp_line.split("-f ")[1])
            temp_lines = temp_file.readlines()
            filelines += temp_lines
            temp_file.close()
        elif temp_line.startswith("-v"):
            temp_file = temp_line.split("-v ")[1]
            verilog_files.append(temp_file)
        elif temp_line.endswith(".v"):
            verilog_files.append(temp_line)

    # spawn this into parallel cpu's # todo try parallel threads, not cpu
    pool = mp.Pool(mp.cpu_count())
    print("processing with " + str(mp.cpu_count()) + " different threads")
    module_hierarchy_l = [pool.apply(create_single_module_tree_from_file, args=(verilog_file, )) for verilog_file in verilog_files]
    # for verilog_file in verilog_files:
    #     curr_model_l = get_modules_from_file(verilog_file)
    #     module_hierarchy_l.append(curr_model_l)
    pool.close()
    return module_hierarchy_l








