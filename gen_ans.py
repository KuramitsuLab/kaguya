import MeCab
from functools import reduce
import re
import sys

m = MeCab.Tagger()


class MecabWord():
    __slots__ = ['word', 'hinshi', 'origin']
    def __init__(self, raw, h='*', d1='*', d2='*', d3='*', g='*', kt='*', o='*', ym='*', ot='*'):
        # self, 単語, 品詞, 品詞の詳細1, 品詞の詳細2, 品詞の詳細3, 活用の種類, 活用形, 原型, 読み方, 発音
        self.word = raw
        if h == '名詞' and d1 == '形容動詞語幹':
            self.hinshi = '形容動詞'
        elif h == '接頭詞':
            self.hinshi = '名詞'
        else:
            self.hinshi = h
        self.origin = o

    def __str__(self):
        return self.word

    def __repr__(self):
        s = ''
        for v in self.__dict__.values():
            if v != '*':
                s += f'{v}, '
        return s[:-2]

    def slim(self):
        if self.word == '。':
            return ''
        else:
            return f'{self.word} ({self.hinshi})'


# sentence -> list<MecabWord>
def mecab_parse(s):
    ADJV_GOKAN = ['だろ', 'だっ', 'で', 'に', 'だ', 'な', 'なら']
    ADJV_CON = ['そうだろ', 'そうだっ', 'そうで', 'そうに', 'そうだ', 'そうなら', 'そうな',
                'らしかっ', 'らしく', 'らしい', 'らしい', 'らしけれ', 'でしょ', 'でし', 'です', 'です']
    words = []
    stack = []
    sahen = []
    tokens = m.parse(s).split('\n')[:-2]  # remove EOS
    for t in tokens:
        (raw, info) = t.split()
        mw = MecabWord(raw, *info.split(','))
        if re.fullmatch(r'[・、。!！?？\(\)「」\[\]"\'（）]', raw):
            if len(stack) > 0:
                con_noun = str(reduce(lambda x, y: str(x)+str(y), stack))
                words.append(MecabWord(con_noun, '名詞'))
                stack.clear()
            continue
        if mw.hinshi in ['名詞']:
            stack.append(mw)
        elif len(stack) > 0:
            con_noun = str(reduce(lambda x, y: str(x)+str(y), stack))
            stack.clear()
            if mw.hinshi == '動詞' and mw.origin == 'する':
                words.append(MecabWord(con_noun+mw.word, '動詞'))
                sahen.append(con_noun)
            else:
                words.append(MecabWord(con_noun, '名詞'))
                words.append(mw)
        elif mw.hinshi in ['助詞', '助動詞'] and words[-1].hinshi == '形容動詞':
            adjv = words.pop(-1)
            if mw.word in ADJV_GOKAN:
                words.append(MecabWord(adjv.word+mw.word, '形容動詞'))
            elif mw.word in ADJV_CON:
                words.append(adjv)
                words.append(mw)
            else:
                words.append(MecabWord(adjv.word, '名詞'))
                words.append(mw)
        else:
            words.append(mw)
    return words,sahen


def gen_answer(fpath):
    all_words = []
    all_sahen = []
    with open(fpath, mode='r', encoding='utf_8') as f:
        txt = f.read().split('\n')[1:]
    for s in txt:
        words,sahen = mecab_parse(s)
        all_words += words
        all_sahen += sahen
        all_words.append(MecabWord('。'))  # add EOS
    with open(f'{fpath[:-4]}_ans.txt', mode='w', encoding='utf_8') as f:
        f.write('\n'.join(map(lambda w: w.slim(), all_words)))
    print('\n'.join(set(all_sahen)))


if __name__ == "__main__":
    gen_answer(sys.argv[1])











