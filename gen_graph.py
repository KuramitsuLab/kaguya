from pprint import pprint
import sys
import re
from pathlib import Path
import unicodedata
import textwrap
import subprocess
import shutil


GEN_DOT_PATH = './.generated_dot.dot'



class AST():
    def __init__(self, s, p):
        self.s = s
        self.pos = p


class Tree():
    def __init__(self, n, nid, node):
        self.name = n;
        self.nid = nid;
        self.node = node;


class Leaf():
    def __init__(self, n, nid):
        self.name = n
        self.nid = nid


# AST string -> dict
def parse(tree_str):
    def make_dict(tree, d):
        if isinstance(tree, Tree):
            for n in tree.node:
                d[str(n.nid)] = { 'label': n.name, 'parent': tree.nid }
                make_dict(n, d)

    try:
        ast = AST(tree_str, 0)
        tree = getNode(ast, 0)
        d = {}
        d[str(tree.nid)] = {'label': tree.name, 'parent': ''}
        make_dict(tree, d)
        return d
    except Exception as e:
        print(e)
        return {'ERROR': {'label': 'ERROR', 'parent': ''}}



def getNode(ast, nid):
    try:
        require(ast, '[')
        tag = getTag(ast)
        skip_space(ast)
        node = getInner(ast, f'{nid}')
        skip_space(ast)
        require(ast, ']')
        return Tree(tag, nid, node)
        # if tag == '#LookAHead' and len(node) >= 2:
        #     return Tree(tag, nid, node[:-1])
        # else:
        #     return Tree(tag, nid, node)
    except Exception as e:
        raise e


def getInner(ast, nid):
    try:
        if ast.s[ast.pos:].startswith('\''):
            return [getLeaf(ast, f'{nid}_0')]
        elif ast.s[ast.pos:].startswith('['):
            count = 0;
            node = [];
            while ast.s[ast.pos] != ']':
                inner = getNode(ast, f'{nid}_{count}')
                node.append(inner)
                count += 1
                skip_space(ast)
            return node
        else:
            raise Exception(f'<PARSE ERROR> {ast.s[ast.pos]} don\'t start with "\'" or "["')
    except Exception as e:
        raise e


def getLeaf(ast, nid):
    try:
        require(ast, '\'')
        lname = ''
        while not ast.s[ast.pos:].startswith('\']'):
            lname += escape(ast.s[ast.pos]);
            ast.pos += 1;
        require(ast, '\'')
        return Leaf(lname, nid)
    except Exception as e:
        raise e


def escape(s):
    after = ''
    for c in s:
        if c in ['\\', '"']:
            after += f'\\{c}'
        else:
            after += c
    return after


def getTag(ast):
    tag = ''
    while re.compile(r'[\w#]').match(ast.s[ast.pos]):
        tag += ast.s[ast.pos];
        ast.pos += 1;
    return tag


def skip_space(ast):
    while re.compile(r'[ \n\t]').match(ast.s[ast.pos]):
        ast.pos += 1;


def require(ast, target):
    if ast.s[ast.pos:].startswith(target):
        ast.pos += len(target)
    else:
        raise Exception(f'<PARSE ERROR> pos:{ast.pos} don\'t match with {target}')


# tree data -> dot text
def template(s, node, edge):
    return (
        'digraph sample {\n'
        '    graph [\n'
        '        charset = "UTF-8",\n'
        '        label = "%s",\n'
        '        labelloc = t,\n'
        '        fontsize = 18,\n'
        '        dpi = 300,\n'
        '    ];\n\n'
        '    edge [\n'
        '        dir = none,\n'
        '    ];\n\n'
        '    node [\n'
        '        shape = box,\n'
        '        style = "rounded,filled",\n'
        '        color = "#3c3c3c",\n'
        '        fillcolor = "#f5f5f5",\n'
        '        fontname = "MS Gothic",\n'
        '        fontsize = 16,\n'
        '        fontcolor = "#252525",\n'
        '    ];\n\n'
        '%s\n'
        '%s'
        '}' % (s, node, edge))

# dict -> dot file
def gen_dot(base_str, d):
    def_node = ''
    def_edge = ''
    for k, v in d.items():
        parent = v['parent']
        label = v['label']
        bt = 'labelloc = "bottom", ' if 1 in [1 if unicodedata.east_asian_width(c) in ['W', 'F', 'H'] else 0 for c in label] else ''
        def_node += f'    n_{k} [{bt}label = "{label}"];\n'
        def_edge += '' if parent == '' else f'    n_{parent} -> n_{k};\n'
    with open(GEN_DOT_PATH, mode='w', encoding='utf_8') as f:
        f.write(template(base_str, def_node, def_edge))
    return False if 'ERROR' in d.keys() else True


# (base text, AST) -> dict -> dot file -> png
def gen_png(tpl, png_folder, png_name):
    err = gen_dot(tpl[0], parse(tpl[1]))
    Path(f'graph/{png_folder}').mkdir(parents=True, exist_ok=True)
    cmd = ['dot', '-Tpng', GEN_DOT_PATH, '-o', f'graph/{png_folder}/{png_name}.png']
    res = subprocess.call(cmd)
    if res != 0 or not err:
        Path(GEN_DOT_PATH).rename(f'.err_{png_name}.dot')


# success file -> (base text, AST) list -> all png
def main(path):
    if not shutil.which('dot'):
        print('Please install graphviz')
        print('for Mac: brew install graphviz')
        sys.exit()
    fname = path[path.rfind('/')+1 : path.rfind('.')]
    with open(path, mode='r', encoding='utf_8') as f:
        blocks = f.read().split('\n\n')
        MAX_COUNT = len(blocks)
        for count, pair in enumerate(blocks):
            sys.stdout.write(f'\rNow Processing: {count+1}/{MAX_COUNT}')
            (bt, ast, *_) = pair.split('\n')
            gen_png((escape(bt), ast), fname, str(count))
            sys.stdout.flush()
    print()
    Path(GEN_DOT_PATH).unlink()


if __name__ == "__main__":
    if len(sys.argv[1]) >= 2:
        main(sys.argv[1])
    else:
        print('Not Enough Parameter')
