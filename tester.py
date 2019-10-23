import sys
import re
from pathlib import Path
import unicodedata
import subprocess
import shutil
from pegpy.main import *


# sub functions for test()
def txt2array(path):
    s = ''
    with open(path, mode='r', encoding='utf_8') as f:
        s = f.read()
    s = re.sub(r'[ ]', '', s)  # スペースの除去は入力文字列にあわせて適宜行う方がよいかも
    # s = re.sub(r'[。]', '。\n', s)
    return list(filter(lambda x: not x == '', s.split('\n')))[1:]


def write_result(fpath, results):
    with open(fpath, mode='w', encoding='utf_8') as f:
        s = ''
        for bl, cnt, ipt, res in results:
            sf = 'OK' if bl else 'NG'
            s += f'{cnt},{sf}: {ipt}\n'
            s += f'{res}\n\n'
        f.write(s[:-2])


def print_err(lst):
    fails = list(filter(lambda l: not l[0], lst))
    if len(fails) > 0:
        for _, cnt, s, remain in fails:
            print(f'入力: {s}')
            print(f'残り: {remain}')


# sub functions for test_with_graph()
def parse_ast(ast_str):
    class AST():
        def __init__(self, s, p):
            self.s = s
            self.pos = p

    class Tree():
        def __init__(self, tag_str, node_id, nodes_list, label_str):
            self.name = tag_str
            self.nid = node_id
            self.node = nodes_list
            self.label = label_str

    class Leaf():
        def __init__(self, inner_str, leaf_id):
            self.name = inner_str
            self.nid = leaf_id

    def get_tree(ast, nid, label):
        require(ast, '[')
        tag = get_tag(ast)
        ast.pos += 1
        node = get_node(ast, f'{nid}')
        require(ast, ']')
        return Tree(tag, nid, node, label)

    def get_node(ast, nid):
        node = []
        if ast.s[ast.pos:].startswith('\''):
            return [get_leaf(ast, f'{nid}_0')]
        label = get_label(ast)
        if ast.s[ast.pos:].startswith('['):
            while ast.s[ast.pos] != ']':
                inner = get_tree(ast, f'{nid}_{len(node)}', label)
                node.append(inner)
                if ast.s[ast.pos] == ' ':
                    ast.pos += 1
                    label = get_label(ast)
            return node
        else:
            print(f'pos:{ast.pos} don\'t start with "\'" or "["')
            sys.exit()

    def get_leaf(ast, nid):
        require(ast, '\'')
        name = ''
        while not ast.s[ast.pos:].startswith('\']'):
            name += escape(ast.s[ast.pos])
            ast.pos += 1
        require(ast, '\'')
        return Leaf(name, nid)

    def get_tag(ast):
        tag = ''
        while ast.s[ast.pos] != ' ':
            tag += ast.s[ast.pos]
            ast.pos += 1
        return tag

    def get_label(ast):
        label = 'None'
        label_match = re.match('[a-zA-Z0-9_]+=\[#', ast.s[ast.pos:])
        if label_match:
            label = label_match.group()[:-3]
            ast.pos += len(label) + 1
        return label

    def escape(s):
        after = ''
        META_LITERAL = ['\\', '"']
        for c in s:
            if c in META_LITERAL:
                after += f'\\{c}'
            else:
                after += c
        return after

    def require(ast, target):
        if ast.s[ast.pos:].startswith(target):
            ast.pos += len(target)
        else:
            print(f'pos:{ast.pos} don\'t match with {target}')
            sys.exit()

    def make_dict(tree, d):
        if isinstance(tree, Tree):
            for n in tree.node:
                label = n.label if isinstance(n, Tree) else ''
                d[str(n.nid)] = {'tag': n.name,
                                 'parent': tree.nid, 'label': label}
                make_dict(n, d)

    ast = AST(ast_str, 0)
    tree = get_tree(ast, 0, 'top')
    d = {}
    d[str(tree.nid)] = {'tag': tree.name, 'parent': '', 'label': tree.label}
    make_dict(tree, d)
    return d


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
        '        fontname = "MS Gothic",\n'
        '        fontcolor = "#252525",\n'
        '        fontsize = 12,\n'
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


def gen_dot(input_str, d):
    def_node = ''
    def_edge = ''
    for k, v in d.items():
        bt = ''
        for c in v["tag"]:
            if unicodedata.east_asian_width(c) in ['W', 'F', 'H']:
                bt = ', labelloc = "bottom"'
                break
        label = '' if v["label"] == 'None' else f' [label = "{v["label"]}"]'
        def_node += f'    n_{k} [label = "{v["tag"]}"{bt}];\n'
        def_edge += '' if v["parent"] == '' else f'    n_{v["parent"]} -> n_{k}{label};\n'
    return template(input_str, def_node, def_edge)


def make_dir(dn):
    try:
        Path(dn).mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        print(f'"{dn}": This directory already exist, can I overwrite it?')
        choice = input('(y/n): ')
        if choice in 'yY':
            shutil.rmtree(dn)
            make_dir(dn)
        else:
            sys.exit()


def escape(s):
        after = ''
        META_LITERAL = ['\\', '"']
        for c in s:
            if c in META_LITERAL:
                after += f'\\{c}'
            else:
                after += c
        return after


def gen_graph(input_str, ast_str, path='graph.png'):
    GEN_DOT_PATH = '.temp.dot'
    if not shutil.which('dot'):
        print('Not find "dot" command')
        print('Please install "Graphviz"')
        sys.exit()
    with open(GEN_DOT_PATH, mode='w', encoding='utf_8') as f:
        f.write(gen_dot(input_str, parse_ast(ast_str)))
    cmd = ['dot', '-Tpng', GEN_DOT_PATH, '-o', path]
    res = subprocess.call(cmd)
    Path(GEN_DOT_PATH).unlink()


def leaf2token(word, nodes):
    NON_UTILIZE = {
        'Noun': '名詞',
        'Block': '名詞',
        'Adnominal': '連体詞',
        'Adverb': '副詞',
        'Conjunction': '接続詞',
        'Interjection': '感動詞',
    }
    if   nodes[-1].startswith('ADJV'):
        return f'{word} (形容動詞)'
    elif nodes[-1].startswith('ADJ'):
        return f'{word} (形容詞)'
    elif nodes[-1].startswith('P_'):
        return f'{word} (助詞)'
    elif nodes[-1].startswith('AUX'):
        return f'{word} (助動詞)'
    elif nodes[-1].startswith('V'):
        return f'{word} (動詞)'
    else:
        return f'{word} ({NON_UTILIZE[nodes[-1]]})'


def gen_compare(ast):
    def make_words(tree, words, nodes):
        if len(tree.subs()) == 0:
            leaf = str(tree)
            current = [tree.tag] if tree.tag != '' else []
            words.append(leaf2token(leaf, nodes+current))
        else:
            for i, (_, child) in enumerate(tree.subs()):
                current = [tree.tag] if tree.tag != '' else []
                make_words(child, words, nodes+current)

    words = []
    make_words(ast, words, [])
    words.append('。 (文末)')
    return words


# main tester functions
def test(target_name, grammar='kaguya0.tpeg', print_log='True', _='y or n'):
    options = parse_options(['-g', grammar])
    peg = load_grammar(options)
    parser = generator(options)(peg, **options)
    results = []
    compare_words = []
    fail_cnt = 0

    input_list = txt2array(target_name)
    FILE_NAME = target_name[(target_name.rfind('/')) +
                            1: (target_name.rfind('.'))]
    Path('test/result').mkdir(parents=True, exist_ok=True)

    for count, s in enumerate(input_list):
        sys.stdout.write(f'\rNow Processing: {count+1}/{len(input_list)}')
        try:
            tree = parser(s)
        except Exception as e:
            print(e)
        if tree.tag == 'err':
            results.append((False, count+1, s, tree.inputs[tree.epos:]))
            fail_cnt += 1
        else:
            results.append((True, count+1, s, repr(tree)))
            compare_words += gen_compare(tree)
        sys.stdout.flush()
    print()
    write_result(f'test/result/{FILE_NAME}.txt', results)
    with open(f'test/result/{FILE_NAME}_for_compare.txt', mode='w', encoding='utf_8') as f:
        f.write('\n'.join(compare_words))
    if not print_log in ['0', 'false', 'False']:
        print_err(results)
    print('Fail Rate: %d / %d' % (fail_cnt, len(input_list)))
    return results


def test_with_graph(target_file, grammar_file, print_log='True', _='y or n'):
    if not shutil.which('dot'):
        print('Not find "dot" command')
        print('Please install "Graphviz"')
        sys.exit()
    FILE_NAME = target_file[target_file.rfind('/')+1: target_file.rfind('.')]
    results = test(target_file, grammar_file, print_log)
    MAX_COUNT = len(results)
    make_dir(f'graph_{FILE_NAME}')
    for count, (bl, ln, s, ast) in enumerate(results):
        sys.stdout.write(f'\rNow Processing: {count+1}/{MAX_COUNT}')
        if bl:
            gen_graph(escape(s), ast, f'graph_{FILE_NAME}/{count}.png')
        else:
            gen_graph(escape(s), f'[#Remain \'{escape(ast)}\']', f'graph_{FILE_NAME}/{count}.png')
        sys.stdout.flush()
    print()


if __name__ == "__main__":
    # example: python tester.py test/ethereum.txt gakkou.tpeg
    if len(sys.argv) >= 5:
        s = sys.argv[4]
    else:
        print('Do test with generating graph?')
        s = input('(y/n): ')
    if s == 'y':
        test_with_graph(*sys.argv[1:])
    elif s == 'n':
        test(*sys.argv[1:])
