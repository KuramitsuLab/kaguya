import sys
import time
import re
import string
from pathlib import Path
import unicodedata
import subprocess
import shutil
import platform
import copy

sys.setrecursionlimit(2**31-1)


# switch pegpy <-> pegtree
IS_PEGPY = False
if IS_PEGPY:
  from pegpy.main import *
else:
  from pegtree.main import *

def get_tag(ast):
  if IS_PEGPY:
    return ast.tag
  else:
    return ast.tag_

def get_inputs(ast):
  if IS_PEGPY:
    return ast.inputs
  else:
    return ast.inputs_

def get_epos(ast):
  if IS_PEGPY:
    return ast.epos
  else:
    return ast.epos_

def is_err(ast):
  if IS_PEGPY:
    return ast.tag == 'err'
  else:
    return ast.isSyntaxError()


# sub functions for test()
def txt2array(path):
  import random
  s = ''
  with open(path, mode='r', encoding='utf_8') as f:
    s = f.read()
  s = re.sub(r'[ ]', '', s)  # スペースの除去は入力文字列にあわせて適宜行う方がよいかも
  return list(filter(lambda x: not x.strip() == '', set(s.split('\n')[1:])))
  # return random.sample(list(filter(lambda x: not x.strip() == '', set(s.split('\n')[1:]))), 100)


def write_result(fpath, results):
  with open(fpath, mode='w', encoding='utf_8') as f:
    s = ''
    print('Now Caching Result')
    for cnt, ast in results:
      OKorNG = 'NG' if is_err(ast) else 'OK'
      if is_err(ast):
        third = f'{get_inputs(ast)[get_epos(ast):]}\n'
      else:
        try:
          third = f'{repr(ast)}\n'
        except Exception as e:
          third = f'Error in repr(ast)\n'
          OKorNG = 'NG'
      s += f'{cnt},{OKorNG}\n'
      s += f'{get_inputs(ast)}\n'
      s += third
    print('Now Writing Result')
    f.write(s)


def print_err(results):
  for cnt, ast in results:
    if is_err(ast):
      print(f'入力: {get_inputs(ast)}')
      print(f'残り: {get_inputs(ast)[get_epos(ast):]}')


DOT = '''\
digraph sample {
  graph [
    charset = "UTF-8",
    label = "$input_text",
    labelloc = t,
    fontname = "MS Gothic",
    fontsize = 18,
    dpi = 300,
  ];

  edge [
    dir = none,
    fontname = "MS Gothic",
    fontcolor = "#252525",
    fontsize = 12,
  ];

  node [
    shape = box,
    style = "rounded,filled",
    color = "#3c3c3c",
    fillcolor = "#f5f5f5",
    fontname = "MS Gothic",
    fontsize = 16,
    fontcolor = "#252525",
  ];

  $node_description

  $edge_description
}'''


def escape(s):
  after = ''
  META_LITERAL = ['\\', '"']
  for c in s:
    if c in META_LITERAL:
      after += f'\\{c}'
    else:
      after += c
  return after


def bottom_check(s):
  if platform.system() == 'Darwin':
    for c in s:
      if unicodedata.east_asian_width(c) in ['W', 'F', 'H']:
        return ', labelloc = "bottom"'
  return ''


def make_dict(t, d, nid):
  d['node'].append(f'n{nid} [label="#{get_tag(t)}"]')
  if len(t.subs()) == 0:
    leaf = str(t)
    d['node'].append(f'n{nid}_0 [label="{escape(leaf)}"{bottom_check(leaf)}]')
    d['edge'].append(f'n{nid} -> n{nid}_0')
  else:
    for i, (fst, snd) in enumerate(t.subs()):
      label = f' [label="{fst}"]' if fst != '' else ''
      d['edge'].append(f'n{nid} -> n{nid}_{i}{label}')
      make_dict(snd, d, f'{nid}_{i}')


def gen_dot(t):
  d = {'node': [], 'edge': []}
  if is_err(t):
    leaf = escape(get_inputs()[get_epos():])
    d['node'].append(f'n0 [label="#Remain"]')
    d['node'].append(f'n0_0 [label="{leaf}"{bottom_check(leaf)}]')
    d['edge'].append(f'n0 -> n0_0')
  else:
    make_dict(t, d, 0)
  context = {
    'input_text': escape(get_inputs()),
    'node_description': ';\n  '.join(d['node']),
    'edge_description': ';\n  '.join(d['edge']),
  }
  return string.Template(DOT).substitute(context)


def gen_graph(ast, path='graph.png'):
  GEN_DOT_PATH = '.temp.dot'
  with open(GEN_DOT_PATH, mode='w', encoding='utf_8') as f:
    f.write(gen_dot(ast))
  cmd = ['dot', '-Tpng', GEN_DOT_PATH, '-o', path]
  res = subprocess.call(cmd)
  if res != 0:
    Path(GEN_DOT_PATH).rename(f'.erred.dot')
  else:
    Path(GEN_DOT_PATH).unlink()


def make_dir(dn):
  try:
    Path(dn).mkdir(parents=True, exist_ok=False)
  except FileExistsError:
    print(f'"{dn}": This directory already exist, can I overwrite it?')
    choice = input('(y/n): ')
    if choice in 'yY':
      shutil.rmtree(dn)
      make_dir(dn)
    else:
      sys.exit()


def gen_mecab_parsed(sentences):
  import scripts
  s_list = []
  m = scripts.MeCab.Tagger()
  TOTAL = len(sentences)
  for i,s in enumerate(sentences):
    print(f'\r{i+1}/{TOTAL}', end='')
    res = scripts.MecabToken.fromParsedData(m.parse(s))
    _sub = []
    skip_suru = False
    skip_da = False
    for i,t in enumerate(res):
      if skip_suru:
        skip_suru = False
        continue
      if skip_da:
        skip_da = False
        continue
      if t.word in ['、', '。', '！']:
        continue
      if t.is_noun() and i+1 < len(res) and res[i+1].is_suru():
        _sub.append(('#VERB', f'{str(t)}{str(res[i+1])}'))
        skip_suru = True
      elif t.is_adjv() and i+1 < len(res) and res[i+1].is_suffix_adjv():
        _sub.append(('#ADJV', f'{str(t)}{str(res[i+1])}'))
        skip_da = True
      else:
        _sub.append(t.convert2tag())
    s_list.append(_sub)
  return s_list


def leaf2token(word, nodes):
  NON_UTILIZE = {
    'Noun': '#NOUN',
    'Postp': '#POSTP',
    'Adnominal': '#ADNM',
    'Adverb': '#ADV',
    'Conjunction': '#CONJ',
    'Interjection': '#INTJ',
  }
  if   nodes[-1].startswith('ADJV'):
    tag = '#ADJV'
  elif nodes[-1].startswith('ADJ'):
    tag = '#ADJ'
  elif nodes[-1].startswith('P_'):
    tag = '#POSTP'
  elif nodes[-1].startswith('AUX'):
    tag = '#AUXVERB'
  elif nodes[-1].startswith('V'):
    tag = '#VERB'
  elif nodes[-1] in NON_UTILIZE:
    tag = f'{NON_UTILIZE[nodes[-1]]}'
  else:
    tag  = f'#{nodes[-1]}'
  return (tag, word)


def ast2list(ast):
  def make_words(tree, words, nodes):
    if len(tree.subs()) == 0:
      leaf = str(tree)
      if leaf in ['', '、', '。', '！']:
        pass
      else:
        current = [get_tag(tree)] if get_tag(tree) != '' else []
        words.append(leaf2token(leaf, nodes+current))
    else:
      for i, (_, child) in enumerate(tree.subs()):
        current = [get_tag(tree)] if get_tag(tree) != '' else []
        make_words(child, words, nodes+current)
  words = []
  make_words(ast, words, [])
  return words


def compare_gk_mecab(sentences, gk_result):
  mp = [gen_mecab_parsed(sentences)]  # tpl[1]: 単語のみ比較
  mp.append(copy.deepcopy(mp[0]))   # tpl   : 単語と品詞を比較
  total_sentence, total_token = 0, 0
  no_diff_sentence, diff_token = [[], []], [0, 0]
  s = ['','']
  for ln, ast in gk_result:
    if not is_err(ast):
      total_sentence += 1
      total_token += len(mp[1][ln-1])
      for t in ast2list(ast):
        # 単語だけの一致チェック
        for mt in mp[0][ln-1]:
          if t[1] == mt[1]:
            mp[0][ln-1].remove(mt)
            break
        # 単語と品詞の一致チェック
        if t in mp[1][ln-1]:
          mp[1][ln-1].remove(t)
      for i in range(2):
        if len(mp[i][ln-1]) > 0:
          s[i] += '<!-- slide -->\n'
          s[i] += get_inputs(ast) + '\n'
          s[i] += 'MeCabRemain: ' + ' '.join(map(lambda tpl: f'({tpl[0]}, {tpl[1]})', mp[i][ln-1])) + '\n\n\n'
          diff_token[i] += len(mp[i][ln-1])
        else:
          no_diff_sentence[i].append(get_inputs(ast))
  with open('private/compare_log.md', 'w', encoding='utf_8') as f:
    f.write('<!-- slide -->\n# 【単語】\n\n\n'+s[0]+'<!-- slide -->\n# 【単語と品詞】\n'+s[1][:-1])
  print('\n【単語】')
  print(f'Accurate sentence: {len(no_diff_sentence[0])} / {total_sentence} => {round(100*len(no_diff_sentence[0])/total_sentence, 3)}[%]')
  print(f'Accurate token   : {total_token - diff_token[0]} / {total_token} => {round(100*(total_token - diff_token[0])/total_token, 3)}[%]')
  print('【単語と品詞】')
  print(f'Accurate sentence: {len(no_diff_sentence[1])} / {total_sentence} => {round(100*len(no_diff_sentence[1])/total_sentence, 3)}[%]')
  print(f'Accurate token   : {total_token - diff_token[1]} / {total_token} => {round(100*(total_token - diff_token[1])/total_token, 3)}[%]')
  with open('private/no_diff_inputs.txt', 'w', encoding='utf_8') as f:
    f.write('\n'.join(sorted(no_diff_sentence[1], key=len)))



def test(opt):
  options = parse_options(['-g', str(opt['-g'])])
  peg = load_grammar(options)
  parser = generator(options)(peg, **options)
  results = []
  fail_cnt = 0

  Path('test/result').mkdir(parents=True, exist_ok=True)

  START = time.time()
  for count, s in enumerate(opt['inputs']):
    sys.stdout.write(f'\rNow Processing: {count+1}/{len(opt["inputs"])}')
    try:
      tree = parser(s)
    except Exception as e:
      print(e)
    if is_err(tree):
      fail_cnt += 1
    results.append((count+1, tree))
    sys.stdout.flush()
  print()
  write_result(f'test/result/{opt["-t"].stem}_{opt["-g"].stem}.txt', results)
  END = time.time() - START
  TOTAL = len(opt['inputs'])
  print(f'SUCCESS RATE  : {TOTAL-fail_cnt}/{TOTAL} => {round(100*(TOTAL-fail_cnt)/TOTAL, 3)}[%]')
  print(f'TEST EXECUTION TIME: {round(END, 3)}[sec]')
  return results


def main(args):
  def arg2dict(d, l):
    if len(l) < 1:return 0
    head = l.pop(0)
    if head == '-t':
      d[head] = Path(l.pop(0))
      d['inputs'] = txt2array(d[head])
      arg2dict(d, l)
    elif head in ['-g']:
      d[head] = Path(l.pop(0))
      arg2dict(d, l)
    elif head in ['-n']:
      d[head] = Path(l.pop(0))
      shutil.copy(d[head], 'dic/TestNoun.txt')
      arg2dict(d, l)
    elif head in ['-Graph', '-Log', '-Compare']:
      d[head] = True
      arg2dict(d, l)
    else:
      print(f'Invalid argument: {head}')
      sys.exit()

  options = {
    '-t': '<TEXT PATH>',
    '-g': '<GRAMMAR PATH>',
    '-n': '<NOUN DIC PATH>',
    '-Graph': False,
    '-Log': False,
    '-Compare': False,
    'inputs': [],
  }
  arg2dict(options, args)
  results = test(options)
  if options['-Log']:
    print_err(results)
  if options['-Graph']:
    if not shutil.which('dot'):
      print('Not find "dot" command')
      print('Please install "Graphviz"')
      sys.exit()
    MAX_COUNT = len(results)
    DIR_NAME = f'graph_{options["-t"].stem}_{options["-g"].stem}'
    make_dir(DIR_NAME)
    st = time.time()
    for count, (ln, ast) in enumerate(results):
      sys.stdout.write(f'\rNow Processing: {count+1}/{MAX_COUNT}')
    gen_graph(ast, f'{DIR_NAME}/{count}.png')
    sys.stdout.flush()
    et = time.time() - st
    print(f'\nGEN_GRAPH EXECUTION TIME: {et}[sec]')
  if options['-Compare']:
    compare_gk_mecab(options['inputs'], results)

if __name__ == "__main__":
  # e.g.) python tester.py -t test/javadoc.txt -g gk.tpeg -Graph -Log
  main(sys.argv[1:])
