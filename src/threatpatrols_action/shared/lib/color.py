#
# https://stackoverflow.com/questions/287871/how-do-i-print-colored-text-to-the-terminal#287944
# https://svn.blender.org/svnroot/bf-blender/trunk/blender/build_files/scons/tools/bcolors.py
#


class ansicode:
    HEADER = "\033[95m"
    #
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    #
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    #
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    #
    ENDC = "\033[0m"
