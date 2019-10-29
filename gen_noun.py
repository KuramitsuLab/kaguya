# ansデータから名詞辞書を作成する
import sys

def main(path):
    noun = []
    adjv = []
    FILENAME = path[path.rfind('/')+1: path.rfind('.')]
    with open(path, mode='r', encoding='utf_8') as f:
        tokens = f.read().split('\n')
    for token in tokens:
        if token.endswith('(名詞)'):
            noun.append(token[0:token.find(' (名詞)')])
        elif token.endswith('(形容動詞)'):
            adjv.append(token[0:token.find(' (形容動詞)')])
    with open(f'dic/Noun_{FILENAME}.txt', mode='w', encoding='utf_8') as f:
        f.write('\n'.join(set(noun)))
    print('\n'.join(set(adjv)))


if __name__ == "__main__":
    main(sys.argv[1])
