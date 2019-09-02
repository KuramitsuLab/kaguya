import sys
import re
from pegpy.main import *

GRAMMAR = './kaguya0.tpeg'

def txt2array(path):
    s = ''
    with open(path, mode='r', encoding='utf_8') as f:
        s = f.read()
    s = re.sub(r'[ ]', '', s)
    s = re.sub(r'[。]', '。\n', s)
    return list(filter(lambda x: not x == '', s.split('\n')))


def test(argv):
    options = parse_options(['-g', GRAMMAR])
    peg = load_grammar(options)
    parser = generator(options)(peg, **options)
    results = {
        'success': [],
        'fail': [],
    }

    lines = txt2array(argv[1])

    for count,line in enumerate(lines):
        sys.stdout.write(f'\rNow Processing: {count+1}/{len(lines)}')
        tree = repr(parser(line))
        if tree.startswith('[#err'):
            results['fail'].append((line, tree))
        else:
            results['success'].append((line, tree))
        sys.stdout.flush()
    fail_rate = '\nERR_RATE: %d/%d' % (len(results['fail']), len(lines))
    with open(argv[1][:-4]+'_fail.txt', mode='w') as f:
        f.write('\n'.join(list(map(lambda tpl: str(tpl[0])+'\n'+str(tpl[1])+'\n', results['fail']))))
    with open(argv[1][:-4]+'_success.txt', mode='w') as f:
        f.write('\n'.join(list(map(lambda tpl: str(tpl[0])+'\n'+str(tpl[1])+'\n', results['success']))))
    print(fail_rate)




def rule_test(argv):
    options = parse_options(['-g', GRAMMAR])
    options['start'] = argv[1]
    peg = load_grammar(options)
    parser = generator(options)(peg, **options)
    try:
        while True:
            s = input('>>> ')
            print(repr(parser(s)))
    except Exception as e:
        print(e)


if __name__ == "__main__":
    # python tester.py test/hoge.txt
    test(sys.argv)
    # rule_test(sys.argv)
