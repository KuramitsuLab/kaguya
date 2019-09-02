from enum import IntEnum
import pprint as pp


class Katsuyo(IntEnum):
    Mizen = 0
    Renyo = 1
    Syushi = 2
    Rentai = 3
    Katei = 4
    Meirei = 5

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


class Verb():
    __slots__ = ['word', 'katsuyo', 'base']

    def __init__(self, w, k, b):
        self.word = w
        self.katsuyo = k
        self.base = b

    def __str__(self):
        return self.word

    def __repr__(self):
        return f'{self.word}：{self.base}活用の{str(self.katsuyo)}の動詞'


class AuxVerb():
    __slots__ = ['word', 'katsuyo', 'base', 'mean', 'connection']

    def __init__(self, w, k, b, m, c):
        self.word = w
        self.katsuyo = k
        self.base = b
        self.mean = m
        if isinstance(c, tuple):
            self.connection = list(c)
        elif isinstance(c, type(lambda x:x)):
            self.connection = [c]

    def __str__(self):
        return self.word

    def __repr__(self):
        return f'{self.word}：{self.mean}の助動詞「{self.base}」の{str(self.katsuyo)}'

    def connect(self, pre_word):
        connection_check = map(lambda f: f(pre_word), self.connection)
        return (True in connection_check)


def judge(x, v_or_av, base_or_pattern, katsuyo):
    bs = []
    # 動詞または助動詞かどうか
    bs.append(isinstance(x, v_or_av))
    # 接続できる活用（五段、サ変...）または助動詞（ます、される...）かどうか
    if isinstance(base_or_pattern, list):
        bs.append(x.base in base_or_pattern)
    elif isinstance(base_or_pattern, tuple):
        bs.append(not x.base in base_or_pattern)
    # 接続できる活用形かどうか
    bs.append(str(x.katsuyo) == katsuyo)
    # 後ろになにも続かない助動詞かどうか（活用後の単体で指定）
    if isinstance(x, AuxVerb) and str(x) in ['ん','です']:
        bs.append(False)
    return not False in bs

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
     lambda x: judge(x, AuxVerb, ['ない', 'たい', 'た', 'だ1', 'そうだ11', 'ようだ1', 'ます2', 'だ2', 'です1'], '未然形')),
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
     lambda x: judge(x, AuxVerb, ('ない2','ず','たい2','たがる1','そうだ12','そうだ13','そうだ2','ようだ2','ようだ3','らしい2','だ2'), '連用形')),
    # だ1（ガ/ナ/バ/マ行五段の動詞に接続する時のみ）
    lambda x: judge(x, Verb, ['五段'], '連用形'),
    # そうだ11（そうだっ）
    (lambda x: judge(x, Verb, True, '連用形'),
     lambda x: judge(x, AuxVerb, ['せる', 'させる', 'れる', 'られる'], '連用形')),
    # そうだ12（そうで）
    (lambda x: judge(x, Verb, True, '連用形'),
     lambda x: judge(x, AuxVerb, ['せる', 'させる', 'れる', 'られる'], '連用形')),
    # そうだ13（そうに）
    (lambda x: judge(x, Verb, True, '連用形'),
     lambda x: judge(x, AuxVerb, ['せる', 'させる', 'れる', 'られる'], '連用形')),
    # そうだ2
    (lambda x: judge(x, Verb, True, '終止形'),
     lambda x: judge(x, AuxVerb, ('ん','う','よう','まい','そうだ11','そうだ2','ます1','ようだ1'), '終止形')),
    # ようだ1（ようだ）
    (lambda x: judge(x, Verb, True, '連体形'),
     lambda x: judge(x, AuxVerb, ('ん', 'う', 'よう', 'まい', 'ようだ1', 'そうだ11', 'ます1', 'らしい1'), '連体形')),
    # ようだ2（ようで）
    (lambda x: judge(x, Verb, True, '連体形'),
     lambda x: judge(x, AuxVerb, ('ん', 'う', 'よう', 'まい', 'ようだ1', 'そうだ11', 'ます1', 'らしい1'), '連体形')),
    # ようだ3（ように）
    (lambda x: judge(x, Verb, True, '連体形'),
     lambda x: judge(x, AuxVerb, ('ん', 'う', 'よう', 'まい', 'ようだ1', 'そうだ11', 'ます1', 'らしい1'), '連体形')),
    # らしい1（らしかっ）
    (lambda x: judge(x, Verb, True, '終止形'),
     lambda x: judge(x, AuxVerb, ('う','よう','まい','そうだ11','そうだ2','ようだ1','らしい1','ます1'), '終止形')),
    # らしい2（らしく）
    (lambda x: judge(x, Verb, True, '終止形'),
     lambda x: judge(x, AuxVerb, ('う','よう','まい','そうだ11','そうだ2','ようだ1','らしい1','ます1'), '終止形')),
    # ます1（ませ、ませ）
    (lambda x: judge(x, Verb, True, '連用形'),
     lambda x: judge(x, AuxVerb, ['せる', 'させる', 'れる', 'られる', 'たがる1'], '連用形')),
    # ます2（ましょ、まし）
    (lambda x: judge(x, Verb, True, '連用形'),
     lambda x: judge(x, AuxVerb, ['せる', 'させる', 'れる', 'られる', 'たがる1'], '連用形')),
    # だ2（動詞・助動詞に接続するものは「だろ・で・なら」のみ）
    (lambda x: judge(x, Verb, True, '終止形'),
     lambda x: judge(x, AuxVerb, ('ん','う','よう','まい','そうだ11','そうだ2','ようだ1','ます1'), '終止形')),
    # です1（でしょ）
    (lambda x: judge(x, Verb, True, '終止形'),
     lambda x: judge(x, AuxVerb, ('ん','う','よう','まい','そうだ11','そうだ2','ようだ1','ます1'), '終止形')),
    # です2（です）
    (lambda x: judge(x, AuxVerb, ['そうだ12','ようだ2'], '連用形'),
     lambda x: judge(x, AuxVerb, ['ない1','たい1','らしい1'], '終止形'))
]

sub_verb_table = {
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
    'だ2': ('断定',['だろ','で',None,None,'なら',None]),
    'です1': ('丁寧な断定',['でしょ',None,None,None,None,None]),
    'です2': ('丁寧な断定',[None,None,'です','です',None,None])
}

avs = []

for i,k in enumerate(sub_verb_table):
    mean,lst = sub_verb_table[k]
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

# pp.pprint(avs)

sample_verbs = [
    ('五段', ['(話さ/話そ)', '話し', '話す', '話す', '話せ', '話そ']),
    ('サ変', ['為', '為', '為る', '為る', '為れ', '為ろ']),
    ('カ変', ['来', '来', '来る', '来る', '来れ', '来い']),
    ('一段', ['起き', '起き', '起きる', '起きる', '起きれ', '起き(ろ/よ)'])
]

def make_verb(n):
    verb = []
    b,v = sample_verbs[n]
    for i, w in enumerate(v):
        verb.append(Verb(w, Katsuyo(i), b))
    return verb

verb = make_verb(3)

# pp.pprint(verb)


def to_str_old(*args):
    s = '    / \''
    for a in args:
        s += str(a)
    return s+'\''

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


starts = [
    Verb(),
    Verb(),
    Verb(),
    Verb(),
    Adjective(),
    Adjective(),
]

output = []
for av1 in avs:
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

# pp.pprint(output)

output.sort(key=len, reverse=True)

# pp.pprint(output)

def gen_tpeg(lst):
    list_amount = int(len(lst) / 100) + (0 if len(lst) % 100 == 0 else 1)
    tpeg1 = 'AuxVerbs = {\n'
    tpeg2 = ''
    for i in range(list_amount):
        slash = ' ' if i == 0 else '/'
        tpeg1 += f'    {slash} AV{i}\n'
        tpeg2 += f'AV{i} =\n'
        for p in lst[i*100:i*100+100]:
            tpeg2 += f'{p}\n'
        tpeg2 += '\n'
    tpeg1 += '    #AuxVerbs\n}\n\n'
    return tpeg1+tpeg2


# print(gen_tpeg(output))

# pp.pprint(avs)


def gen_tpeg2(lst):
    text = 'AUXVERB =\n'
    for p in lst:
        text += f'{p}\n'
    return text

# print(gen_tpeg2(output))

for p in output:
    print(p)
