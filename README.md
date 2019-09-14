# KAGUYA
KAGUYA関連のレポジトリ

# ファイル概要
## `kaguya0.tpeg`
+ KAGUYA文法本体


## `gen_dic.py`
+ IPA辞書全般を扱うプログラム
+ `dic/`下に各品詞を、`dic/Verb`下に動詞のチョイス用辞書を生成する
+ 辞書には "ipadic-2.7.0" を使用している


## `tester.py`
+ パーステストを行うプログラム
+ `python tester.py test/<パース対象のファイル>`で実行する
+ パース失敗の場合は、`test/result/fail/<ファイル名>.txt`に入力文字列と残り文字列を記述する
+ パース成功の場合は、`test/result/success/<ファイル名>.txt`に入力文字列とASTを記述する


## `gen_graph.py`
+ ASTからツリー図を作成するプログラム
+ "Graphviz" の`dot`コマンドを使える必要がある
  + Homebrewが入っていれば`brew install graphviz`でインストールできる
+ `python gen_graph.py test/result/success/<ファイル名>.txt`で実行する
+ `graph/<ファイル名>/<番号>.png`として図を保存する


## `checker.py`
+ インタプリタでパースしつつ木をグラフ化するプログラム
+ `python checker.py <文法ファイル>`で実行
+ `./temp.png`が木の図
