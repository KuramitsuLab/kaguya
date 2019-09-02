import sys
import re
from pegpy.main import *


def txt2array(path):
    s = ''
    with open(path, mode='r', encoding='utf_8') as f:
        s = f.read()
    s = re.sub(r'[ ]', '', s)
    s = re.sub(r'[。]', '。\n', s)
    return list(filter(lambda x: not x == '', s.split('\n')))


def main(argv):
    GRAMMAR = 'grammar/kaguya0.tpeg'
    options = parse_options(['-g', GRAMMAR])
    peg = load_grammar(options)
    parser = generator(options)(peg, name='Postp', **options)
    results = {
        'ok': [],
        'err': [],
    }
    lines = txt2array(argv[1])
    for count,line in enumerate(lines):
        sys.stdout.write(f'\rNow Processing: {count+1}/{len(lines)}')
        tree = repr(parser(line))
        if tree.startswith('[#err'):
            results['err'].append((line, tree))
        else:
            results['ok'].append((line, tree))
        sys.stdout.flush()
    err_rate = 'ERR_RATE: %d/%d' % len(results['err']), len(lines)
    print(err_rate)

def test(argv):
    NAME = argv[1]
    GRAMMAR = 'grammar/kaguya0.tpeg'
    options = parse_options(['-g', GRAMMAR])
    options['start'] = NAME
    peg = load_grammar(options)
    parser = generator(options)(peg, **options)
    try:
        while True:
            s = input('>>> ')
            print(repr(parser(s)))
    except Exception as e:
        print(e)



if __name__ == "__main__":
    # python src/tester.py test_text/hoge.txt
    # main(sys.argv)
    test(sys.argv)
