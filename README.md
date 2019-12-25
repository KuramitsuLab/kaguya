# KAGUYA

## ファイル概要
### `gk2.tpeg`
+ gk1に、助詞に関する厳格な規則を追加した文法
+ 具体的には、助詞規則も助動詞規則のように定義した
+ また、外部辞書には、手を加えた`dic-edited`を用いる
  + 誤ったマッチを引き起こしやすい、マイナーな単語を除去した
  + 除外した単語は`dic-edited/removed.txt`に記述している


### `gk1.tpeg`
+ 学校文法を先読みありで定義した文法


### `gk0.tpeg`
+ 学校文法を先読みなしで定義した文法


### `cj.tpeg`
+ Controlled Japanese


### `koinu.tpeg`
+ Puppy用の文法？


### `gen_dic.py`
+ IPA辞書を扱うプログラム
+ `dic/`下に各品詞の辞書を、`dic/Verb`下に動詞の辞書を生成する
+ 辞書には "ipadic-2.7.0" を使用している


### `gen_noun.py`
+ Mecabでテストデータに形態素解析をかけて名詞辞書を生成するプログラム


### `tester.py`
+ パーステストを行うプログラム
+ `python tester.py test/<パース対象のファイル> <解析に使う文法>`で実行する
+ パース結果（テキスト）は、`test/result/<ファイル名>.txt`に出力する
+ 'Do test with generating graph?'に`y`でツリー図も生成する
  + "Graphviz" の`dot`コマンドを使える必要がある
  + Homebrewが入っていれば`brew install graphviz`でインストールできる
  + `graph/<ファイル名>/<行番号>.png`として図を保存する


### `all_test.sh`
+ `gakkou.tpeg`と`kaguya0.tpeg`のテストをまとめて行う
+ `sh all_test.sh python`で実行すると`test_python`に結果をまとめる
