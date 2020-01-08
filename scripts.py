import sys
import json
import time
import re
from pprint import pprint as pp
from pathlib import Path
from bs4 import BeautifulSoup
import requests
import MeCab
from pegpy.main import *
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import rcParams
rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = ['Hiragino Maru Gothic Pro', 'Yu Gothic', 'Meirio', 'Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP']


FP = Path(__file__).resolve().parent
NEOLOGD_PATH = Path('/Users/xps/Documents/mecab-dic/neolog/mecab-ipadic-neologd')  # winPC
# NEOLOGD_PATH = Path('/usr/local/lib/mecab/dic/mecab-ipadic-neologd')  # macbook
UNIDIC_PATH = Path('/Users/xps/Documents/mecab-dic/unidic-cwj-2.3.0')
LOG_PATH = FP/'analyze_log'
LOG_PATH.mkdir(exist_ok=True)

# DIC_PATH = NEOLOGD_PATH
DIC_PATH = UNIDIC_PATH


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


class Statistics():
  def __init__(self):
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
    with open(LOG_PATH/'count_of.json', 'w', encoding='utf_8') as f:
      json.dump(self.count_of, f, ensure_ascii=False)
    with open(LOG_PATH/'count_of.tsv', 'w', encoding='utf_8') as f:
      f.write('\n'.join(make_tsv({'data': self.count_of})))
    # 名詞辞書の作成
    with open(LOG_PATH/'JavadocNoun.txt', 'w', encoding='utf_8') as f:
      f.write('\n'.join(list(map(lambda tpl:f'{tpl[0]},{tpl[1]}', sorted(self.set_of_Noun.items(), key=lambda kv: kv[1], reverse=True)))))
    # 助詞辞書の作成
    with open(LOG_PATH/'JavadocSymbol.txt', 'w', encoding='utf_8') as f:
      f.write('\n'.join(list(map(lambda tpl:f'{tpl[0]},{tpl[1]}', sorted(self.set_of_Symbol.items(), key=lambda kv: kv[1], reverse=True)))))
    # 動詞辞書の作成
    with open(LOG_PATH/'JavadocIntj.txt', 'w', encoding='utf_8') as f:
      f.write('\n'.join(list(map(lambda tpl:f'{tpl[0]},{tpl[1]}', sorted(self.set_of_Intj.items(), key=lambda kv: kv[1], reverse=True)))))
    # 文の統計情報の書き出し
    with open(LOG_PATH/'token_amount_of_sentence.txt', 'w', encoding='utf_8') as f:
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
      plt.savefig(LOG_PATH/'token_amount_each_comma.png')
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
      plt.savefig(LOG_PATH/'token_amount.png')
      # 読点の数の割合、円グラフ
      plt.figure()
      plt.gca().get_xaxis().set_major_locator(ticker.MaxNLocator(integer=True))
      plt.pie(comma_rate_data, labels=comma_rate_label, counterclock=False, startangle=90)
      plt.tight_layout()
      plt.savefig(LOG_PATH/'comma_rate.png')
      f.write(s)
    # 文型の分類結果と、その他に分類された文の書き出し
    with open(LOG_PATH/'sentence_analyze.txt', 'w', encoding='utf_8') as f:
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
    plt.savefig(LOG_PATH/'hinshi_rate.png')
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
    plt.savefig(LOG_PATH/'aux_len_rate.png')


def parse_ast(file_path):
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
    AMOUNT = len(lines) // 3
    for i in range(AMOUNT):
      print(f'\r{i}', end='')
      is_success = lines.pop(0).split(',')[1]
      input_text = lines.pop(0)
      if is_success == 'OK':
        tree = parser(lines.pop(0))
        if have_err(tree): err += 1
      else:
        lines.pop(0)
    print(f'\ncount of err sentence: {err}/{AMOUNT}')



# MeCab Tester
def mecab():
  dict_path = f' -d {DIC_PATH}' if DIC_PATH.exists() else ''
  m = MeCab.Tagger(dict_path)
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


def noun_check():
  result = {
    'Code': 0,
    'ひらがなのみ': 0,
    'カタカナのみ': 0,
    '漢字のみ': 0,
    'ひらがな以外': 0,
    'ひらがな含む': 0,
    'その他': 0
  }
  with open(LOG_PATH/'JavadocNoun.txt', 'r', encoding='utf_8') as f:
    csv = f.read()
  TOTAL = len(csv)
  for line in csv:
    noun = line.split(',')
    if len(noun) > 2:
      print(f'Invalid Noun: {noun}')
    else:
      noun = noun[0]
      if   re.fullmatch(r'[A-Za-z0-9.(){}, +\-*/%\\]+', noun):
        result['Code'] += 1
      elif re.fullmatch(r'[ぁ-ん]+', noun):
        result['ひらがなのみ'] += 1
      elif re.fullmatch(r'[ァ-ヶー・]+', noun):
        result['カタカナのみ'] += 1
      elif re.fullmatch(r'[㐀-䶵一-龠々〇〻ーご]+', noun):
        result['漢字のみ'] += 1
      elif not re.search(r'[ぁ-ん]', noun):
        result['ひらがな以外'] += 1
      elif re.serch(r'[ぁ-ん]', noun):
        result['ひらがな含む'] += 1
      else:
        result['その他'] += 1
  with open(LOG_PATH/'noun_detail.txt', 'w', encoding='utf_8') as f:
    s = ''
    for k,v in result.items():
      s += f'{k}: {v}個: {round(100*v/TOTAL, 3)}%\n'
    f.write(s)


# Sentence Text -> Statistic -> Log
def analyze():
  dict_path = f' -d {DIC_PATH}' if DIC_PATH.exists() else ''
  m = MeCab.Tagger(dict_path)
  st = Statistics()
  with open(FP/'test'/'javadoc.txt', 'r', encoding='utf_8') as f:
    all_sentences = f.read().split('\n')
    sentences = list(set(all_sentences))
  TOTAL = len(sentences)
  START = time.time()
  for i,s in enumerate(sentences):
    # if i > 99:break
    print(f'\r{i+1}/{TOTAL}', end='')
    res = MecabToken.fromParsedData(m.parse(s))
    st.add_sentence(res)
  print('\nLogging Now')
  st.write_log()
  print(f'Execution Time: {time.time() - START}[sec]')


# HTML -> Sentence Text
def gen_sentence():
  def extract_text(html):
    ss = []
    err = []
    soup = BeautifulSoup(html, 'html.parser')
    txt_list = soup.select('li.blockList div.block')
    for i,t in enumerate(txt_list):
      for code in t.select('pre'):
        code.decompose()
      for s in t.get_text().split('\u3002'):
        s = s.strip()
        if not re.fullmatch(r'[\u0020\u3002\u000a-\u000d]*', s):
          if ('\n' in s):
            err.append(s)
          else:
            ss.append(f'{s}\u3002')
    return ss, err

  all_sentence = []
  all_err = []
  files = list((FP/'java_se_html').glob('*.html'))
  TOTAL = len(files)
  (FP/'java_se_text').mkdir(exist_ok=True)
  for i,fname in enumerate(files):
    print(f'\rProcessing {i+1}/{TOTAL}', end='')
    # if i>100:break
    with open(fname, 'r', encoding='utf_8') as f_read:
      with open(FP/'java_se_text'/f'{fname.stem}.txt', 'w', encoding='utf_8') as f_write:
        ss, err = extract_text(f_read)
        f_write.write('\n'.join(ss))
        all_sentence += ss
        all_err += err
  print()
  with open(FP/'test'/'javadoc.txt', 'w', encoding='utf_8') as f:
    f.write('\n'.join(sorted(all_sentence, key=len, reverse=True)))
  with open(FP/'test'/'javadoc_invalids.txt', 'w', encoding='utf_8') as f:
    f.write(f'\n{"="*60}\n'.join(sorted(all_err, key=len, reverse=True)))
  print(f'valid: {len(all_sentence)}, invalid: {len(all_err)}')


# URL List -> HTML
def get_html():
  err_log = []
  with open(FP/'javadoc_api_urls.json', 'r', encoding='utf_8') as f:
    class_list = json.load(f)
  TOTAL = len(class_list)
  (FP/'java_se_html').mkdir(exist_ok=True)
  for i, (href, cname) in enumerate(class_list):
    print(f'\rProcessing {i+1}/{TOTAL}: Request', end='')
    try:
      with open(FP/'java_se_html'/f'{cname}.html', 'w', encoding='utf_8') as f:
        res = requests.get(href)
        res.encoding = res.apparent_encoding
        f.write(res.text)
    except Exception as e:
      err_log.append(repr(e))
    print(f'\rProcessing {i+1}/{TOTAL} :Interval', end='')
    time.sleep(1.0)
  print('')
  with open(FP/'err_log.txt', 'w', encoding='utf_8') as f:
    f.write('\n'.join(err_log))


def main(args):
  fname = args[1]
  if len(args) < 3:
    globals()[fname]()
  else:
    globals()[fname](*args[2:])


if __name__ == "__main__":
    main(sys.argv)


