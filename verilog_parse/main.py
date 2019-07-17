from anytree import Node, RenderTree

import time
import pprint

__version__ = "1.0.11"


import parse_functions
import collections
import settings
from anytree.exporter import DotExporter

settings.init(False)


top_most_module = "H_Link"
list_file = "H_Link.list"  # list of all include modules

module_hierarchy_l = parse_functions.create_module_file_name_pairs(list_file)

for mod in module_hierarchy_l:
    if mod.inst_type == top_most_module:
        root = mod
        block_queue = collections.deque([x for x in root.children])
        break

while block_queue:
    curr_block = block_queue.popleft()
    for mod in module_hierarchy_l:
        if mod.inst_type == curr_block.inst_type:
            temp_name = curr_block.name
            mod.parent = curr_block.parent
            curr_block.parent = None
            del curr_block
            mod.name = temp_name
            for gr_child in mod.children:
                block_queue.append(gr_child)
            break

DotExporter(root).to_picture("root.png")
DotExporter(root).to_dotfile("dot_file.dot")



