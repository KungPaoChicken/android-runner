import sys
from os.path import expanduser
from config_checker import Experiment


def main():
    if len(sys.argv) == 1:
        print("Usage: android-runner config_file")
    exp = Experiment().from_config(expanduser(sys.argv[1]))
    if exp.is_valid():
        # Print excerpts of the experiment
        start = raw_input("start experiment? [y]/n ")
        if 'n' in start:
            print("Experiment cancelled.")
        else:
            exp.run()

if __name__ == "__main__":
    main()
