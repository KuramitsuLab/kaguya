import re


with open('sample_text_ethereum.txt', mode='r', encoding='utf_8') as f_in:
    with open('sample_text_ethereum_adjust.txt', mode='w') as f_out:
        s = f_in.read()
        s = re.sub(r'[ ]', '', s)
        s = re.sub(r'^[\n]', '', s)
        s = re.sub(r'[。]', '。\n', s)
        f_out.write(s)

