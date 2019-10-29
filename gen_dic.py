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


def gen_hira(dic_list, genre):
    def len_of_word(w):
        return len(str(w))

    hira_only = []
    hira_mix = []
    for key in dic_list:
        for e in dic_list[key]:
            if re.compile('[ぁ-ん]+').fullmatch(str(e)) and genre in e.genre:
                if not str(e) in hira_only:
                    hira_only.append(e)
            elif re.search(r'[ぁ-ん]', str(e)) and genre in e.genre:
                if not str(e) in hira_mix:
                    hira_mix.append(e)
    hira_only.sort(key=len_of_word)
    hira_mix.sort(key=len_of_word)
    with open(f'dic/NOUN.txt', mode='w') as f:
        for p in hira_only:
            if len(str(p)) >= 2:
                f.write(str(p)+'\n')
        for p in hira_mix:
            f.write(str(p)+'\n')
    # print(f'ひらがなのみの{genre}の数：{len(hira_only)}')
    # print(f'ひらがな混在の{genre}の数：{len(hira_mix)}')


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
        with open(f'dic/Verb/{k}.txt', mode='w') as f:
            for p in d[k]:
                bad_cond = [
                    str(p) in ['行く', '来る', 'くる', 'する'],  # PEG側に定義済みの動詞
                    len(str(p)) < 2,  # 1文字動詞はかなり特殊なので除外
                    # re.match('[ぁ-ん]{2}$', str(p))  # ひらがな2文字動詞の除外
                ]
                if not True in bad_cond:
                    if k in ['SAHEN_SURU', 'SAHEN_ZURU', 'KAHEN']:
                        # サ変、カ変は後ろ2文字が活用語尾
                        f.write(str(p)[:-2]+'\n')
                    # elif k in ['VERB1']:
                    #     # 一段動詞は語幹部分がひらがな1文字になるとよろしくない
                    #     if len(str(p)) > 2:
                    #         f.write(str(p)[:-1]+'\n')
                    else:
                        # 他の動詞は後ろ1文字が活用語尾
                        f.write(str(p)[:-1]+'\n')


def generate(dic_list):
    gen_verb(dic_list)
    gen_hira(dic_list, '名詞')
    with open(f'dic/ADJ.txt', mode='w') as f:
        for p in dic_list['Adj.dic']:
            f.write(str(p)[:-1] + '\n')
        for p in dic_list['Noun.nai.dic']:
            f.write(str(p)+'な\n')
    with open(f'dic/ADJV.txt', mode='w') as f:
        for p in dic_list['Noun.adjv.dic']:
            f.write(str(p) + '\n')
    with open(f'dic/ADNM.txt', mode='w') as f:
        for p in dic_list['Adnominal.dic']:
            f.write(str(p) + '\n')
    with open(f'dic/POSTP.txt', mode='w') as f:
        writed = []
        for p in dic_list['Postp.dic']:
            if not str(p) in ['ちゃ', 'ん'] and re.match('[ぁ-ん]+$', str(p)) and not str(p) in writed:
                f.write(str(p) + '\n')
                writed.append(str(p))
        # for p in dic_list['Postp-col.dic']:
        #     f.write(str(p) + '\n')
    with open(f'dic/CONJ.txt', mode='w') as f:
        for p in dic_list['Conjunction.dic']:
            f.write(str(p) + '\n')
    with open(f'dic/ADV.txt', mode='w') as f:
        for p in dic_list['Adverb.dic']:
            f.write(str(p) + '\n')
        for p in dic_list['Noun.adverbal.dic']:
            f.write(str(p) + '\n')
    with open(f'dic/INTJ.txt', mode='w') as f:
        for p in dic_list['Interjection.dic']:
            f.write(str(p) + '\n')


load_dic(dic_list)
generate(dic_list)

