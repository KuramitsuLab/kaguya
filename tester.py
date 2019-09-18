import sys
import time
from pathlib import Path
import datetime
import re
from pegpy.main import *
import itertools


def txt2array(path):
    s = ''
    with open(path, mode='r', encoding='utf_8') as f:
        s = f.read()
    s = re.sub(r'[ ]', '', s)
    # s = re.sub(r'[。]', '。\n', s)
    return list(filter(lambda x: not x == '', s.split('\n')))[1:]


def logging(fn, aopl, pt, fr):
    s = ''
    date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open('test/result/LOG.md', mode='a', encoding='utf_8') as f:
        s += f'+ Date: {date}\n'
        s += f'+ Target File Name: `{fn}`\n'
        s += f'+ Amount of Parse Lines: {aopl}\n'
        s += f'+ Parse Required Time: {round(pt, 5)} sec\n'
        s += f'+ Fail Rate: {fr[0]}/{fr[1]}\n'
        s += '---\n\n'
        f.write(s)


def write_result(fpath, results, count=0):
    with open(fpath, mode='w', encoding='utf_8') as f:
        s = ''
        for text, tree in results:
            s += text + '\n'
            s += tree + '\n'
            s += '\n'
        f.write(s[:-1])


def print_err(lst):
    if len(lst) > 0:
        with open('err_cases.txt', mode='w', encoding='utf_8') as f:
            for fst, snd in lst:
                print('入力: ' + fst)
                print(snd + '\n')
                f.write(fst + '\n')



def test(target_name, grammar='kaguya0.tpeg', cmax=0):
    options = parse_options(['-g', grammar])
    peg = load_grammar(options)
    parser = generator(options)(peg, **options)
    results = {
        'success': [],
        'fail': [],
    }

    str_list = txt2array(target_name)
    FILE_NAME = target_name[(target_name.rfind('/'))+1 : (target_name.rfind('.'))]
    MAX_COUNT = cmax if cmax > 0 else len(str_list)
    Path('test/result/success').mkdir(parents=True, exist_ok=True)
    Path('test/result/fail').mkdir(parents=True, exist_ok=True)

    # START = time.time()
    for count,s in enumerate(str_list):
        if count >= MAX_COUNT:break
        sys.stdout.write(f'\rNow Processing: {count+1}/{MAX_COUNT}')
        if s.startswith('//'):
            sys.stdout.flush()
            print(f'Skiped: {s}')
            continue
        tree = parser(s)
        if 'Syntax Error' in repr(tree):
            results['fail'].append((s, f'残り: [{str(tree)}]'))
        else:
            results['success'].append((s, repr(tree)))
        sys.stdout.flush()
    # STOP = time.time()

    print()
    FAIL_RATE = (len(results['fail']), MAX_COUNT)
    # PARSE_TIME = STOP-START
    write_result(f'test/result/success/{FILE_NAME}.txt', results['success'])
    write_result(f'test/result/fail/{FILE_NAME}.txt', results['fail'])
    # logging(target_name, MAX_COUNT, STOP-START, FAIL_RATE)
    # print_err(results['fail'])
    print(f'Fail Rate: {FAIL_RATE[0]}/{FAIL_RATE[1]}')


def gen_chunk(lst):
    s = 'Chunk =\n'
    for l in lst:
        s += f'    / {l}\n'
    return s


def chunk_test(target_name, grammar='kaguya0.tpeg', cmax=0):
    chunks = [
        'NounPhrase',
        'ConjunctionPhrase',
        'AdverbPhrase',
        'AdnominalPhrase',
        'VerbPhrase',
        'AdjectivePhrase',
        'AdjectiveVerbPhrase'
    ]
    all_pattern = list(itertools.permutations(chunks))
    base_grammar = ''
    with open(grammar, mode='r', encoding='utf_8') as f:
        base_grammar = f.read()
    for pattern in all_pattern:
        with open('temp_grammar.tpeg', mode='w', encoding='utf_8') as f:
            f.write(base_grammar.replace('REPLACE_HERE', gen_chunk(pattern)))
        print(f'pattern is {pattern}')
        test(target_name, 'temp_grammar.tpeg')
    Path('temp_grammar.tpeg').unlink()



if __name__ == "__main__":
    # chunk_test(*sys.argv[1:])
    test(*sys.argv[1:])
