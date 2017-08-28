import sys


def main(output_root):
    print('Output root: {}'.format(output_root))


if __name__ == '__main__':
    if len(sys.argv) == 1:
        main(sys.argv[1])
