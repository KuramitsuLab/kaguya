import sys
import json
import time
import re
from pathlib import Path
from bs4 import BeautifulSoup
import requests
import MeCab
from pegpy import *
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import rcParams
rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = ['Hiragino Maru Gothic Pro', 'Yu Gothic', 'Meirio', 'Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP']
from tester import txt2array


ROOT = Path(__file__).resolve().parent


class MecabToken():
  def __init__(self, line):
    (self.word, detail) = line.split('\t')
    details = detail.split(',')
    details = list(map(lambda d: '*' if d == '' else d, details))
    details += ['*'] * (9-len(details))
    (
      self.品詞,
      self.品詞細分1,
      self.品詞細分2,
      self.品詞細分3,
      self.活用型,
      self.活用形,
      self.原形,
      self.読み,
      self.発音
    ) = details[0:9]

  def __str__(self):
    return self.word

  def __repr__(self):
    return f'{self.word}\t{self.品詞},{self.品詞細分1},{self.品詞細分2},{self.品詞細分3},{self.活用型},{self.活用形},{self.原形},{self.読み},{self.発音}'

  def get_key_list(self):
    return [self.品詞, self.品詞細分1, self.品詞細分2, self.品詞細分3, self.活用型, self.活用形, self.原形, self.読み, self.発音]

  def is_noun(self):
    return self.品詞 in ['名詞', '代名詞', '記号', '接頭詞', '接尾辞', '補助記号']

  def is_suru(self):
    return self.品詞 == '動詞' and self.原形 in ['する', 'ずる']
  
  def is_adjv(self):
    return self.品詞細分1 in ['形状詞', '形容動詞語幹']

  def is_suffix_adjv(self):
    return (self.品詞 == '助動詞' and self.原形 in 'だダ') or (self.品詞 == '助詞' and self.word == 'に')

  def convert2tag(self):
    if self.品詞 in ['名詞', '代名詞', '記号', '補助記号']:
      tag = 'NOUN'
    elif self.品詞 in ['接頭詞']:
      tag = 'NOUN'
    elif self.品詞 in ['形状詞', '形容動詞語幹']:
      tag = 'ADJV'
    elif self.品詞 in ['接尾辞']:
      tag = 'NOUN'
    elif self.品詞 in ['動詞']:
      tag = 'VERB'
    elif self.品詞 in ['形容詞']:
      tag = 'ADJ'
    elif self.品詞 in ['副詞']:
      tag = 'ADV'
    elif self.品詞 in ['形容動詞']:
      tag = 'ADJV'
    elif self.品詞 in ['助詞']:
      tag = 'POSTP'
    elif self.品詞 in ['接続詞']:
      tag = 'CONJ'
    elif self.品詞 in ['感動詞']:
      tag = 'INTJ'
    elif self.品詞 in ['連体詞']:
      tag = 'ADNM'
    elif self.品詞 in ['助動詞']:
      tag = 'AUXVERB'
    else:
      return ('#ERR', f'{self.__repr__()}')
    return (f'#{tag}', f'{self.word}')

  def fromParsedData(pd):
    tokens = []
    for line in pd.split('\n')[:-2]:
      tokens.append(MecabToken(line))
    return tokens

  def tokens2sentence(tokens):
    s = ''
    for t in tokens:
      s += t.word
    return s
  
  def mecab_parser(d):
    pd = Path(d)
    if d != 'ipa' and pd.exists():
      d_path = f' -d {d}'
      print(f'Use {pd.stem}')
    else:
      print('Use ipa')
      d_path = ''
    return MeCab.Tagger(d_path)


# get any statistic logs
class Statistics():
  def __init__(self, _title):
    self.title = _title  # 何の解析か、e.g. python, javadoc
    self.log_path = Path(ROOT/'private'/f'analyze_log_{_title}')
    Path(ROOT/'private'/f'analyze_log_{_title}').mkdir(exist_ok=True)
    self.token_amount_of_sentence = []  # indexが読点の数で、valueは文の構成トークン数を追加していく配列
    self.count_of = {}  # 品詞情報を入れていく、keyがMeCabの単語情報でvalueが{size: keyに当てはまる単語数, data: さらに細分化したデータ}
    # MeCabの品詞情報で"*"にまとめられてしまう「名詞、記号、感動詞」は個別に集計する
    self.set_of_Noun = {}  # 名詞の辞書
    self.set_of_Symbol = {}  # 記号の辞書
    self.set_of_Intj = {}  # 感動詞の辞書
    self.sentence_type = {  # 基本文型の分類
      '名詞文': 0,  # 名詞文, 状態
      '動詞文': 0,  # 動詞文, 操作
      '形容詞文': 0,  # 形容詞文, 状態
      '存在文': 0,  # 存在文, 状態
      'その他': 0  # その他
    }
    self.other = []  # 基本文型がその他の場合はここに文を追加
    self.aux_len = []  # 助動詞の連続回数をappendしていく

  def count(self, d, keys):
    head = keys[0]
    if len(keys) > 1:
      if head in d:
        d[head]['size'] += 1
        self.count(d[head]['data'], keys[1:])
      else:
        d[head] = {'size': 1, 'data': {}}
        self.count(d[head]['data'], keys[1:])
    else:
      if head in d:
        d[head]['size'] += 1
        d[head]['data'] += 1
      else:
        d[head] = {'size': 1, 'data': 1}

  def add_sentence(self, tokens):
    # 文に関しての記録
    comma = len(list(filter(lambda t: t.word == '、', tokens)))
    if len(self.token_amount_of_sentence) > comma:
      self.token_amount_of_sentence[comma].append(len(tokens))
    else:
      for i in range(comma-len(self.token_amount_of_sentence)+1):
        self.token_amount_of_sentence.append([])
      self.token_amount_of_sentence[comma].append(len(tokens))
    key = self.dist_type(tokens)
    self.sentence_type[key] += 1
    if key == 'その他':
      self.other.append(tokens)
    # 文中の単語に関しての記録
    continuing = False
    for t in tokens:
      # 全体の記録への追加
      self.count(self.count_of, t.get_key_list())
      # 特定の品詞辞書の作成
      if t.品詞 == '名詞':
        if t.word in self.set_of_Noun:
          self.set_of_Noun[t.word] += 1
        else:
          self.set_of_Noun[t.word] = 1
      elif t.品詞 == '感動詞':
        if t.word in self.set_of_Intj:
          self.set_of_Intj[t.word] += 1
        else:
          self.set_of_Intj[t.word] = 1
      elif t.品詞 == '記号':
        if t.word in self.set_of_Symbol:
          self.set_of_Symbol[t.word] += 1
        else:
          self.set_of_Symbol[t.word] = 1
      # 助動詞の連続回数の記録
      if t.品詞 == '助動詞' or (t.品詞 == '動詞' and t.原形 in ['れる','られる','せる','させる']):
        if continuing:
          self.aux_len[-1] += 1
        else:
          continuing = True
          self.aux_len.append(1)
      elif continuing:
        continuing = False

  def dist_type(self, tokens):
    if tokens[-1].原形 in ['ある', 'ない']:
      return '存在文'
    elif tokens[-1].品詞 == '動詞':
      return '動詞文'
    elif tokens[-1].品詞 == '形容詞' or (tokens[-1].品詞 == '名詞' and tokens[-1].品詞細分1 in ['ナイ形容詞語幹', '形容動詞語幹']):
      return '形容詞文'
    elif tokens[-1].品詞 == '名詞':
      return '名詞文'
    elif len(tokens) > 1:
      return self.dist_type(tokens[0:-1])
    else:
      return 'その他'

  def write_log(self):
    def make_tsv(d):
      if type(d['data']) == dict:
        l = []
        for k,v in d['data'].items():
          l += list(map(lambda tsv: f'{k}\t{tsv}', make_tsv(v)))
        return l
      else:
        return [f'{d["data"]}']

    # 各MeCabトークンの出現回数の計測結果の書き出し
    with open(self.log_path/'count_of.json', 'w', encoding='utf_8') as f:
      json.dump(self.count_of, f, ensure_ascii=False)
    with open(self.log_path/'count_of.tsv', 'w', encoding='utf_8') as f:
      f.write('\n'.join(make_tsv({'data': self.count_of})))
    # 名詞辞書の作成
    with open(self.log_path/'list_of_noun.csv', 'w', encoding='utf_8') as f:
      f.write('\n'.join(list(map(lambda tpl:f'{tpl[0]},{tpl[1]}', sorted(self.set_of_Noun.items(), key=lambda kv: kv[1], reverse=True)))))
    # 助詞辞書の作成
    with open(self.log_path/'list_of_symbol.csv', 'w', encoding='utf_8') as f:
      f.write('\n'.join(list(map(lambda tpl:f'{tpl[0]},{tpl[1]}', sorted(self.set_of_Symbol.items(), key=lambda kv: kv[1], reverse=True)))))
    # 動詞辞書の作成
    with open(self.log_path/'list_of_intj.csv', 'w', encoding='utf_8') as f:
      f.write('\n'.join(list(map(lambda tpl:f'{tpl[0]},{tpl[1]}', sorted(self.set_of_Intj.items(), key=lambda kv: kv[1], reverse=True)))))
    # 文の統計情報の書き出し
    with open(self.log_path/'token_amount_of_sentence.txt', 'w', encoding='utf_8') as f:
      s = '# 文の統計\n'
      token_amount_rate = []
      comma_rate_label, comma_rate_data = [], []
      plt.figure()
      plt.gca().get_xaxis().set_major_locator(ticker.MaxNLocator(integer=True))
      for i,taos in enumerate(self.token_amount_of_sentence):
        if len(taos) == 0:continue
        x, y = [], []
        for d in set(taos):
          x.append(d)
          y.append(taos.count(d))
        plt.bar(x, y, label=f'comma_{i}')
        token_amount_rate += taos
        comma_rate_label.append(f'読点が{i}個')
        s += f'## 読点の数が{i}個の場合\n'
        s += f'+ 文の総数: {len(taos)}\n'
        comma_rate_data.append(len(taos))
        s += f'+ 単語数の最大値: {max(taos)}\n'
        s += f'+ 単語数の最小値: {min(taos)}\n'
        s += f'+ 単語数の平均値: {sum(taos)/len(taos)}\n'
        if len(taos)%2 == 0:
          ci = len(taos)//2
          center = (taos[ci]+taos[ci-1])/2
        else:
          ci = len(taos)//2
          center = taos[ci]
        s += f'+ 単語数の中央値: {center}\n\n'
      plt.legend(loc='best')
      plt.title('1文に含まれる単語数ごとの文の数（読点の数ごとに区別）')
      plt.xlabel('単語数')
      plt.ylabel('文の数')
      plt.savefig(self.log_path/'token_amount_each_comma.png')
      # 単語数の割合（読点は関係なし）
      plt.figure()
      plt.gca().get_xaxis().set_major_locator(ticker.MaxNLocator(integer=True))
      x, y = [], []
      for d in set(token_amount_rate):
        x.append(d)
        y.append(token_amount_rate.count(d))
      plt.bar(x, y)
      plt.title('1文に含まれる単語数ごとの文の数')
      plt.xlabel('単語数')
      plt.ylabel('文の数')
      plt.savefig(self.log_path/'token_amount.png')
      # 読点の数の割合、円グラフ
      plt.figure()
      plt.gca().get_xaxis().set_major_locator(ticker.MaxNLocator(integer=True))
      plt.pie(comma_rate_data, labels=comma_rate_label, counterclock=False, startangle=90)
      plt.tight_layout()
      plt.savefig(self.log_path/'comma_rate.png')
      f.write(s)
    # 文型の分類結果と、その他に分類された文の書き出し
    with open(self.log_path/'sentence_analyze.txt', 'w', encoding='utf_8') as f:
      s = ''
      for k,v in self.sentence_type.items():
        s += f'{k}: {v}文\n'
      s += f'\n{"="*40} その他の文 {"="*40}\n\n'
      for tokens in self.other:
        s += f'{MecabToken.tokens2sentence(tokens)}\n'
      f.write(s)
    # 品詞（名詞、動詞など）の出現割合
    plt.figure()
    label = []
    data = []
    for k,v in self.count_of.items():
      label.append(k)
      data.append(v['size'])
    plt.pie(data, labels=label, counterclock=False, startangle=90, autopct='%1.1f%%')
    plt.title('品詞の出現割合（単語数の割合）')
    plt.tight_layout()
    plt.savefig(self.log_path/'hinshi_rate.png')
    # 助動詞の連続回数の統計
    plt.figure()
    label = []
    data = []
    for l in set(self.aux_len):
      label.append(f'{l}回')
      data.append(self.aux_len.count(l))
    plt.pie(data, labels=label, counterclock=False, startangle=90, autopct='%1.1f%%')
    plt.title('助動詞の連続回数の割合')
    plt.tight_layout()
    plt.savefig(self.log_path/'aux_len_rate.png')


# parse test/result/*.txt with ast.tpeg
def parse_result(file_path, write_log=False):
  def have_err(tree):
    if tree.tag == 'Tag' and str(tree) == 'err':
      return True
    if len(tree.subs()) > 0:
      for _, child in tree.subs():
        if have_err(child): return True
    return False

  fp = Path(file_path)
  options = parse_options(['-g', 'ast.tpeg'])
  peg = load_grammar(options)
  parser = generator(options)(peg, **options)

  with open(file_path, 'r', encoding='utf_8') as f:
    lines = f.read().split('\n')
    err = 0
    err_list = []
    AMOUNT = len(lines) // 3
    for i in range(AMOUNT):
      print(f'\rNow Processing: {i}/{AMOUNT}', end='')
      is_success = lines.pop(0).split(',')[1]
      input_text = lines.pop(0)
      tree_text = lines.pop(0)
      if is_success == 'OK':
        tree = parser(tree_text)
        if have_err(tree):
          err += 1
          err_list.append(input_text)
          err_list.append(tree_text)
  print(f'\n#err rate: {err}/{AMOUNT} => {round(100*err/AMOUNT, 3)}[%]')
  if write_log:
    with open(f'private/err_list_of_{fp.stem}.txt', 'w', encoding='utf_8') as f:
      f.write('\n'.join(err_list))


# generate err case sentence file from `test/result/*.txt`
def extract_err_sentence(file_path):
  fp = Path(file_path)
  with open(file_path, 'r', encoding='utf_8') as f:
    lines = f.read().split('\n')
    err_list = []
    AMOUNT = len(lines) // 3
    for i in range(AMOUNT):
      print(f'\rNow Processing: {i}/{AMOUNT}', end='')
      is_success = lines.pop(0).split(',')[1]
      input_text = lines.pop(0)
      tree_text = lines.pop(0)
      if is_success == 'NG':
        err_list.append(input_text)
  with open(f'test/err_cases_{fp.stem}.txt', 'w', encoding='utf_8') as f:
    f.write('\n'.join(err_list))


# MeCab Tester
def mecab(d='ipa'):
  m = MecabToken.mecab_parser(d)
  while True:
    try:
      s = input('>> ')
      res = MecabToken.fromParsedData(m.parse(s))
      for w in res:
        print(repr(w))
    except KeyboardInterrupt:
      print()
      break
    except Exception as e:
      print(e)


# generate Noun_~.txt from sentence text
def gen_noun(fp, d='ipa'):
  m = MecabToken.mecab_parser(d)
  target = Path(fp)
  nouns = set([])
  sentences = txt2array(target)
  TOTAL = len(sentences)
  for i,s in enumerate(sentences):
    print(f'\r{i+1}/{TOTAL}', end='')
    res = MecabToken.fromParsedData(m.parse(s))
    for t in res:
      if t.is_noun():
        nouns.add(str(t))
  with open(f'dic/Noun_{target.stem}.txt', 'w', encoding='utf_8') as f:
    f.write('\n'.join(list(nouns)))


# get size of dictionary (exclude not used dict)
def culc_dict():
  dic_cj3_fix = {
    'cjdic/CONJ.txt': False,
    'cjdic/ADVERB.txt': False,
    'cjdic/ADVERB_NOUN.txt': False,
    'cjdic/UNIT.txt': True,
    'cjdic/NONUNIT.txt': False,
    'cjdic/ADNOUN.txt': False,
    'cjdic/XVERB.txt': True,
    'cjdic/XNOUN.txt': True,
    'cjdic/NOUN.txt': True,
    'cjdic/NOUNADJ.txt': True,
    'dic/Verb/VERB5KA.txt': False,
    'dic/Verb/VERB5SA.txt': False,
    'dic/Verb/VERB5TA.txt': False,
    'dic/Verb/VERB5NA.txt': False,
    'dic/Verb/VERB5MA.txt': False,
    'dic/Verb/VERB5RA.txt': False,
    'dic/Verb/VERB5WA.txt': False,
    'dic/Verb/VERB5GA.txt': False,
    'dic/Verb/VERB5BA.txt': False,
    'dic/Verb/VERB1.txt': False,
    'dic/ADJ.txt': False,
  }
  dic_gk1 = {
    'dic/TestNoun.txt': True,
    'dic/Verb/VERB5KA.txt': False,
    'dic/Verb/VERB5SA.txt': False,
    'dic/Verb/VERB5TA.txt': False,
    'dic/Verb/VERB5NA.txt': False,
    'dic/Verb/VERB5MA.txt': False,
    'dic/Verb/VERB5RA.txt': False,
    'dic/Verb/VERB5WA.txt': False,
    'dic/Verb/VERB5GA.txt': False,
    'dic/Verb/VERB5BA.txt': False,
    'dic/Verb/VERB1.txt': False,
    'dic/Verb/KAHEN.txt': False,
    'dic/Verb/SAHEN_SURU.txt': False,
    'dic/Verb/SAHEN_ZURU.txt': False,
    'dic/ADJ.txt': False,
    'dic/ADJV.txt': False,
    'dic/POSTP.txt': False,
    'dic/ADNM.txt': False,
    'dic/ADV.txt': False,
    'dic/CONJ.txt': False,
    'dic/INTJ.txt': False,
  }

  def get_size_amoun(l):
    import os.path as op
    size = [0, 0]  # Noun, All
    token = [0, 0]  # Noun, All
    for (_p, is_noun) in l.items():
      p = Path(_p)
      _size = op.getsize(p)
      with open(p, 'r', encoding='utf_8') as f:
        _token = len(f.read().split('\n'))
      if is_noun:
        size[1] += _size
        token[1] += _token
      size[0] += _size
      token[0] += _token
    print(f'<Only Noun> Tokens: {token[1]}, Size: {size[1]//1024} [KB]')
    print(f'<All  Dict> Tokens: {token[0]}, Size: {size[0]//1024} [KB]')
  print('@@ dict of gk1')
  get_size_amoun(dic_gk1)
  print('@@ dict of cj3_fix')
  get_size_amoun(dic_cj3_fix)


# list_of_noun.csv -> rate of each noun group
def noun_check(target_csv, min_amount=0, with_plt=False):
  result = {
    '英数字記号のみ': [],
    'ひらがなのみ': [],
    'カタカナのみ': [],
    '漢字のみ': [],
    'ひらがな以外の混合': [],
    'ひらがなを含む混合': [],
    'その他': []
  }
  csv_path = Path(target_csv)
  with open(csv_path, 'r', encoding='utf_8') as csv:
    total = 0
    each_amount = []
    label = []
    for line in csv.read().split('\n'):
      noun = line.split(',')
      if len(noun) > 2:
        print(f'Invalid Noun: {noun}')
      else:
        n = noun[0]
        amount = int(noun[1])
        if amount < int(min_amount):
          break
        total += 1
        each_amount.append(amount)
        label.append(n)
        if   re.fullmatch(r'[A-Za-z0-9.(){}, +\-*/%\\]+', n):
          result['英数字記号のみ'].append(n)
        elif re.fullmatch(r'[ぁ-ん]+', n):
          result['ひらがなのみ'].append(n)
        elif re.fullmatch(r'[ァ-ヶー・]+', n):
          result['カタカナのみ'].append(n)
        elif re.fullmatch(r'[㐀-䶵一-龠々〇〻ーご]+', n):
          result['漢字のみ'].append(n)
        elif not re.search(r'[ぁ-ん]', n):
          result['ひらがな以外の混合'].append(n)
        elif re.search(r'[ぁ-ん]', n):
          result['ひらがなを含む混合'].append(n)
        else:
          result['その他'].append(n)

  for k,v in result.items():
    print(f'{k} : {len(v)}単語 : {round(100*len(v)/total, 3)}[%]')

  with_plt = bool(with_plt)
  if with_plt:
    plt.figure(figsize=(15,total//5), dpi=80)
    plt.barh(list(range(total)), list(reversed(each_amount)), tick_label=list(reversed(label)), align='center')
    plt.grid(which='both', axis='x', color='blue', alpha=0.8, linestyle='--')
    plt.gca().xaxis.set_minor_locator(ticker.MultipleLocator(500))
    plt.savefig(csv_path.parent/'noun_distribution.png', bbox_inches='tight', pad_inches=1)


# Sentence Text -> Statistic -> Log
def analyze(target, d='ipa'):
  f = Path(target)
  m = MecabToken.mecab_parser(d)
  st = Statistics(f.stem)
  sentences = txt2array(ROOT/'test'/f.name)
  TOTAL = len(sentences)
  START = time.time()
  for i,s in enumerate(sentences):
    print(f'\r{i+1}/{TOTAL}', end='')
    res = MecabToken.fromParsedData(m.parse(s))
    st.add_sentence(res)
  print('\nLogging Now')
  st.write_log()
  print(f'Execution Time: {time.time() - START}[sec]')


# Used in gen_sentence and get_html
def listen_choice():
  def remove_dom(selector):
    def inner(t):
      for code in t.select(selector):
        code.decompose()
    return inner

  setting = [
    (
      'javadoc',
      ['li.blockList div.block'],
      remove_dom('pre'),
      lambda x: x
    ),
    (
      'nhk_news',
      ['div#news_textbody', 'div#news_textmore'],
      lambda x: x,
      lambda s: re.sub(r'<br>|<br />', '', s)
    )
  ]
  for s in setting:
    choice = input(f'Use setting of {s[0]}? (Yy/Nn): ')
    if choice in 'Yy':
      return s
  print('Not selected setting')
  sys.exit()


# HTML -> Sentence Text
def gen_sentence():
  def extract_text(html, selectors, for_dom=lambda x: x, for_inner=lambda x: x):
    ss, err = [], []
    soup = BeautifulSoup(html, 'html.parser')
    txt_list = []
    for s in selectors:
      txt_list += soup.select(s)
    for i,t in enumerate(txt_list):
      for_dom(t)
      for s in for_inner(t.get_text()).split('\u3002'):
        s = s.strip()
        if not re.fullmatch(r'[\u0020\u3002\u000a-\u000d]*', s):
          if ('\n' in s):
            err.append(s)
          else:
            ss.append(f'{s}\u3002')
    return ss, err

  (title, slct, f_dom, f_inner) = listen_choice()
  all_sentence = []
  all_err = []
  files = list((ROOT/f'{title}_html').glob('*.html'))
  TOTAL = len(files)
  (ROOT/f'{title}_text').mkdir(exist_ok=True)
  for i, fname in enumerate(files):
    print(f'\rProcessing {i+1}/{TOTAL}', end='')
    with open(fname, 'r', encoding='utf_8') as f_read:
      with open(ROOT/f'{title}_text'/f'{fname.stem}.txt', 'w', encoding='utf_8') as f_write:
        ss, err = extract_text(f_read, slct, f_dom, f_inner)
        f_write.write('\n'.join(ss))
        all_sentence += ss
        all_err += err
  print()
  header = '# created by scripts\n'
  with open(ROOT/'test'/f'{title}.txt', 'w', encoding='utf_8') as f:
    f.write(header + '\n'.join(sorted(all_sentence, key=len, reverse=True)))
  if len(all_err) > 0:
    with open(ROOT/'test'/f'{title}_invalids.txt', 'w', encoding='utf_8') as f:
      f.write(header + f'\n{"="*60}\n'.join(sorted(all_err, key=len, reverse=True)))
  print(f'valid: {len(all_sentence)}, invalid: {len(all_err)}')


# URL List (json) -> HTML
def get_html():
  (title, *_) = listen_choice()
  err_log = []
  with open(ROOT/f'{title}.json', 'r', encoding='utf_8') as f:
    hrefs = json.load(f)
  TOTAL = len(hrefs)
  (ROOT/f'{title}_html').mkdir(exist_ok=True)
  for i, (href, fname) in enumerate(hrefs):
    print(f'\rProcessing {i+1}/{TOTAL}: Request', end='')
    try:
      with open(ROOT/f'{title}_html'/f'{fname}.html', 'w', encoding='utf_8') as f:
        res = requests.get(href)
        res.encoding = res.apparent_encoding
        f.write(res.text)
    except Exception as e:
      err_log.append(repr(e))
    print(f'\rProcessing {i+1}/{TOTAL} :Interval', end='')
    time.sleep(1.0)
  print('')
  with open(ROOT/'err_log.txt', 'w', encoding='utf_8') as f:
    f.write('\n'.join(err_log))


def main(args):
  fname = args[1]
  if len(args) < 3:
    globals()[fname]()
  else:
    globals()[fname](*args[2:])


if __name__ == "__main__":
    main(sys.argv)


