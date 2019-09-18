import MeCab
import re
from pathlib import Path
import sys


m = MeCab.Tagger("-Ochasen")

test_cases = Path('test/').glob('*.txt')

class Word():
    def __init__(self, w='None', y='None', sy='None', h='None', *remain):
        self.word = w
        self.yomi = y
        self.suyomi = sy
        self.hinshi = h

    def __str__(self):
        return self.word


def cat(lst):
    s = ''
    res = []
    for e in lst:
        if '名詞' in e.hinshi:
            if not str(e) in res:
                res.append(str(e))
            if s == '':
                s = str(e)
            else:
                s += str(e)
        else:
            if not str(e) in res:
                res.append(s)
            s = ''
    return [p for p in res if p != '']


def main(args):
    file = args[1]
    filename = file[file.rfind('/')+1:]
    words = []
    with open(file, mode='r', encoding='utf_8') as f:
        for count,l in enumerate(f.readlines()):
            sub_word = []
            l = l.replace(' ', '')
            if count == 0:continue
            kana = re.findall(r'[ァ-ヴ][ァ-ヴー・]*', l)
            alpha = re.findall(r'[ -~]+', l)
            for w in kana+alpha:
                words.append(str(w))
            for p in m.parse(l).split('\n'):
                datas = p.split()  # [そのまま, 読み方, 素読み, 品詞名]
                # print(' '.join(datas))
                sub_word.append(Word(*datas))
            words += cat(sub_word)
    ipa_noun = ''
    with open('dic/NOUN.txt', mode='r', encoding='utf_8') as f:
       ipa_noun = f.read()
    with open(f'dic/TestNoun.txt', mode='w', encoding='utf_8') as f:
        f.write(ipa_noun)
        f.write('\n'.join(list(set(words))))


if __name__ == "__main__":
    main(sys.argv)
