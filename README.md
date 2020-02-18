# KAGUYA

## Grammars

### `gk0.tpeg`
+ 学校文法を先読みなしで定義した文法


### `gk1.tpeg`
+ 学校文法を先読みありで定義した文法


### `gk2.tpeg`
+ gk1に、助詞に関する厳格な規則を追加した文法
+ 具体的には、助詞規則も助動詞規則のように定義した
+ また、外部辞書には、手を加えた`dic-edited`を用いる
  + 誤ったマッチを引き起こしやすい、マイナーな単語を除去した
  + 除外した単語は`dic-edited/removed.txt`に記述している


### `cj.tpeg`
+ Controlled Japanese


### `cj0.tpeg`
+ 動かない


### `cj2.tpeg`
+ `cj.tpeg`の改良版？


### `cj3.tpeg`
+ `cj2.tpeg`の改良版


### `koinu.tpeg`
+ Puppy用の文法？


## Scripts

### `tester.py`
+ 主にGK文法のパーステストを行うプログラム
+ `python tester.py -t <パース対象のファイル> -g <解析に使う文法ファイル> -n <解析に使う名詞辞書>`で実行する
+ パース結果（テキスト）は、`test/result/<ファイル名>_<文法名>.txt`に出力する
+ 追加引数`-Graph`でグラフを生成する
  + "Graphviz" の`dot`コマンドを使える必要がある
  + Homebrewが入っていれば`brew install graphviz`でインストールできる
  + `graph/<ファイル名>/<行番号>.png`として図を保存する
+ 追加引数`-Log`でコンソールに解析に失敗した文と残り文字列を表示する
+ `-Compare`でMeCab+IPA辞書との比較を行う


### `scripts.py`
+ `parse_ast`: `ast.tpeg`を使ってresultの解析木をもう一回ツリーに変換する
+ `analyze`: MeCabと辞書を使って`javadoc.txt`を解析していろいろ結果を出力する
+ `get~`: JavaAPIDocumentをダウンロードしてテキスト化する
+ mecab_parseの引数に他の辞書を指定可能
  + `~~/mecab-ipadic-neologd`
  + `~~/unidic-cwj-2.3.0`


### `gen_dic.py`
+ IPA辞書からGK文法用の辞書を生成する
+ `dic/`下に各品詞の辞書を、`dic/Verb`下に動詞の辞書を生成する

