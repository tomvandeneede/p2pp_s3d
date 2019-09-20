__author__ = 'Tom Van den Eede'
__copyright__ = 'Copyright 2019, Palette2 Splicer Post Processing Project for Simplify 3D'
__credits__ = ['Tom Van den Eede']
__license__ = 'GPLv3'
__maintainer__ = 'Tom Van den Eede'
__email__ = 't.vandeneede@pandora.be'


toolsused = [ False, False, False, False]
toolchangeinfo = []

filament_type = [None, None, None, None]
loadinfo = [80, 80, 80, 80]
unloadinfo = [80, 80, 80, 80]
algorithm = {}


purge_minx=9999
purge_maxx=-9999
purge_miny=9999
purge_maxy=-9999


pingincrease = 1.03
pinglength   = 350

towerdelta = 0

rawfile = []
gcodes  = []

layer_height = None
extrusion_width = None
prime_pillar = 0

# nex two variables keep the processing layer value
process_layer = 0
process_layer_z = 0


#regex objects

regex_layer = None
regex_p2pp = None
regex_layer_height = None
regex_extrusion_width = None
regex_use_prime_pillar = None
regex_purge_info = None


mode = 0