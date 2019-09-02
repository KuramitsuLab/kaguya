import pprint as pp
import re

def classify(t):
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


def load_dic(dic_path, verbs):
    def dict_parser(s):
        WORD = s[s.find('(', s.find('見出し語'))+1: s.find(')',s.find('見出し語'))].split(' ')[0]
        TYPE = s[s.find(' ', s.find('活用型'))+1: s.find(')', s.find('活用型'))]
        return (WORD, TYPE)

    lst = []
    with open(dic_path, mode='r', encoding='euc_jp') as f:
        for s in f.readlines():
            (w, t) = dict_parser(s)
            key = classify(t)
            if not w in verbs[key]:
                verbs[key].append(w)

def dic2tpeg(verbs):
    tpeg1,tpeg2 = ('','')
    junior = ['V5KA', 'V5SA', 'V5TA', 'V5NA',
          'V5MA', 'V5RA', 'V5WA', 'V5GA', 'V5BA', 'V1', 'SSURU', 'SZURU', 'KAHEN', 'UNKNOWN']
    for j,k in enumerate(verbs):
        if('UNKNOWN' in k):break
        ls = [verbs[k][i:i+100] for i in range(0,len(verbs[k]),100)]
        tpeg1 += f'{k} =\n'
        for count,l in enumerate(ls):
            # slash = ' ' if count == 0 else '/'
            tpeg1 += f'    / {junior[j]}_{count}\n'
            tpeg2 += f'{junior[j]}_{count} =\n'
            for p in l:
                if p in ['行く','来る','くる','する'] or len(p) < 2 or re.match('[あ-ん]{2}$', p):
                    continue
                if k in ['SAHEN_SURU', 'SAHEN_ZURU', 'KAHEN']:
                    tpeg2 += f'    / \'{p[:-2]}\'\n'
                else:
                    tpeg2 += f'    / \'{p[:-1]}\'\n'
            tpeg2 += '\n'
        tpeg1 += f'\n'
    return tpeg1+tpeg2


def dic2tpeg_ver2(verbs):
    katsuyo = {
        "VERB5KA": ['[かこ] #Mizen', '[きい] #Renyo', '[く] #SyushiRentai', '[け] #KateiMeirei'],
        "VERB5SA": ['[さそ] #Mizen', '[し] #Renyo', '[す] #SyushiRentai', '[せ] #KateiMeirei'],
        "VERB5TA": ['[たと] #Mizen', '[ちっ] #Renyo', '[つ] #SyushiRentai', '[て] #KateiMeirei'],
        "VERB5NA": ['[なの] #Mizen', '[にん] #Renyo', '[ぬ] #SyushiRentai', '[ね] #KateiMeirei'],
        "VERB5MA": ['[まも] #Mizen', '[みん] #Renyo', '[む] #SyushiRentai', '[め] #KateiMeirei'],
        "VERB5RA": ['[らろ] #Mizen', '[りっ] #Renyo', '[る] #SyushiRentai', '[れ] #KateiMeirei'],
        "VERB5WA": ['[わお] #Mizen', '[いっ] #Renyo', '[う] #SyushiRentai', '[え] #KateiMeirei'],
        "VERB5GA": ['[がご] #Mizen', '[ぎい] #Renyo', '[ぐ] #SyushiRentai', '[げ] #KateiMeirei'],
        "VERB5BA": ['[ばぼ] #Mizen', '[びん] #Renyo', '[ぶ] #SyushiRentai', '[べ] #KateiMeirei'],
        "VERB1": ['[る] #SyushiRentai', '[れ] #Katei', '[ろよ] #Meirei', '#MizenRenyo'],
        "SAHEN_SURU": ['\'する\' #SyushiRentai', '\'すれ\' #Katei', '(\'しろ\' / \'せよ\') #Meirei', '[し] #MizenRenyo', '[させ] #Mizen'],
        "SAHEN_ZURU": ['\'ずる\' #SyushiRentai', '\'ずれ\' #Katei', '(\'じろ\' / \'ぜよ\') #Meirei', '[じ] #MizenRenyo', '[ざぜ] #Mizen'],
        "KAHEN": ['[き] #Renyo', '(\'くる\' / \'来る\') #SyushiRentai', '(\'くれ\' / \'来れ\') #Katei', '(\'こい\' / \'来い\') #Meirei', '[来] #MizenRenyo', '[こ] #Mizen'],
    }

    tpeg_gokan = ''
    tpeg_verb_all = 'Verb =\n    / VerbUnique_begin\n'
    tpeg_verbs = {}
    for j, k in enumerate(verbs):
        if('UNKNOWN' in k):break
        s_len = k[k.find('LEN')+3:]
        v_name = k[:k.find('LEN')-1]
        # ls = [verbs[k][i:i+100] for i in range(0, len(verbs[k]), 100)]
        if not str(s_len) in tpeg_verbs:
            tpeg_verbs[str(s_len)] = ''
        # for count, l in enumerate(ls):
        for gobi in katsuyo[v_name]:
            tpeg_verbs[str(s_len)] += f'    / {{ {k} {gobi} }}\n'
        tpeg_gokan += f'{k} =\n'
        for p in verbs[k]:
            if p in ['行く', '来る', 'くる', 'する'] or len(p) < 2 or re.match('[あ-ん]{2}$', p):
                continue
            if v_name in ['SAHEN_SURU', 'SAHEN_ZURU', 'KAHEN']:
                tpeg_gokan += f'    / \'{p[:-2]}\'\n'
            else:
                tpeg_gokan += f'    / \'{p[:-1]}\'\n'
        tpeg_gokan += '\n'
    lens = []
    for ln in tpeg_verbs:
        lens.append(int(ln))
    lens.sort(reverse=True)
    for i in lens:
        tpeg_verb_all += tpeg_verbs[str(i)]
    tpeg_verb_all += '    / VerbUnique_end\n\n' + tpeg_gokan
    return tpeg_verb_all



# 動詞辞書の用意
verbs = {
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
disted_verbs = {}

load_dic('ipadic-2.7.0/Verb.dic', verbs)

# pp.pprint(verbs)

for k in verbs:
    verbs[k].sort(key=len, reverse=True)

for k in verbs:
    for p in verbs[k]:
        if p in ['行く', '来る', 'くる', 'する'] or len(p) < 2 or re.match('[あ-ん]{2}$', p):
            continue
        if not f'{k}_LEN{len(p)}' in disted_verbs:
            disted_verbs[f'{k}_LEN{len(p)}'] = []
        disted_verbs[f'{k}_LEN{len(p)}'].append(p)

# for k in disted_verbs:print(k)

# pp.pprint(disted_verbs)
# VERB5KA_LEN1, VERB5SA_LEN1, VERB1_LEN1, SAHEN_SURU_LEN2, KAHEN_LEN2
# [く], [す], [る], [する], [くる、来る]

# tpeg_str = dic2tpeg(verbs)
tpeg_str = dic2tpeg_ver2(disted_verbs)

print(tpeg_str)
