import sys
from pprint import pprint as pp
import copy


class Word():
    def __init__(self, word, katsuyo_type):
        self.w = str(word)
        self.t = katsuyo_type

    def __str__(self):
        return self.w

    def __repr__(self):
        return f'{self.w}:{self.t}'

    def __eq__(self, o):
        if not isinstance(o, Word):
            return NotImplemented
        return self.w == o.w

    def len(self):
        return len(self.word)

    def fullmatch(self, o):
        if not isinstance(o, Word):
            return NotImplemented
        if self.t == '副詞名詞' and not o.t == '副詞名詞':
            return self.w == o.w and o.t in ['副詞', '名詞']
        elif o.t == '副詞名詞' and not self.t == '副詞名詞':
            return self.w == o.w and self.t in ['副詞', '名詞']
        return self.w == o.w and self.t == o.t


def get_word_list(ans, target):
    ans_txt, sentence = [], []
    with open(ans, mode='r', encoding='utf_8') as f:
        ans_lines = f.read().split('\n')
    for l in ans_lines:
        if l == '':
            ans_txt.append(copy.deepcopy(sentence))
            sentence.clear()
        else:
            w,h = l.split(' ')
            h = h[1:-1]
            sentence.append(Word(w, h))
    sentence.clear()
    parse_txt = ['']*len(ans_txt)
    with open(target, mode='r', encoding='utf_8') as f:
        parse_lines = f.read().split('\n')
    if not parse_lines[0].startswith('No_'):
        print('Illegal compare file')
        sys.exit()
    count = int(parse_lines[0][3:])
    for l in parse_lines:
        if l.startswith('No_'):
            if len(sentence) > 0:
                parse_txt[count] = copy.deepcopy(sentence)
                count = int(l[3:])
            sentence.clear()
        else:
            w,h = l.split(' ')
            h = h[1:-1]
            sentence.append(Word(w, h))
    if len(sentence) > 0:
        parse_txt[count] = copy.deepcopy(sentence)
    return ans_txt, parse_txt


def compare(t1, t2):  # t1 is answer tokens, t2 is parsed tokens
    def word_match(l1_original, l2_original):
        l1, l2 = copy.deepcopy(l1_original), copy.deepcopy(l2_original)
        for target in l2:
            if target in l1:
                l1.remove(target)
        return l1

    def full_match(l1_original, l2_original):
        l1, l2 = copy.deepcopy(l1_original), copy.deepcopy(l2_original)
        for target in l2:
            for t in l1:
                if t.fullmatch(target):
                    l1.remove(target)
                    break
        return l1

    if len(t1) != len(t2):
        print(f'compared files must be same length')
        sys.exit()
    wm, fm = [], []
    for i in range(len(t1)):
        if t2[i] == '':
            wm.append(f'ERR')
            fm.append(f'ERR')
        else:
            wm.append(word_match(t1[i], t2[i]))
            fm.append(full_match(t1[i], t2[i]))
    return wm, fm


def log_detail(ml):
    tokens = []
    for l in ml:
        for t in l:
            if isinstance(t, Word):
                tokens.append(f'{t.w} ({t.t})')
    d = {}
    for u in set(tokens):
        d[u] = 0
    for t in tokens:
        d[t] += 1
    pp(d)
    print()


def main(ans_path, target_path):
    # ans_path = 'test/python_ans-edit.txt'
    # target_path = 'test_result/test_python_20/for_compare_ver_kaguya-kai.txt'
    answer, parsed = get_word_list(ans_path, target_path)
    wm, fm = compare(answer, parsed)
    # print(f'{parsed}', file=sys.stderr)
    print('----- Detail -----')
    ANSS = len(answer)  # 解析対象の文の数
    PSDS = len(answer) - parsed.count('')  # 解析に成功した文の数
    ANSTALL = sum(len(l) for l in answer)  # 正解データの単語の数
    ANST = sum(len(l) if isinstance(parsed[i], list) else 0 for i,l in enumerate(answer))   # 解析に成功した文における単語の数
    PSDT = sum(len(l) for l in list(filter(lambda x:isinstance(x,list), parsed)))  # 解析結果の単語の数
    WMS = sum([1 if l == [] else 0 for l in wm])  # 品詞を考慮しないマッチで正解データと一致した文の数
    FMS = sum([1 if l == [] else 0 for l in fm])  # 品詞を考慮したマッチで正解データと一致した文の数
    WMT = sum(len(l) for l in wm)  # 品詞を考慮しないマッチでマッチしなかった正解単語の数
    FMT = sum(len(l) for l in fm)  # 品詞を考慮したマッチでマッチしなかった正解単語の数
    print('【品詞を考慮しない比較において誤ったマッチとなった原因】')
    log_detail(wm)
    print('【品詞を考慮した比較において誤ったマッチとなった原因】')
    log_detail(fm)
    print(f'正解データと比較したファイル　　　　　　: {target_path}')
    print(f'品詞を考慮せず正解データに一致した文の数: {WMS} / {PSDS} / {ANSS}')
    print(f'品詞も考慮して正解データに一致した文の数: {FMS} / {PSDS} / {ANSS}')
    print(f'マッチした単語の数（品詞考慮なし）　　　: {ANST - WMT} / {ANST}')
    print(f'マッチした単語の数（品詞考慮あり）　　　: {ANST - FMT} / {ANST}')
    print(f'解析に成功した文の正解データの単語数　　: {ANST} / {ANSTALL}')
    print(f'解析結果の単語数　　　　　　　　　　　　: {PSDT}')


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('Not enough argument')
    main(*sys.argv[1:3])
