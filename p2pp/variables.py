__author__ = 'Tom Van den Eede'
__copyright__ = 'Copyright 2019, Palette2 Splicer Post Processing Project for Simplify 3D'
__credits__ = ['Tom Van den Eede']
__license__ = 'GPLv3'
__maintainer__ = 'Tom Van den Eede'
__email__ = 't.vandeneede@pandora.be'

toolsused = [False, False, False, False]
toolchangeinfo = []
toolchangeposition = []
pingpositions = []
layer_toolchange_count = []
layer_purge_volume = []
layer_purge_structure = []
algooverview = set([])
retraction = 0.8

mindelta = 999
maxdelta = -999

lastping = 0

printerid = None

filament_type = [None, None, None, None]
loadinfo = [80, 80, 80, 80]
unloadinfo = [80, 80, 80, 80]
algorithm = {}

processcomments = []

extra_extrusion_at_end = 150
spliceoffset = 20

purge_minx = 9999
purge_maxx = -9999
purge_miny = 9999
purge_maxy = -9999

bed_min_x = 0
bed_min_y = 0
bed_size_x = 0
bed_size_y = 0

brim_generated = False

pingincrease = 1.03
pinglength = 350

towerdelta = 0

rawfile = []
gcodes = []
output_code = []

wipe_feedrate = 3000        #default is 50mm/s
wipe_feedrate1 = 1200       #default is 20mm/s
purgelayer = 1

layer_height = None
extrusion_width = None
prime_pillar = 0

# nex two variables keep the mcf layer value
process_layer = 0
process_layer_z = 0

# regex objects

regex_layer = None
regex_p2pp = None
regex_layer_height = None
regex_extrusion_width = None
regex_use_prime_pillar = None
regex_purge_info = None
regex_bed_size = None
regex_bed_origin = None
regex_primepillar = None
regex_tower_width = None
regex_process = None

current_position_x = 0
current_position_y = 0
current_position_z = 0

splice_procent = False

previous_tool = -1
current_tool = -1
toolchange = 0
toolchangepos = 0

extrusion_multiplier = 1.0
total_extrusion = 0

filename = ""

parse_prevtool = -1
parse_curtool = -1

expand_tower = False
pillarposition = -1
pillarwidth = 0

mode = 0
