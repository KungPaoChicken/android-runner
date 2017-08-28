import sys


def main(output_root):
    print(output_root)
    pass


if __name__ == '__main__':
    if len(sys.argv) == 1:
        main(sys.argv[1])
