# KAGUYA
KAGUYA関連のレポジトリ

# ファイル概要
## `kaguya0.tpeg`
+ KAGUYA文法本体

## `gen_auxverb.py`
+ 助動詞フレーズの生成プログラム

## `ipadic_control.py`
+ IPA辞書全般を扱うプログラム

## `tester.py`
+ パーステストを行うプログラム
+ `python tester.py test/<パース対象のファイル>`で実行
+ `<ファイル名>_fail.txt`と`<ファイル名>_success.txt`に入力文字列とASTを記述する
