import MeCab
import re
from pathlib import Path


m = MeCab.Tagger("-Ochasen")

test_cases = Path('test/').glob('*.txt')



for file in test_cases:
    words = []
    with open(file, mode='r', encoding='utf_8') as f:
        for count,l in enumerate(f.readlines()):
            if count == 0:continue
            for p in m.parse(l).split('\n'):
                datas = p.split()  # [そのまま, 読み方, 素読み, 品詞名]
                if len(datas) >= 4 and '名詞' in datas[3] and not datas[0] in words:
                    words.append(datas[0])
    with open(f'dic/Noun/{file.name}', mode='w', encoding='utf_8') as f:
        f.write('\n'.join(words))
