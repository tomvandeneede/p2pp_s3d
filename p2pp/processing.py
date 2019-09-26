__author__ = 'Tom Van den Eede'
__copyright__ = 'Copyright 2019, Palette2 Splicer Post Processing Project for Simplify 3D'
__credits__ = ['Tom Van den Eede']
__license__ = 'GPLv3'
__maintainer__ = 'Tom Van den Eede'
__email__ = 't.vandeneede@pandora.be'

import p2pp.variables as v
import p2pp.gcode as gcode
import re
import p2pp.purgetower as purgetower
from p2pp.logging import error, warning, comment
from p2pp.formatnumbers import hexify_short, hexify_float, hexify_long, hexify_byte
import p2pp.gui as gui


def check_tooldefs():
    for i in range(4):
        if v.toolsused[i] and not v.filament_type[i]:
            return False
    return True

def omegaheader():
    header = []

    header.append('O21 ' + hexify_short(20) + "\n")

    if v.printerid:
        header.append('O22 D' + v.printerid.strip("\n") + "\n")
    else:
        error(";P2PP PRINTERPROFILE command is missing from configuration")

    header.append('O23 D0001' + "\n")  # unused
    header.append('O24 D0000' + "\n")  # unused

    toolinfo = ["D0", "D0", "D0", "D0" ]

    materials = {}
    header.append("\n; P2 Input / Material usage info\n")
    for i in range(4):
        if v.toolsused[i] and v.filament_type[i] not in materials.keys():
            materials[v.filament_type[i]] = len(materials.keys())+1

    for i in range(4):
        if v.toolsused[i]:
            toolinfo[i] = "D{}_input{}_{}".format(materials[v.filament_type[i]], i,v.filament_type[i])

    header.append('O25 {} {} {} {}'.format(toolinfo[0],toolinfo[1],toolinfo[2],toolinfo[3]) + "\n")
    header.append("; P2 Number of splices = {}\n".format(len(v.toolchangeinfo)))
    header.append('O26 ' + hexify_short(len(v.toolchangeinfo)) + "\n")
    header.append("; P2 Number of pings = {}\n".format(len(v.pingpositions)))
    header.append('O27 ' + hexify_short(len(v.pingpositions)) + "\n")
    header.append("; P2 Number of splicing algorithms = {}\n".format(len(v.algooverview)))
    header.append('O28 ' + hexify_short(len(v.algooverview)) + "\n")


    previous_change = 0
    header.append('O29 ' + hexify_short(0) + "\n")
    header.append("\n; P2 Tool change information\n")

    v.processcomments.append("\n")
    v.processcomments.append(";------------------------------------\n")
    v.processcomments.append(";SPLICE INFORMATION - {} SPLICES\n".format(len(v.toolchangeinfo)))
    v.processcomments.append(";------------------------------------\n")

    previoussplice = 0
    for i in range(len(v.toolchangeinfo)):
        nextpos = v.toolchangeinfo[i]["E"]+v.spliceoffset
        if previous_change==0 and nextpos < 100:
            error("First splice is {}mm too short.  Try adding brim or skirt".format(100-nextpos))
        else:
            splicelength = nextpos - previous_change
            if splicelength < 70:
                error("Short splice {} is {}mm too short. Try increasing purge".format(i+1, 70-splicelength))
        previous_change = nextpos


        header.append("O30 D{:0>1d} {}\n".format(v.toolchangeinfo[i]["Tool"],
                                                 hexify_float(nextpos)))
        v.processcomments.append(";Tool {} Length {:.2f}mm\n".format(v.toolchangeinfo[i]["Tool"], nextpos-previoussplice))
        previoussplice = nextpos


    v.processcomments.append("\n")

    v.processcomments.append("\n")
    v.processcomments.append(";------------------------------------\n")
    v.processcomments.append(";PING INFORMATION - {} PINGS\n".format(len(v.pingpositions)))
    v.processcomments.append(";------------------------------------\n")

    for i in range( len(v.pingpositions)):
        v.processcomments.append(";PING {:>4}  at {:8.2f}mm\n".format(i,v.pingpositions[i]))

    v.processcomments.append("\n")

    header.append("\n; P2 Splicing algorithms\n")
    if not "DEFAULT" in v.algorithm.keys():
        v.algorithm['DEFAULT'] = (0,0,0)

    if check_tooldefs():

        for algo in v.algooverview:

            fils = algo.split("_")

            if algo in v.algorithm.keys():
                info = v.algorithm[algo]
            else:
                info = v.algorithm["DEFAULT"]
            process = "{} {} {}".format(hexify_short(int(info[0])),
                              hexify_short(int(info[1])),
                              hexify_short(int(info[2]))
                              )

            header.append("O32 D{}{} {}\n".format(materials[fils[0]],materials[fils[1]],process))

    header.append("\n")
    header.append("O1 D{} {}\n"
                  .format("_S3D_P2PP_PRINT_", hexify_long(int(v.total_extrusion + v.extra_extrusion_at_end + v.spliceoffset))))
    header.append("\n")

    header = header + v.processcomments
    header.append(";--- END OF P2 HEADER ---\n")
    header.append("\n")



    return header

def create_regex_objects():
    v.regex_layer = re.compile("^; layer (\d+), Z = (\d+\.\d+)")
    v.regex_p2pp = re.compile("^;\s*P2PP\s+([^=]+)=?(.*)$")
    v.regex_layer_height= re.compile("^;\s*layerHeight,(\d+\.\d+)")
    v.regex_extrusion_width= re.compile("^;\s*extruderWidth,(\d+\.\d+)")
    v.regex_use_prime_pillar= re.compile("^;\s*usePrimePillar,(\d)")
    v.regex_purge_info = re.compile("(\w+):\[\s*(\d+)\s*,\s*(\d+)\s*\]")
    v.regex_bed_size = re.compile("^;\s*stroke([X|Y])override,(\-?\d+)")
    v.regex_bed_origin = re.compile("^;\s*originOffset([X|Y])override,(\-?\d+)")
    v.regex_primepillar = re.compile("^;\s*primePillarLocation,(\-?\d+)")
    v.regex_tower_width = re.compile("^;\s*primePillarWidth,(\-?\d+)")


def p2pp_command( command , parameter):

    command = command.upper()

    if command == "LINEARPINGLENGTH":
        v.pinglength = float(parameter)
        v.pingincrease = 1

    if command == "TOWERDELTA":
        v.towerdelta = float(parameter)

    if command == "PRINTERPROFILE":
        v.printerid = parameter
        gui.set_printer_id(v.printerid)

    if command == "EXTRAENDFILAMENT":
        v.extra_extrusion_at_end = float(parameter)

    if command == "SPLICEOFFSET":
        v.spliceoffset = float(parameter)

    if command == "AUTOEXPANDTOWER":
        v.expand_tower = True

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
            v.algorithm["{}".format(m.group(1))]= (int(m.group(2)), int(m.group(3)), int(m.group(4)))
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

    m = v.regex_layer.match(line)
    if m:
        v.process_layer = int(m.group(1))
        v.process_layer_z = float(m.group(2))
        v.layer_toolchange_count.append(0)
        v.layer_purge_volume.append(0.0)
        v.layer_purge_structure.append(0)


    m = v.regex_p2pp.match(line)
    if m:
        p2pp_command( m.group(1), m.group(2))

    m = v.regex_bed_size.match(line)
    if m:
        if m.group(1)=="X":
            v.bed_size_x = int(m.group(2))
        else:
            v.bed_size_y = int(m.group(2))

    m = v.regex_bed_origin.match(line)
    if m:
        if m.group(1)=="X":
            v.bed_min_x = int(m.group(2))
        else:
            v.bed_min_y = int(m.group(2))

    m = v.regex_layer_height.match(line)
    if m:
        lh = float(m.group(1))
        if not v.layer_height:
            v.layer_height = lh
        else:
            if not lh == v.layer_height:
                error("Layer Height of all processes should be the same")

    m = v.regex_primepillar.match(line)
    if m:
        v.pillarposition = int(m.group(1))

    m = v.regex_tower_width.match(line)
    if m:
        v.pillarwidth = int(m.group(1))

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
        if "prime pillar" in line:
            v.mode = MODE_PURGE
        else:
            v.mode = MODE_OTHER

def calc_purge_length(_from , _to):
    tmp = (v.unloadinfo[_from] + v.loadinfo[_to])/2
    if not tmp:
        tmp = 0
    return tmp

def process_tool_change(gc):


    if not gc:
        tmp = {"Layer": 999 , "Tool": int(v.previous_tool), "E": v.total_extrusion}
        v.toolchangeinfo.append(tmp)
        return

    tmp = {"Layer": gc.layer, "Tool": int(v.previous_tool), "E": v.total_extrusion}


    new_tool = int(gc.command[1])

    if new_tool == v.current_tool:
        gc.move_to_comment("-- Change to current filament --")
        return

    if v.current_tool == -1:
        v.current_tool = new_tool
        v.previous_tool = new_tool
        # Issue brim layer
        for i in purgetower.brimlayer:
            i.issue_command()
        return

    if not v.previous_tool == v.current_tool:
        v.algooverview.add("{}_{}".format(v.filament_type[v.previous_tool], v.filament_type[v.current_tool]))

    v.toolchangeinfo.append(tmp)
    gc.move_to_comment("Toolchange handled by Palette")

    required_purge = calc_purge_length(v.current_tool , new_tool)
    purgetower.purge_generate_sequence(required_purge / v.extrusion_multiplier) * v.extrusion_multiplier

    v.previous_tool = v.current_tool
    v.current_tool = new_tool


def process_gcode():

    gui.comment("Processing "+v.filename)
    linecount = len(v.rawfile)
    lineidx = 0
    for line in v.rawfile:
        lineidx +=1
        gui.setprogress(int(50 * lineidx / linecount))

        # skip fully empty lines
        if len(line) == 0:
            continue

        tmp = gcode.GCodeCommand(line)

        # parse comments
        if line.startswith(";"):
            parse_comment( line )

        # we calculate the purge for tower position
        # afterwards this code is removed
        #########################################################
        if v.mode == MODE_PURGE:
            if tmp.E:
                v.purge_minx = min(v.purge_minx, tmp.get_parameter("X", 9999))
                v.purge_maxx = max(v.purge_maxx, tmp.get_parameter("X", -9999))
                v.purge_miny = min(v.purge_miny, tmp.get_parameter("Y", 9999))
                v.purge_maxy = max(v.purge_maxy, tmp.get_parameter("Y", -9999))

            if tmp.is_comment() and tmp.comment.startswith(' process'):
                v.gcodes.append(tmp)
        else:
            v.gcodes.append(tmp)

        toolchange = tmp.is_toolchange()
        if toolchange in [0,1,2,3]:

            # keep track of the tools used
            if not v.toolsused[ toolchange ] :
                if not v.filament_type[toolchange]:
                    error("TOOL_{} setting command missing - output file cannot be created".format(toolchange))
            v.toolsused[ toolchange] = True

            # caulculate the purge
            if not (v.parse_curtool == -1):
                v.layer_toolchange_count[-1] += 1
                if v.filament_type[toolchange] and v.filament_type[v.parse_curtool] and not (v.parse_curtool==toolchange):
                    v.layer_purge_volume[-1] += calc_purge_length(v.parse_curtool , toolchange)
                    v.parse_prevtool = v.parse_curtool
                    v.parse_curtool = toolchange

            else:
                v.parse_curtool = v.parse_prevtool = toolchange


    comment('S3D Purge: {:.3f},{:.3f} -> {:.3f},{:.3f}'.format(v.purge_minx, v.purge_miny, v.purge_maxx, v.purge_maxy))
    comment('Bed Size: {:.3f},{:.3f} -> {:.3f},{:.3f}'.format(v.bed_min_x,v.bed_min_y,v.bed_size_x,v.bed_size_y ))
    comment("filament Info: " + v.filament_type.__str__())
    comment("Tool unload info: " + v.unloadinfo.__str__())
    comment("Tool load info: " + v.loadinfo.__str__())
    comment("Algorithms:" + v.algorithm.__str__())

    comment("Maximum purge needed per layer: {}mm".format(max(v.layer_purge_volume)))


    expand = 0
    tower_fits = False
    while not tower_fits:
        purgetower.purge_create_layers(v.purge_minx-1 , v.purge_miny-1 , v.purge_maxx - v.purge_minx+2, v.purge_maxy - v.purge_miny +2)
        tower_fits = purgetower.simulate_tower(purgetower.sequence_length_solid ,purgetower.sequence_length_empty)
        if not tower_fits:
            purgetower.tower_auto_expand(10)
            expand += 10


    if expand > 0:
        warning("Tower expanded by {}mm".format(expand))

    comment('New purge volume : {:.3f},{:.3f} -> {:.3f},{:.3f}'.format(v.purge_minx, v.purge_miny, v.purge_maxx, v.purge_maxy))
    comment("Filament needed for a solid purge layer: {}mm".format(purgetower.sequence_length_solid))
    comment("Filament needed for a sparse purge layer: {}mm".format(purgetower.sequence_length_empty))

    lineidx = 0
    linecount = len(v.gcodes)
    for g in v.gcodes:
        lineidx += 1
        gui.setprogress(50 + int(50 * lineidx / linecount))
        if g.command in ["M220"]:
            g.move_to_comment("IGNORED COMMAND")
            g.issue_command()
            continue     # no further processing required

        if g.command == "M221":
            v.extrusion_multiplier = g.get_parameter("S", v.extrusion_multiplier*100)/100
            g.issue_command()
            continue      # no further processing required

        if g.command in ["T0", "T1" , "T2", "T3"]:
            process_tool_change(g)
            g.issue_command()
            continue      # no further processing required

        if g.command in ["M104", "M106", "M109", "M140", "M190", "M73", "M900", "M84"]:
            g.issue_command()
            continue      # no further processing required

        if g.is_movement_command():
            v.current_position_x = g.get_parameter("X", v.current_position_x)
            v.current_position_y = g.get_parameter("Y", v.current_position_y)
            v.current_position_z = g.get_parameter("Z", v.current_position_z)
            if purgetower.moveintower():
                error("MODEL COLLIDES WITH TOWER.")
        g.issue_command()

    process_tool_change(None)

    if v.maxdelta >0.3 or v.mindelta < -0.3:
        warning("Tower hight deviates {:.2f}mm above and {:.2f}mm below print level".format(-v.mindelta, v.maxdelta))
        warning("Make sure to keep enough distance between tower and object to avoid collisions")
        warning("If the tower grows over the print height, consider increasing the prime pillar width in S3D")


    gui.completed()

def save_code():
    output_file = v.filename.replace(".gcode", ".mcf.gcode")

    comment("saving output to "+output_file)


    header = omegaheader()
    comment(" number of lines: {}".format(len(header)+len(v.output_code)))

    try:
        opf = open(output_file,"w",  encoding='utf-8')
    except TypeError:
        try:
            opf = open(output_file, "w")
        except IOError:
            error ("Could not open output file {}".format(output_file))
            return
    except IOError:
        error("Could not read open output {}".format(output_file))
        return
    opf.writelines(header)
    opf.writelines(v.output_code)
    opf.close()
    pass

def process_file():

    create_regex_objects()
    process_gcode()
    save_code()

