import re
import sys
from pathlib import Path

class IPA_Word():
  def __init__(self, 単語, 品詞, 活用の種類):
    self.w = 単語
    self.h = 品詞
    self.k = 活用の種類

  def __str__(self):
    return self.w

  def __repr__(self):
    return f'{self.w} {self.h} {self.k}'
  
  def parse(s):
    spot_h = s.find('品詞')
    spot_w = s.find('見出し語')
    h = s[s.find('(', spot_h)+1: s.find(')', spot_h)].replace(' ','-')
    w = s[s.find('(', spot_w)+1: s.find(')', spot_w)].split(' ')[0]
    k = ''
    if '活用型' in s:
      spot_k = s.find('活用型')
      k = s[s.find(' ', spot_k)+1: s.find(')', spot_k)]
    return IPA_Word(w, h, k)
  
  def is_hira_only(self):
    return bool(re.fullmatch(r'[ぁ-ん]+', self.w))

  def has_hira(self):
    return bool(re.search(r'[ぁ-ん]', self.w))


class IPA_Dic():
  def __init__(self, _ipa_path):
    self.ipa_path = Path(_ipa_path)
    self.ipa_classify = {
      'Adj.dic': ['ADJ'],  # 形容詞
      'Adnominal.dic': ['ADNM'],  # 連体詞
      'Adverb.dic': ['ADV'],  # 副詞
      'Auxil.dic': ['UNKNOWN'],  # 助動詞
      'Conjunction.dic': ['CONJ'],  # 接続詞
      'Filler.dic': ['UNKNOWN'],  # フィラー
      'Interjection.dic': ['INTJ'],  # 感動詞
      'Noun.adjv.dic': ['NOUN', 'ADJV'],  # 形容動詞語幹
      'Noun.adverbal.dic': ['NOUN', 'ADV'],  # 副詞可能
      'Noun.demonst.dic': ['NOUN'],  # 名詞代名詞
      'Noun.dic': ['NOUN'],  # 名詞
      'Noun.nai.dic': ['NOUN', 'ADJ_Nai'],  # 名詞 ナイ形容詞語幹
      'Noun.name.dic': ['NOUN'],  # 固有名詞 人名
      'Noun.number.dic': ['NOUN'],  # 名詞 数
      'Noun.org.dic': ['NOUN'],  # 固有名詞 組織
      'Noun.others.dic': ['NOUN'],  # 名詞 非自立
      'Noun.place.dic': ['NOUN'],  # 固有名詞 地域
      'Noun.proper.dic': ['NOUN'],  # 固有名詞
      'Noun.verbal.dic': ['NOUN'],  # 名詞 サ変接続
      'Onebyte.dic': ['NOUN'],  # 記号や数字
      'Others.dic': ['NOUN'],  # その他
      'Postp-col.dic': ['POSTP'],  # 格助詞
      'Postp.dic': ['POSTP'],  # 助詞
      'Prefix.dic': ['NOUN'],  # 接頭詞
      'Suffix.dic': ['NOUN'],  # 名詞 接尾
      'Symbol.dic': ['NOUN'],  # 記号
      'Verb.dic': ['VERB'],  # 動詞
    }
    self.new_dic = {
      'ADJ': set([]),
      'ADJV': set([]),
      'NOUN': set([]),
      'ADNM': set([]),
      'ADV': set([]),
      'CONJ': set([]),
      'INTJ': set([]),
      'POSTP': set([]),
      'VERB5KA': set([]),
      'VERB5SA': set([]),
      'VERB5TA': set([]),
      'VERB5NA': set([]),
      'VERB5MA': set([]),
      'VERB5RA': set([]),
      'VERB5WA': set([]),
      'VERB5GA': set([]),
      'VERB5BA': set([]),
      'VERB1': set([]),
      'SAHEN_SURU': set([]),
      'SAHEN_ZURU': set([]),
      'KAHEN': set([]),
      'UNKNOWN': set([])
    }

  def load_dic(self):
    for d in self.ipa_classify:
      with open(self.ipa_path/d, 'r', encoding='euc_jp') as f:
        for s in f.readlines():
          iw = IPA_Word.parse(s)
          self.convert(d, iw)

  def convert(self, dic_name, ipa_word):
    for new_dic_name in self.ipa_classify[dic_name]:
      if new_dic_name == 'VERB':
        try:
          new_dic_name, preped = self.verb_classify(ipa_word)
          self.new_dic[new_dic_name].add(preped)
        except Exception as e:
          print(e)
      elif new_dic_name == 'ADJ':
        self.new_dic[new_dic_name].add(ipa_word.w[:-1])
      elif new_dic_name == 'ADJ_Nai':
        self.new_dic['ADJ'].add(ipa_word.w+'な')
      elif new_dic_name == 'POSTP':
        postp = ipa_word.w
        self.new_dic[new_dic_name].add(postp)
      elif new_dic_name == 'UNKNOWN':
        self.new_dic[new_dic_name].add(repr(ipa_word))
      else:
        self.new_dic[new_dic_name].add(ipa_word.w)
  
  def generate(self, dic_dir='dic'):
    dd = Path(dic_dir)
    (dd/'Verb').mkdir(parents=True, exist_ok=True)
    for nd in self.new_dic:
      if nd == 'UNKNOWN':
        with open(dd/f'{nd}.txt', 'w', encoding='utf_8') as f:
          f.write('\n'.join(list(self.new_dic[nd])))
      elif nd.startswith('VERB') or nd in ['SAHEN_SURU','SAHEN_ZURU','KAHEN']:
        with open(dd/'Verb'/f'{nd}.txt', 'w', encoding='utf_8') as f:
          f.write('\n'.join(list(self.new_dic[nd])))
      else:
        with open(dd/f'{nd}.txt', 'w', encoding='utf_8') as f:
          f.write('\n'.join(list(self.new_dic[nd])))

  # 活用型の名前の変換
  def verb_classify(self, ipa_word):
    # 文法内に定義している動詞と1文字動詞は除外している
    if ipa_word.w in ['行く', 'くる', '来る', 'する'] or len(ipa_word.w) < 2:
      raise Exception(f'Skip Verb: {repr(ipa_word)}')
    if   '五段・カ行' in ipa_word.k:
      return 'VERB5KA', ipa_word.w[:-1]
    elif '五段・サ行' in ipa_word.k:
      return 'VERB5SA', ipa_word.w[:-1]
    elif '五段・タ行' in ipa_word.k:
      return 'VERB5TA', ipa_word.w[:-1]
    elif '五段・ナ行' in ipa_word.k:
      return 'VERB5NA', ipa_word.w[:-1]
    elif '五段・マ行' in ipa_word.k:
      return 'VERB5MA', ipa_word.w[:-1]
    elif '五段・ラ行' in ipa_word.k:
      return 'VERB5RA', ipa_word.w[:-1]
    elif '五段・ワ行' in ipa_word.k:
      return 'VERB5WA', ipa_word.w[:-1]
    elif '五段・ガ行' in ipa_word.k:
      return 'VERB5GA', ipa_word.w[:-1]
    elif '五段・バ行' in ipa_word.k:
      return 'VERB5BA', ipa_word.w[:-1]
    elif '一段' in ipa_word.k:
      return 'VERB1', ipa_word.w[:-1]
    elif 'サ変' in ipa_word.k:
      if 'スル' in ipa_word.k:
        return 'SAHEN_SURU', ipa_word.w[:-2]
      else:
        return 'SAHEN_ZURU', ipa_word.w[:-2]
    elif 'カ変' in ipa_word.k:
      return 'KAHEN', ipa_word.w[:-2]
    else:
      return 'UNKNOWN', repr(ipa_word)


if __name__ == "__main__":
  # arg is IPA-dic directory
  ipa = IPA_Dic(sys.argv[1])
  ipa.load_dic()
  ipa.generate()
