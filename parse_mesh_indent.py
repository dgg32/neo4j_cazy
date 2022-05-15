import sys

mesh_indent_file = sys.argv[1]

def tab_level(astr):
    """Count number of leading tabs in a string
    """
    return len(astr)- len(astr.lstrip(' '))



indent_space = 4
indent_text = {}

relation = "from,to\n"

nodes = ""

n = 0
for i, line in enumerate(open(mesh_indent_file, 'r')):
    if line.strip() != "":
        indent = tab_level(line)
        indent_text[indent] = line.strip()
        nodes += f"{line.strip()}\n"

        if n == 1:
            indent_space = indent
        #print (indent, line)
        if indent != 0:
            relation += f'"{line.strip()}","{indent_text[indent-indent_space]}"' + "\n"
        n += 1

with open("mesh_indent_relation.csv", 'w') as f:
    f.write(relation)

with open("mesh_indent_node.csv", 'w') as f:
    f.write(nodes)