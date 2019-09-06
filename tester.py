import sys
import time
from pathlib import Path
import datetime
import re
from pegpy.main import *


GRAMMAR = 'kaguya0.tpeg'


def txt2array(path):
    s = ''
    with open(path, mode='r', encoding='utf_8') as f:
        s = f.read()
    s = re.sub(r'[ ]', '', s)
    s = re.sub(r'[。]', '。\n', s)
    return list(filter(lambda x: not x == '', s.split('\n')))


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
    try:
        new_fpath = fpath[:(fpath.rfind('.txt'))] + f'_{count}.txt'
        with open(new_fpath, mode='x', encoding='utf_8') as f:
            s = ''
            for text, tree in results:
                s += text + '\n'
                s += tree + '\n'
                s += '\n'
            f.write(s[:-1])
    except FileExistsError:
        write_result(fpath, results, count+1)


def print_err(lst):
    for fst, snd in lst:
        print('入力: ' + fst)
        print(snd + '\n')


def test(argv):
    options = parse_options(['-g', GRAMMAR])
    peg = load_grammar(options)
    parser = generator(options)(peg, **options)
    results = {
        'success': [],
        'fail': [],
    }

    str_list = txt2array(argv[1])
    FILE_NAME = argv[1][(argv[1].rfind('/'))+1 : (argv[1].rfind('.'))]
    MAX_COUNT = int(argv[2]) if len(argv) > 2 else len(str_list)
    Path('test/result/success').mkdir(parents=True, exist_ok=True)
    Path('test/result/fail').mkdir(parents=True, exist_ok=True)

    START = time.time()
    for count,s in enumerate(str_list):
        if count >= MAX_COUNT:break
        sys.stdout.write(f'\rNow Processing: {count+1}/{MAX_COUNT}')
        tree = parser(s)
        if 'Syntax Error' in repr(tree):
            results['fail'].append((s, f'残り: [{str(tree)}]'))
        else:
            results['success'].append((s, repr(tree)))
        sys.stdout.flush()
    STOP = time.time()

    print()
    FAIL_RATE = (len(results['fail']), MAX_COUNT)
    write_result(f'test/result/success/{FILE_NAME}.txt', results['success'])
    write_result(f'test/result/fail/{FILE_NAME}.txt', results['fail'])
    logging(argv[1], MAX_COUNT, STOP-START, FAIL_RATE)
    print(f'Fail Rate: {FAIL_RATE[0]}/{FAIL_RATE[1]}')
    print_err(results['fail'])


if __name__ == "__main__":
    test(sys.argv)
