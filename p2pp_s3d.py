__author__ = 'Tom Van den Eede'
__copyright__ = 'Copyright 2019, Palette2 Splicer Post Processing Project for Simplify 3D'
__credits__ = ['Tom Van den Eede']
__license__ = 'GPLv3'
__maintainer__ = 'Tom Van den Eede'
__email__ = 't.vandeneede@pandora.be'


import sys
import platform
import os
import p2pp.gui as gui
import p2pp.variables as v
import p2pp.processing as processing
from p2pp.logging import error, warning, comment




def main(filename):

    try:
        opf = open(filename, encoding='utf-8')
    except TypeError:
        try:
            opf = open(filename)
        except IOError:
            error ("Could not read input file {}".format(filename))
            return
    except IOError:
        error("Could not read input file {}".format(filename))
        return

    v.rawfile = opf.readlines()
    opf.close()

    v.rawfile = [item.strip() for item in v.rawfile]
    v.filename = filename
    gui.setfilename(filename)
    processing.process_file()



def usage():
    comment("Use:  p2pp_s3d [filename]")


if __name__ == "__main__":

    number_of_args = len(sys.argv)

    if number_of_args == 1:
        platformD = platform.system()
        if platformD == 'Darwin':
            comment('{}/p2pp_s3d.command "[output_filepath]"'.format(os.path.dirname(sys.argv[0])))
        elif platformD == 'Windows':
            if " " in os.path.dirname(sys.argv[0]):
                warning("Your path contains spaces!!!")
                comment('"{}/\\p2pp_s3d.bat" "[output_filepath]"'.format(os.path.dirname(sys.argv[0])))
            else:
                comment('{}/\\p2pp_s3d.bat "[output_filepath]"'.format(os.path.dirname(sys.argv[0])))
        pass

    if number_of_args == 2:
        main ( filename = sys.argv[1] )


    if number_of_args > 2:
        error("Invalid usage of p2pp_s3d")
        usage()

    gui.close_button_enable()
