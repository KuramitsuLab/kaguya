from enum import IntEnum
import pprint as pp


# 活用型クラス
class Katsuyo(IntEnum):
    Mizen = 0
    Renyo = 1
    Syushi = 2
    Rentai = 3
    Katei = 4
    Meirei = 5
    Gokan = 6

    def __str__(self):
        if   self.name == 'Mizen':
            return '未然形'
        elif self.name == 'Renyo':
            return '連用形'
        elif self.name == 'Syushi':
            return '終止形'
        elif self.name == 'Rentai':
            return '連体形'
        elif self.name == 'Katei':
            return '仮定形'
        elif self.name == 'Meirei':
            return '命令形'
        elif self.name == 'Gokan':
            return '語幹'


# 基本文字クラス
class BaseWord():
    __slots__ = ['word', 'katsuyo', 'base']

    def __init__(self, w, k, b):
        self.word = w
        self.katsuyo = k
        self.base = b

    def __str__(self):
        return self.word


# 動詞
class Verb(BaseWord):
    def __init__(self, *args):
        super().__init__(*args)

    def __repr__(self):
        return f'{self.word}：{self.base}活用の{str(self.katsuyo)}の動詞'


# 形容詞または形容動詞
class Adjective(BaseWord):
    def __init__(self, *args):
        super().__init__(*args)

    def __repr__(self):
        return f'{self.word}：{str(self.katsuyo)}の{self.base}'


# 活用しない品詞
# 名詞（体言）、連体詞、助詞
class ImmutableWord():
    __slots__ = ['word', 'base']

    def __init__(self, w, b):
        self.word = w
        self.base = b

    def __str__(self):
        return self.word

    def __repr__(self):
        return f'{self.word}: {self.base}'


# 助動詞
class AuxVerb(BaseWord):
    __slots__ = ['mean', 'connection']

    def __init__(self, w, k, b, m, c):
        super().__init__(w, k, b)
        self.mean = m
        if isinstance(c, tuple):
            self.connection = list(c)
        elif isinstance(c, type(lambda x:x)):
            self.connection = [c]

    def __repr__(self):
        return f'{self.word}：{self.mean}の助動詞「{self.base}」の{str(self.katsuyo)}'

    def connect(self, pre_word):
        connection_check = map(lambda f: f(pre_word), self.connection)
        return (True in connection_check)


def judge(x, v_or_av, base_or_pattern, katsuyo):
    bs = []
    # 動詞または助動詞かどうか
    if not isinstance(x, v_or_av):
        return False
    # 接続できる活用（五段、サ変...）または助動詞（ます、される...）かどうか
    if isinstance(base_or_pattern, list):
        bs.append(x.base in base_or_pattern)
    elif isinstance(base_or_pattern, tuple):
        bs.append(not x.base in base_or_pattern)
    # 接続できる活用形かどうか
    bs.append(str(x.katsuyo) == katsuyo)
    return not False in bs


def judge2(x, base_or_pattern, word):
    bs = []
    if not isinstance(x, ImmutableWord):
        return False
    if isinstance(base_or_pattern, list):
        bs.append(x.base in base_or_pattern)
    elif isinstance(base_or_pattern, tuple):
        bs.append(not x.base in base_or_pattern)
    if isinstance(word, str):
        bs.append(x.word == word)
    return not False in bs


def make_avs():
    connection = [
        # せる
        lambda x: judge(x, Verb, ['五段', 'サ変'], '未然形'),
        # させる
        lambda x: judge(x, Verb, ['一段', 'カ変'], '未然形'),
        # れる
        lambda x: judge(x, Verb, ['五段', 'サ変'], '未然形'),
        # られる
        (lambda x: judge(x, Verb, ['一段', 'カ変'], '未然形'),
        lambda x: judge(x, AuxVerb, ['せる', 'させる'], '未然形')),
        # ない1（なかっ）
        (lambda x: judge(x, Verb, True, '未然形'),
        lambda x: judge(x, AuxVerb, ['せる', 'させる', 'れる', 'られる', 'たがる1'], '未然形')),
        # ない2（なく）
        (lambda x: judge(x, Verb, True, '未然形'),
        lambda x: judge(x, AuxVerb, ['せる', 'させる', 'れる', 'られる', 'たがる1'], '未然形')),
        # ず（ず）
        (lambda x: judge(x, Verb, True, '未然形'),
        lambda x: judge(x, AuxVerb, ['せる', 'させる', 'れる', 'られる', 'たがる1'], '未然形')),
        # ん（ん、「ません」専用）
        lambda x: judge(x, AuxVerb, ['ます1'], '未然形'),
        # う
        (lambda x: judge(x, Verb, ['五段'], '未然形'),
        lambda x: judge(x, Adjective, ['形容詞', '形容動詞'], '未然形'),
        lambda x: judge(x, AuxVerb, ['ない', 'たい', 'た', 'だ1', 'そうだ11', 'ようだ1', 'ます2', 'だ21', 'です1', 'です2'], '未然形')),
        # よう
        (lambda x: judge(x, Verb, ['一段', 'カ変', 'サ変'], '未然形'),
        lambda x: judge(x, AuxVerb, ['せる','させる','れる','られる'], '未然形')),
        # まい
        (lambda x: judge(x, Verb, ['一段', 'カ変', 'サ変'], '未然形'),
        lambda x: judge(x, Verb, ['五段'], '終止形'),
        lambda x: judge(x, AuxVerb, ['ます'], '終止形'),
        lambda x: judge(x, AuxVerb, ['せる', 'させる', 'れる', 'られる'], '未然形')),
        # たい1（たかっ）
        (lambda x: judge(x, Verb, True, '連用形'),
        lambda x: judge(x, AuxVerb, ['せる', 'させる', 'れる', 'られる'], '連用形')),
        # たい2（たく）
        (lambda x: judge(x, Verb, True, '連用形'),
        lambda x: judge(x, AuxVerb, ['せる', 'させる', 'れる', 'られる'], '連用形')),
        # たがる1（たがり）
        (lambda x: judge(x, Verb, True, '連用形'),
        lambda x: judge(x, AuxVerb, ['せる', 'させる', 'れる', 'られる'], '連用形')),
        # たがる2（たがっ）
        (lambda x: judge(x, Verb, True, '連用形'),
        lambda x: judge(x, AuxVerb, ['せる', 'させる', 'れる', 'られる'], '連用形')),
        # た
        (lambda x: judge(x, Verb, True, '連用形'),
        lambda x: judge(x, Adjective, ['形容詞', '形容動詞'], '連用形'),
        lambda x: judge(x, AuxVerb, ('ない2','ず','たい2','たがる1','そうだ12','そうだ13','そうだ2','ようだ2','ようだ3','らしい2','だ21','だ23'), '連用形')),
        # だ1（ガ/ナ/バ/マ行五段の動詞に接続する時のみ）
        lambda x: judge(x, Verb, ['五段'], '連用形'),
        # そうだ11（そうだっ）
        (lambda x: judge(x, Verb, True, '連用形'),
        lambda x: judge(x, Adjective, ['形容詞', '形容動詞'], '語幹'),
        lambda x: judge(x, AuxVerb, ['せる', 'させる', 'れる', 'られる'], '連用形')),
        # そうだ12（そうで）
        (lambda x: judge(x, Verb, True, '連用形'),
        lambda x: judge(x, Adjective, ['形容詞', '形容動詞'], '語幹'),
        lambda x: judge(x, AuxVerb, ['せる', 'させる', 'れる', 'られる'], '連用形')),
        # そうだ13（そうに）
        (lambda x: judge(x, Verb, True, '連用形'),
        lambda x: judge(x, Adjective, ['形容詞', '形容動詞'], '語幹'),
        lambda x: judge(x, AuxVerb, ['せる', 'させる', 'れる', 'られる'], '連用形')),
        # そうだ2
        (lambda x: judge(x, Verb, True, '終止形'),
        lambda x: judge(x, Adjective, ['形容詞', '形容動詞'], '終止形'),
        lambda x: judge(x, AuxVerb, ('ん','う','よう','まい','そうだ11','そうだ2','ます1','ようだ1','です1','です2'), '終止形')),
        # ようだ1（ようだ）
        (lambda x: judge(x, Verb, True, '連体形'),
        lambda x: judge(x, Adjective, ['形容詞', '形容動詞'], '連体形'),
        lambda x: judge(x, AuxVerb, ('ん', 'う', 'よう', 'まい', 'ようだ1', 'そうだ11', 'ます1', 'らしい1'), '連体形'),
        lambda x: judge2(x, ['助詞'], 'の'),
        lambda x: judge2(x, ['連体詞'], 'その')),
        # ようだ2（ようで）
        (lambda x: judge(x, Verb, True, '連体形'),
        lambda x: judge(x, Adjective, ['形容詞', '形容動詞'], '連体形'),
        lambda x: judge(x, AuxVerb, ('ん', 'う', 'よう', 'まい', 'ようだ1', 'そうだ11', 'ます1', 'らしい1'), '連体形'),
        lambda x: judge2(x, ['助詞'], 'の'),
        lambda x: judge2(x, ['連体詞'], 'その')),
        # ようだ3（ように）
        (lambda x: judge(x, Verb, True, '連体形'),
        lambda x: judge(x, Adjective, ['形容詞', '形容動詞'], '連体形'),
        lambda x: judge(x, AuxVerb, ('ん', 'う', 'よう', 'まい', 'ようだ1', 'そうだ11', 'ます1', 'らしい1'), '連体形'),
        lambda x: judge2(x, ['助詞'], 'の'),
        lambda x: judge2(x, ['連体詞'], 'その')),
        # らしい1（らしかっ）
        (lambda x: judge(x, Verb, True, '終止形'),
        lambda x: judge(x, Adjective, ['形容詞'], '終止形'),
        lambda x: judge(x, Adjective, ['形容動詞'], '語幹'),
        lambda x: judge(x, AuxVerb, ('う','よう','まい','そうだ11','そうだ2','ようだ1','らしい1','ます1','です2','ん'), '終止形'),
        lambda x: judge2(x, ['名詞', '助詞'], True)),
        # らしい2（らしく）
        (lambda x: judge(x, Verb, True, '終止形'),
        lambda x: judge(x, Adjective, ['形容詞'], '終止形'),
        lambda x: judge(x, Adjective, ['形容動詞'], '語幹'),
        lambda x: judge(x, AuxVerb, ('う','よう','まい','そうだ11','そうだ2','ようだ1','らしい1','ます1','です2','ん'), '終止形'),
        lambda x: judge2(x, ['名詞', '助詞'], True)),
        # ます1（ませ、ませ）
        (lambda x: judge(x, Verb, True, '連用形'),
        lambda x: judge(x, AuxVerb, ['せる', 'させる', 'れる', 'られる', 'たがる1'], '連用形')),
        # ます2（ましょ、まし）
        (lambda x: judge(x, Verb, True, '連用形'),
        lambda x: judge(x, AuxVerb, ['せる', 'させる', 'れる', 'られる', 'たがる1'], '連用形')),
        # だ21（動詞・形容詞・助動詞に接続するものは「だろ・で・なら」のみ）
        (lambda x: judge(x, Verb, True, '終止形'),
        lambda x: judge(x, Adjective, ['形容詞'], '終止形'),
        lambda x: judge(x, AuxVerb, ('ん','う','よう','まい','そうだ11','そうだ2','ようだ1','ます1','です2','だ22'), '終止形')),
        # だ22（だっ、体言と一部の助詞）
        (lambda x: judge(x, Verb, True, '終止形'),
        lambda x: judge2(x, ['名詞', '助詞'], True)),
        # だ23（で、体言と一部の助詞）
        (lambda x: judge(x, Verb, True, '終止形'),
        lambda x: judge2(x, ['名詞', '助詞'], True)),
        # です1（でしょ）
        (lambda x: judge(x, Verb, True, '終止形'),
        lambda x: judge(x, Adjective, ['形容詞'], '終止形'),
        lambda x: judge(x, AuxVerb, ('ん','う','よう','まい','そうだ11','そうだ2','ようだ1','ます1','だ22','です2'), '終止形')),
        # です2（です、形容詞型活用の終止形にもつきうる）
        # 「そうで+です」、「ようで+です」は重なった「で」を消す
        (lambda x: judge(x, AuxVerb, ['そうだ12','ようだ2'], '連用形'),
        lambda x: judge(x, Adjective, ['形容動詞'], '語幹'),
        lambda x: judge(x, AuxVerb, ['ない1','たい1','らしい1'], '終止形'),
        lambda x: judge2(x, ['名詞', '助詞'], True))
    ]

    auxverb_table = {
        'せる': ('使役',['せ','せ','せる','せる','せれ',('せろ','せよ')]),
        'させる': ('使役',['させ','させ','させる','させる','させれ',('させろ','させよ')]),
        'れる': ('受け身・可能・自発・尊敬',['れ','れ','れる','れる','れれ',('れろ','れよ')]),
        'られる': ('受け身・可能・自発・尊敬',['られ','られ','られる','られる','られれ',('られろ','られよ')]),
        'ない1': ('打ち消し',['なかろ','なかっ','ない','ない','なけれ',None]),
        'ない2': ('打ち消し',[None,'なく',None,None,None,None]),
        'ず': ('打ち消し',[None,'ず',None,None,None,None]),  # for 動詞と助動詞
        'ん': ('打ち消し',[None,None,'ん',None,None,None]),  # for 助動詞「ます」
        'う': ('推量・意志',[None,None,'う','う',None,None]),
        'よう': ('推量・意志',[None,None,'よう','よう',None,None]),
        'まい': ('打ち消しの推量・意志',[None,None,'まい','まい',None,None]),
        'たい1': ('希望',['たかろ','たかっ','たい','たい','たけれ',None]),
        'たい2': ('希望',[None,'たく',None,None,None,None]),
        'たがる1': ('希望',['たがら','たがり','たがる','たがる','たがれ',None]),
        'たがる2': ('希望',[None,'たがっ',None,None,None,None]),
        'た': ('過去・完了・存続',['たろ',None,'た','た','たら',None]),
        'だ1': ('過去・完了・存続',['だろ',None,'だ','だ','だら',None]),
        'そうだ11': ('様態',['そうだろ','そうだっ','そうだ','そうな','そうなら',None]),
        'そうだ12': ('様態',[None,'そうで',None,None,None,None]),
        'そうだ13': ('様態',[None,'そうに', None, None, None, None]),
        'そうだ2': ('伝聞',[None, 'そうで', 'そうだ', None, None, None]),
        'ようだ1': ('たとえ・推定・例示',['ようだろ','ようだっ','ようだ','ような','ようなら',None]),
        'ようだ2': ('たとえ・推定・例示',[None,'ようで',None,None,None,None]),
        'ようだ3': ('たとえ・推定・例示',[None,'ように',None,None,None,None]),
        'らしい1': ('推定',[None,'らしかっ','らしい','らしい','らしけれ',None]),
        'らしい2': ('推定',[None,'らしく',None,None,None,None]),
        'ます1': ('丁寧',['ませ','まし','ます','ます','ますれ','ませ']),
        'ます2': ('丁寧',['ましょ',None,None,None,None,'まし']),
        'だ21': ('断定',['だろ','で',None,None,'なら',None]),
        'だ22': ('断定',['だろ','だっ','だ',None,'なら',None]),
        'だ23': ('断定',[None,'で',None,None,None,None]),
        'です1': ('丁寧な断定',['でしょ',None,None,None,None,None]),
        'です2': ('丁寧な断定',['でしょ','でし','です',None,None,None])
    }

    avs = []

    for i,k in enumerate(auxverb_table):
        mean,lst = auxverb_table[k]
        if not len(lst) == 6:raise Exception('ERROR')
        for j,w in enumerate(lst):
            if isinstance(w, str):
                avs.append(AuxVerb(w, Katsuyo(j), k, mean, connection[i]))
            elif isinstance(w, tuple):
                for e in w:
                    avs.append(AuxVerb(e, Katsuyo(j), k, mean, connection[i]))
            elif isinstance(w, type(None)):
                pass
            else:
                raise Exception(f'Unexpected Error')
    return avs


def make_verbs():
    sample_verbs = [
        ('五段', ['(話さ/話そ)', '話し', '話す', '話す', '話せ', '話そ']),
        ('サ変', ['為', '為', '為る', '為る', '為れ', '為ろ']),
        ('カ変', ['来', '来', '来る', '来る', '来れ', '来い']),
        ('一段', ['起き', '起き', '起きる', '起きる', '起きれ', '起き(ろ/よ)'])
    ]

    keys1 = ['V5', 'VSA', 'VKA', 'V1']
    keys2 = ['MIZEN', 'RENYO', 'SYUSHI', 'RENTAI', 'KATEI', 'MEIREI']
    keys = [k1+k2 for k1 in keys1 for k2 in keys2]

    verbs = []
    for b, vs in sample_verbs:
        for i, w in enumerate(vs):
            verbs.append(Verb(w, Katsuyo(i), b))
    return verbs,keys


def make_adjs():
    sample_adjs = [
        ('形容詞', ['赤かろ', '赤(かっ/く)', '赤い', '赤い', '赤けれ', '', '赤']),
        ('形容動詞', ['きれいだろ', 'きれい(だっ/で/に)', 'きれいだ', 'きれいな', 'きれいなら', '', 'きれい']),
    ]

    keys1 = ['ADJ', 'ADJV']
    keys2 = ['MIZEN', 'RENYO', 'SYUSHI', 'RENTAI', 'KATEI', 'GOKAN']
    keys = [k1+k2 for k1 in keys1 for k2 in keys2]

    adjs = []
    for b, vs in sample_adjs:
        for i, w in enumerate(vs):
            if w == '':continue
            adjs.append(Adjective(w, Katsuyo(i), b))
    return adjs,keys


def make_imtws():
    imtws = []
    keys = ['NOUN','ADNM','POSTPNO','POSTP']
    imtws.append(ImmutableWord('夢', '名詞'))
    imtws.append(ImmutableWord('その', '連体詞'))
    imtws.append(ImmutableWord('の', '助詞'))
    imtws.append(ImmutableWord('から', '助詞'))
    return imtws,keys


def begins_setter(d, *tpls):
    for tpl in tpls:
        for i,k in enumerate(tpl[1]):
            d[k] = tpl[0][i]


def to_str(*args):
    s = ''
    for a in args:
        s += str(a)
    return s


def not_dup(*avs):
    # 「そうだ」、「ようだ」、「らしい」が重複しているものを除外
    targets = ['様態', '伝聞', 'たとえ・推定・例示', '推定']
    lst = list(map(lambda x: x.mean, avs))
    for t in targets:
        if lst.count(t) > 1:
            return False
    return True


avs = make_avs()
begins = {}
begins_setter(begins, make_verbs(), make_adjs(), make_imtws())


# FutureWork: 関数化する
results = {}
for k,v in begins.items():
  output = []
  for av1 in avs:
    if av1.connect(v):
      s = to_str(av1)
      if not s in output:output.append(s)
      for av2 in avs:
        if av2.connect(av1):
          s = to_str(av1, av2)
          if not s in output:output.append(s)
          for av3 in avs:
            if av3.connect(av2):
              s = to_str(av1, av2, av3)
              if not s in output and not_dup(av1, av2, av3):
                output.append(s)
              for av4 in avs:
                if av4.connect(av3):
                  s = to_str(av1, av2, av3, av4)
                  if not s in output and not_dup(av1, av2, av3, av4):
                    output.append(s)
                  for av5 in avs:
                    if av5.connect(av4):
                      s = to_str(av1, av2, av3, av4, av5)
                      if not s in output and not_dup(av1, av2, av3, av4, av5):
                        output.append(s)
#   output.sort(key=len, reverse=True)
  results[k] = output

# pp.pprint(results)

def generate(all_dic):
    summury = {
        'ADJV': [],
        'ADJ': [],
        'VERB': []
    }
    for name in all_dic:
        path = f'dic/Auxverb/{name}.txt'
        if len(all_dic[name]) < 1:continue
        with open(path, mode='w', encoding='utf_8') as f:
            for l in all_dic[name]:
                f.write(l + '\n')
                if name.startswith('ADJV') and not l in summury['ADJV']:
                    summury['ADJV'].append(l)
                elif name.startswith('ADJ') and not l in summury['ADJ']:
                    summury['ADJ'].append(l)
                elif name.startswith('V') and not l in summury['VERB']:
                    summury['VERB'].append(l)
    for k,v in summury.items():
        with open(f'dic/Auxverb/{k}.txt', mode='w', encoding='utf_8') as f:
            for p in v:
                f.write(p + '\n')

generate(results)
