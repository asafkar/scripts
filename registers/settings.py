#!/tools/bin/python3.6


def init(local_excel_fn, prefix, curr_tag_used=None):
    global tags_dir
    global tag_used
    global local_excel_filename
    global tag_dict
    global revisions_dir
    global regs_prefix


    regs_prefix = prefix
    local_excel_filename = local_excel_fn

    revisions_dir = "/project/ayalon/projects/ayalon/blocks/REVISIONS/"
    tags_dir = "/project/ayalon/projects/ayalon/blocks/block_config/"
    tag_used = curr_tag_used   #which tag is being used, else None
    tag_dict = {}  # pair of block name and block revision (i.e. vl_clock / vl_clock_8Oct2018175138)

    #parse tag file,
    if tag_used is not None:
        tag_file_handler = open(tags_dir + tag_used + ".tag", "r")  # open the cfg file of the file
        tag_file_l = [line for line in tag_file_handler.read().split('\n')]  # read the tag file
        for line in tag_file_l:
            if "REVISION" not in line:
                continue
            curr_block_name = line.split("BLOCK=")[1].split(" REVISION=")[0]
            curr_block_rev = line.split(" REVISION=")[1]
            tag_dict[curr_block_name]=curr_block_rev  #add to dict

