__author__ = 'Tom Van den Eede'
__copyright__ = 'Copyright 2019, Palette2 Splicer Post Processing Project for Simplify 3D'
__credits__ = ['Tom Van den Eede']
__license__ = 'GPLv3'
__maintainer__ = 'Tom Van den Eede'
__email__ = 't.vandeneede@pandora.be'

import p2pp.gui as gui


def error(text):
    gui.error(text)


def warning(text):
    gui.warning(text)


def comment(text):
    gui.comment(text)