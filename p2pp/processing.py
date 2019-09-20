__author__ = 'Tom Van den Eede'
__copyright__ = 'Copyright 2019, Palette2 Splicer Post Processing Project for Simplify 3D'
__credits__ = ['Tom Van den Eede']
__license__ = 'GPLv3'
__maintainer__ = 'Tom Van den Eede'
__email__ = 't.vandeneede@pandora.be'

import p2pp.variables as v
import p2pp.gcode as gcode
import re
from p2pp.logging import error, warning, comment

def create_regex_objects():
    v.regex_layer = re.compile("; layer (\d+), Z = (\d+\.\d+)")
    v.regex_p2pp = re.compile(";\s*P2PP\s+([^=]+)=?(.*)$")
    v.regex_layer_height= re.compile(";\s*layerHeight,(\d+\.\d+)")
    v.regex_extrusion_width= re.compile(";\s*extruderWidth,(\d+\.\d+)")
    v.regex_use_prime_pillar= re.compile(";\s*usePrimePillar,(\d)")
    v.regex_purge_info = re.compile("(\w+):\[\s*(\d+)\s*,\s*(\d+)\s*\]")


def p2pp_command( command , parameter):

    command = command.upper()

    if command == "LINEARPINGLENGTH":
        v.pinglength = float(parameter)
        v.pingincrease = 1

    if command == "TOWERDELTA":
        v.towerdelta = float(parameter)

    if command in [ "TOOL_0", "TOOL_1", "TOOL_2", "TOOL_3"]:
        m = v.regex_purge_info.match(parameter)
        if m:
            tool = int(command[-1])
            v.filament_type[tool] = m.group(1).upper()
            v.loadinfo[tool] = int(m.group(2))
            v.unloadinfo[tool] = int(m.group(3))

    if command.startswith("MATERIAL"):

        _deflt = "MATERIAL_DEFAULT_(\d+)_(\d+)_(\d+)"
        _algo = "MATERIAL_(\w+_\w+)_(\d+)_(\d+)_(\d+)"

        m = re.search(_algo, command)
        if m:
            v.algorithm["{}".format(m.group(1))] = (int(m.group(2)), int(m.group(3)), int(m.group(4)))
        else:
            m = re.search(_deflt, command )
            if m:
                v.algorithm["DEFAULT"] = ( int(m.group(1)), int(m.group(2)), int(m.group(3)))


MODE_START = 0
MODE_INFILL = 1
MODE_PERIMETER = 2
MODE_OTHER = 3
MODE_PURGE = 4

section = ["START", "INFILL", "PERIMETER", "OTHER", "PURGE"]

def parse_comment( line ):

    ## ; layer 60, Z = 12.000
    m = v.regex_layer.match(line)
    if m:
        v.process_layer = int(m.group(1))
        v.process_layer_z = float(m.group(2))

    m = v.regex_p2pp.match(line)
    if m:
        p2pp_command( m.group(1), m.group(2))

    m = v.regex_layer_height.match(line)
    if m:
        lh = float(m.group(1))
        if not v.layer_height:
            v.layer_height = lh
        else:
            if not lh == v.layer_height:
                error("Layer Height of all processes should be the same")

    m = v.regex_extrusion_width.match(line)
    if m:
        ew = float(m.group(1))
        if not v.extrusion_width:
            v.extrusion_width = ew
        else:
            if not ew == v.extrusion_width:
                error("Extruder Width of all processes should be the same")

    m = v.regex_use_prime_pillar.match(line)
    if m:
        if m.group(1) == "1":
            v.prime_pillar += 1

    if line.startswith("; feature"):
        v.mode = None
        if line == "; feature infill":
            v.mode = MODE_INFILL

        if line == "; feature solid layer":
            v.mode = MODE_PERIMETER

        if line == "; feature inner perimeter":
            v.mode = MODE_PERIMETER

        if line == "; feature outer perimeter":
            v.mode = MODE_PERIMETER

        if line == "; feature prime pillar":
            v.mode = MODE_PURGE

        if v.mode == None:
            v.mode = MODE_OTHER

def process_gcode():

    for line in v.rawfile:
        # skip fully empty lines
        if len(line) == 0:
            return
        # parse comments
        if line.startswith(";"):
            parse_comment( line )

        tmp = gcode.GCodeCommand(line)
        v.gcodes.append(tmp)

        if v.mode == MODE_PURGE:
            v.purge_maxx = max(v.purge_maxx, tmp.get_parameter("X", -9999))
            v.purge_minx = min(v.purge_minx, tmp.get_parameter("X", 9999))
            v.purge_maxy = max(v.purge_maxy, tmp.get_parameter("Y", -9999))
            v.purge_miny = min(v.purge_miny, tmp.get_parameter("Y", 9999))

        toolchange = tmp.is_toolchange()
        if toolchange in [0,1,2,3]:
                v.toolsused[ toolchange]  = True

    print('Tower: {:.3f},{:.3f} -> {:.3f},{:.3f}'.format(v.purge_minx,v.purge_miny,v.purge_maxx,v.purge_maxy ))
    print("filament Info: ", v.filament_type)
    print("Tool unload info: ", v.unloadinfo)
    print("Tool load info: ", v.loadinfo)
    print("Algorithms:", v.algorithm)

    previous_section= 0
    feature_extrusion = 0
    tool_extrude = 0
    for g in v.gcodes:
        if g.command and g.command[0]=="T":
            print("Previous tool:{:.3f}mm".format( tool_extrude))
            print("Switching tool ", g.command)
            tool_extrude = 0
        if not g.codesection == previous_section:
            # print( "Layer {}  Layer-z: {:.3f} Section {} extrudes {:.3f}mm".format(g.layer, g.layerz, section[previous_section], feature_extrusion))
            feature_extrusion = 0

        feature_extrusion += g.get_parameter("E",0)
        tool_extrude += g.get_parameter("E",0)
        previous_section = g.codesection
    print("Previous tool:{:.3f}mm".format(tool_extrude))
    # print("Section {} extrudes {:.3f}mm".format(section[previous_section], feature_extrusion))



def process_file():

    create_regex_objects()
    process_gcode()
