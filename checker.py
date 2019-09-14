from tester import *
from gen_graph import *
import sys


def main(args):
    try:
        options = parse_options(['-g', args[1]])
        peg = load_grammar(options)
        parser = generator(options)(peg, **options)

        while True:
            s = input('>> ')

            results = {
                'success': [],
                'fail': [],
            }

            tree = parser(s)
            if 'Syntax Error' in repr(tree):
                print('<Parse Error>')
                print(f'入力: {s}')
                print(f'残り: {str(tree)}')
            else:
                gen_png((s, repr(tree)), '.', 'temp')
                Path(GEN_DOT_PATH).unlink()
    except KeyboardInterrupt as e:
        print()
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main(sys.argv)
