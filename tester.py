import sys
import time
import re
import string
from pathlib import Path
import unicodedata
import subprocess
import shutil
from pegpy.main import *

sys.setrecursionlimit(2**31-1)

# sub functions for test()
def txt2array(path):
    s = ''
    with open(path, mode='r', encoding='utf_8') as f:
        s = f.read()
    s = re.sub(r'[ ]', '', s)  # スペースの除去は入力文字列にあわせて適宜行う方がよいかも
    # s = re.sub(r'[。]', '。\n', s)
    return list(filter(lambda x: not x == '', set(s.split('\n'))))[1:]


def write_result(fpath, results):
    with open(fpath, mode='w', encoding='utf_8') as f:
        s = ''
        print('Now Caching Result')
        for cnt, ast in results:
            OKorNG = 'NG' if ast.tag == 'err' else 'OK'
            s += f'{cnt},{OKorNG}\n'
            s += f'{ast.inputs}\n'
            if ast.tag == 'err':
                s += f'{ast.inputs[ast.epos:]}\n'
            else:
                s += f'{repr(ast)}\n'
        print('Now Writing Result')
        f.write(s)


def print_err(results):
    for cnt, ast in results:
        if ast.tag == 'err':
            print(f'入力: {ast.inputs}')
            print(f'残り: {ast.inputs[ast.epos:]}')


DOT = '''\
digraph sample {
    graph [
        charset = "UTF-8",
        label = "$input_text",
        labelloc = t,
        fontname = "MS Gothic",
        fontsize = 18,
        dpi = 300,
    ];

    edge [
        dir = none,
        fontname = "MS Gothic",
        fontcolor = "#252525",
        fontsize = 12,
    ];

    node [
        shape = box,
        style = "rounded,filled",
        color = "#3c3c3c",
        fillcolor = "#f5f5f5",
        fontname = "MS Gothic",
        fontsize = 16,
        fontcolor = "#252525",
    ];

    $node_description

    $edge_description
}'''


def escape(s):
        after = ''
        META_LITERAL = ['\\', '"']
        for c in s:
            if c in META_LITERAL:
                after += f'\\{c}'
            else:
                after += c
        return after


def bottom_check(s):
        for c in s:
            if unicodedata.east_asian_width(c) in ['W', 'F', 'H']:
                return ', labelloc = "bottom"'
        return ''


def make_dict(t, d, nid):
    d['node'].append(f'n{nid} [label="#{t.tag}"]')
    if len(t.subs()) == 0:
        leaf = str(t)
        d['node'].append(f'n{nid}_0 [label="{escape(leaf)}"{bottom_check(leaf)}]')
        d['edge'].append(f'n{nid} -> n{nid}_0')
    else:
        for i, (fst, snd) in enumerate(t.subs()):
            label = f' [label="{fst}"]' if fst != '' else ''
            d['edge'].append(f'n{nid} -> n{nid}_{i}{label}')
            make_dict(snd, d, f'{nid}_{i}')


def gen_dot(t):
    d = {'node': [], 'edge': []}
    if t.tag == 'err':
        leaf = escape(t.inputs[t.epos:])
        d['node'].append(f'n0 [label="#Remain"]')
        d['node'].append(f'n0_0 [label="{leaf}"{bottom_check(leaf)}]')
        d['edge'].append(f'n0 -> n0_0')
    else:
        make_dict(t, d, 0)
    context = {
        'input_text': escape(t.inputs),
        'node_description': ';\n    '.join(d['node']),
        'edge_description': ';\n    '.join(d['edge']),
    }
    return string.Template(DOT).substitute(context)


def gen_graph(ast, path='graph.png'):
    GEN_DOT_PATH = '.temp.dot'
    with open(GEN_DOT_PATH, mode='w', encoding='utf_8') as f:
        f.write(gen_dot(ast))
    cmd = ['dot', '-Tpng', GEN_DOT_PATH, '-o', path]
    res = subprocess.call(cmd)
    if res != 0:
        Path(GEN_DOT_PATH).rename(f'.erred.dot')
    else:
        Path(GEN_DOT_PATH).unlink()


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


def leaf2token(word, nodes):
    NON_UTILIZE = {
        'Noun': '名詞',
        'Block': '名詞',
        'Postp': '助詞',
        'Adnominal': '連体詞',
        'Adverb': '副詞',
        'Conjunction': '接続詞',
        'Interjection': '感動詞',
        'Sentence': 'TEN'
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


def gen_compare(ast, count):
    def make_words(tree, words, nodes):
        if len(tree.subs()) == 0:
            leaf = str(tree)
            current = [tree.tag] if tree.tag != '' else []
            words.append(leaf2token(leaf, nodes+current))
        else:
            for i, (_, child) in enumerate(tree.subs()):
                current = [tree.tag] if tree.tag != '' else []
                make_words(child, words, nodes+current)

    words = [f'No_{count}']
    make_words(ast, words, [])
    return words


def test(target, grammar):
    options = parse_options(['-g', str(grammar)])
    peg = load_grammar(options)
    parser = generator(options)(peg, **options)
    results = []
    # compare_words = []
    fail_cnt = 0

    input_list = txt2array(target)
    Path('test/result').mkdir(parents=True, exist_ok=True)

    START = time.time()
    for count, s in enumerate(input_list):
        sys.stdout.write(f'\rNow Processing: {count+1}/{len(input_list)}')
        try:
            tree = parser(s)
        except Exception as e:
            print(e)
        if tree.tag == 'err':
            fail_cnt += 1
        results.append((count+1, tree))
        # compare_words += gen_compare(tree, count)
        sys.stdout.flush()
    print()
    write_result(f'test/result/{target.stem}_{grammar.stem}.txt', results)
    # with open(f'test/result/{target.stem}_for_compare.txt', mode='w', encoding='utf_8') as f:
    #     f.write('\n'.join(compare_words))
    END = time.time() - START
    TOTAL = len(input_list)
    print(f'SUCCESS RATE  : {TOTAL-fail_cnt}/{TOTAL} => {100*(TOTAL-fail_cnt)/TOTAL}[%]')
    print(f'TEST EXECUTION TIME: {END}[sec]')
    return results


def main(args):
    def arg2dict(d, l):
        if len(l) < 1:return 0
        head = l.pop(0)
        if head in ['-t', '-g']:
            d[head] = Path(l.pop(0))
            arg2dict(d, l)
        elif head in ['-Graph', '-Log']:
            d[head] = True
            arg2dict(d, l)
        else:
            print(f'Invalid argument: {head}')
            sys.exit()
    
    options = {
        '-t': None,
        '-g': None,
        '-Graph': False,
        '-Log': False,
    }
    arg2dict(options, args)
    results = test(options['-t'], options['-g'])
    if options['-Log']:
        print_err(results)
    if options['-Graph']:
        if not shutil.which('dot'):
            print('Not find "dot" command')
            print('Please install "Graphviz"')
            sys.exit()
        else:
            MAX_COUNT = len(results)
            FILE_NAME = options['-t'].stem
            GRAMMAR_NAME = options['-g'].stem
            make_dir(f'graph_{FILE_NAME}_{GRAMMAR_NAME}')
            START = time.time()
            for count, (ln, ast) in enumerate(results):
                sys.stdout.write(f'\rNow Processing: {count+1}/{MAX_COUNT}')
                gen_graph(ast, f'graph_{FILE_NAME}_{GRAMMAR_NAME}/{count}.png')
                sys.stdout.flush()
            print()
            END = time.time() - START
            print(f'GEN_GRAPH EXECUTION TIME: {END}[sec]')


if __name__ == "__main__":
    # python tester.py -t test/javadoc.txt -g gk.tpeg -Graph -Log
    main(sys.argv[1:])
