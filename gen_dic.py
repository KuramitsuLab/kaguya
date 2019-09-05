import pprint
import re


class Word():
    __slots__ = ['word', 'genre', 'katsuyo']

    def __init__(self, w, g, k):
        self.word = w
        self.genre = g
        self.katsuyo = k

    def __str__(self):
        return self.word

    def __repr__(self):
        return f'{self.word} {self.genre} {self.katsuyo}'


dic_list = {
    'Adj.dic': [],  # 形容詞
    'Adnominal.dic': [],  # 連体詞
    'Adverb.dic': [],  # 副詞
    'Auxil.dic': [],  # 助動詞
    'Conjunction.dic': [],  # 接続詞
    'Filler.dic': [],  # フィラー
    'Interjection.dic': [],  # 感動詞
    'Noun.adjv.dic': [],  # 形容動詞語幹
    'Noun.adverbal.dic': [],  # 副詞可能
    'Noun.demonst.dic': [],  # 名詞代名詞
    'Noun.dic': [],  # 名詞
    'Noun.nai.dic': [],  # 名詞 ナイ形容詞語幹
    'Noun.name.dic': [],  # 固有名詞 人名
    'Noun.number.dic': [],  # 名詞 数
    'Noun.org.dic': [],  # 固有名詞 組織
    'Noun.others.dic': [],  # 名詞 非自立
    'Noun.place.dic': [],  # 固有名詞 地域
    'Noun.proper.dic': [],  # 固有名詞
    'Noun.verbal.dic': [],  # 名詞 サ変接続
    'Onebyte.dic': [],  # 記号や数字
    'Others.dic': [],  # その他
    'Postp-col.dic': [],  # 格助詞
    'Postp.dic': [],  # 助詞
    'Prefix.dic': [],  # 接頭詞
    'Suffix.dic': [],  # 名詞 接尾
    'Symbol.dic': [],  # 記号
    'Verb.dic': [],  # 動詞
}


def verb_classify(t):
    # 活用型の名前の変換
    if   '五段' in t and 'カ行' in t:
        return 'VERB5KA'
    elif '五段' in t and 'サ行' in t:
        return 'VERB5SA'
    elif '五段' in t and 'タ行' in t:
        return 'VERB5TA'
    elif '五段' in t and 'ナ行' in t:
        return 'VERB5NA'
    elif '五段' in t and 'マ行' in t:
        return 'VERB5MA'
    elif '五段' in t and 'ラ行' in t:
        return 'VERB5RA'
    elif '五段' in t and 'ワ行' in t:
        return 'VERB5WA'
    elif '五段' in t and 'ガ行' in t:
        return 'VERB5GA'
    elif '五段' in t and 'バ行' in t:
        return 'VERB5BA'
    elif '一段' in t:
        return 'VERB1'
    elif 'サ変' in t and 'スル' in t:
        return 'SAHEN_SURU'
    elif 'サ変' in t and 'ズル' in t:
        return 'SAHEN_ZURU'
    elif 'カ変' in t:
        return 'KAHEN'
    else:
        return 'UNKNOWN'


def load_dic(dic_list):
    # dicファイルをWord型のリストに変換してdic_listに追加
    def dict_parser(s):
        GENRE = s[s.find('(', s.find('品詞'))+1: s.find(')',s.find('品詞'))].replace(' ','-')
        WORD = s[s.find('(', s.find('見出し語'))+1: s.find(')',s.find('見出し語'))].split(' ')[0]
        KATSUYO = s[s.find(' ', s.find('活用型'))+1: s.find(')', s.find('活用型'))] if '活用型' in s else ''
        return Word(WORD, GENRE, KATSUYO)

    for path in dic_list:
        with open('./ipadic-2.7.0/'+path, mode='r', encoding='euc_jp') as f:
            for s in f.readlines():
                w = dict_parser(s)
                dic_list[path].append(w)


def hiragana_check(dic_list, genre):
    def len_of_word(w):
        return len(str(w))

    hira_only = []
    hira_mix = []
    for key in dic_list:
        for e in dic_list[key]:
            if re.compile('[あ-ん]+').fullmatch(str(e)) and genre in e.genre:
                hira_only.append(e)
            elif re.search(r'[あ-ん]', str(e)) and genre in e.genre:
                hira_mix.append(e)
    hira_only.sort(key=len_of_word)
    hira_mix.sort(key=len_of_word)
    with open(f'hira_only_of_{genre}.txt', mode='w') as f:
        for p in hira_only:
            f.write(repr(p)+'\n')
    with open(f'hira_mix_of_{genre}.txt', mode='w') as f:
        for p in hira_mix:
            f.write(repr(p)+'\n')
    print(f'ひらがなのみの{genre}の数：{len(hira_only)}')
    print(f'ひらがな混在の{genre}の数：{len(hira_mix)}')


def gen_verb(dic_list):
    d = {
        "VERB5KA": [],
        "VERB5SA": [],
        "VERB5TA": [],
        "VERB5NA": [],
        "VERB5MA": [],
        "VERB5RA": [],
        "VERB5WA": [],
        "VERB5GA": [],
        "VERB5BA": [],
        "VERB1": [],
        "SAHEN_SURU": [],
        "SAHEN_ZURU": [],
        "KAHEN": [],
        "UNKNOWN": []
    }
    for p in dic_list['Verb.dic']:
        path_name = verb_classify(p.katsuyo)
        d[path_name].append(p)

    for k in d:
        with open(f'./grammar/dic/verbs/{k}.txt', mode='w') as f:
            s = ''
            for p in d[k]:
                if not (str(p) in ['行く', '来る', 'くる', 'する'] or len(str(p)) < 2 or re.match('[あ-ん]{2}$', str(p))):
                    if k in ['SAHEN_SURU', 'SAHEN_ZURU', 'KAHEN']:
                        s += str(p)[:-2]+'\n'
                    else:
                        s += str(p)[:-1]+'\n'
            f.write(s)


def generate(dic_list):
    gen_verb(dic_list)
    with open(f'grammar/dic/ADJ.txt', mode='w') as f:
        s = ''
        for p in dic_list['Adj.dic']:
            s += str(p)[:-1] + '\n'
        for p in dic_list['Noun.nai.dic']:
            s += str(p)+'な\n'
        f.write(s)
    with open(f'grammar/dic/ADJV.txt', mode='w') as f:
        s = ''
        for p in dic_list['Noun.adjv.dic']:
            s += str(p) + '\n'
        f.write(s)
    with open(f'grammar/dic/ADNM.txt', mode='w') as f:
        s = ''
        for p in dic_list['Adnominal.dic']:
            s += str(p) + '\n'
        f.write(s)
    with open(f'grammar/dic/CONJ.txt', mode='w') as f:
        s = ''
        for p in dic_list['Conjunction.dic']:
            s += str(p) + '\n'
        f.write(s)
    with open(f'grammar/dic/ADV.txt', mode='w') as f:
        s = ''
        for p in dic_list['Adverb.dic']:
            s += str(p) + '\n'
        f.write(s)


load_dic(dic_list)
generate(dic_list)

