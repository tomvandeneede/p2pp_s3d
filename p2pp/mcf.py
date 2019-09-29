__author__ = 'Tom Van den Eede'
__copyright__ = 'Copyright 2019, Palette2 Splicer Post Processing Project for Simplify 3D'
__credits__ = ['Tom Van den Eede']
__license__ = 'GPLv3'
__maintainer__ = 'Tom Van den Eede'
__email__ = 't.vandeneede@pandora.be'

import p2pp.variables as v
import p2pp.gcode as gcode
import p2pp.purgetower as purgetower
import p2pp.gui as gui
from p2pp.logging import error, warning, comment
from p2pp.omega import omegaheader
import p2pp.parameters as parameters


def process_tool_change(gc):
    if not gc:
        tmp = {"Layer": 999, "Tool": int(v.previous_tool), "E": v.total_extrusion}
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

    required_purge = purgetower.calc_purge_length(v.current_tool, new_tool)

    # add the amount of splice offset either as a fixed length or as a percentage of the upcoming purge
    ###################################################################################################
    if v.splice_procent:
        tmp["E"] += required_purge * v.spliceoffset / 100
    else:
        tmp["E"] += v.spliceoffset

    v.toolchange = new_tool + 1
    v.toolchangepos = tmp["E"]

    # generate the purge tower
    ##########################
    purgetower.purge_generate_sequence(required_purge / v.extrusion_multiplier) * v.extrusion_multiplier

    v.previous_tool = v.current_tool
    v.current_tool = new_tool


def process_gcode():
    gui.comment("Processing " + v.filename)
    line_count = len(v.rawfile)
    line_idx = 0
    for line in v.rawfile:
        line_idx += 1
        gui.setprogress(int(50 * line_idx / line_count))

        # skip fully empty lines
        if len(line) == 0:
            continue

        # parse comments
        if line.startswith(";"):
            line = parameters.parse_comment(line)

        tmp = gcode.GCodeCommand(line)

        # we calculate the purge for tower position
        # afterwards this code is removed
        #########################################################
        if v.mode == parameters.MODE_PURGE:
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
        if toolchange in [0, 1, 2, 3]:

            # keep track of the tools used
            if not v.toolsused[toolchange]:
                if not v.filament_type[toolchange]:
                    error("TOOL_{} setting command missing - output file cannot be created".format(toolchange))
            v.toolsused[toolchange] = True

            # calculate the purge
            if not (v.parse_curtool == -1):
                v.layer_toolchange_count[-1] += 1
                if v.filament_type[toolchange] and v.filament_type[v.parse_curtool] and not (
                        v.parse_curtool == toolchange):
                    v.layer_purge_volume[-1] += purgetower.calc_purge_length(v.parse_curtool, toolchange)
                    v.parse_prevtool = v.parse_curtool
                    v.parse_curtool = toolchange

            else:
                v.parse_curtool = v.parse_prevtool = toolchange

    comment("filament Info: " + v.filament_type.__str__())
    comment("Tool unload info: " + v.unloadinfo.__str__())
    comment("Tool load info: " + v.loadinfo.__str__())
    comment("Algorithms:" + v.algorithm.__str__())

    comment("Maximum purge needed per layer: {}mm".format(max(v.layer_purge_volume)))

    expand = 0
    tower_fits = False
    while not tower_fits:
        purgetower.purge_create_layers(v.purge_minx - 1, v.purge_miny - 1, v.purge_maxx - v.purge_minx + 2,
                                       v.purge_maxy - v.purge_miny + 2)
        tower_fits = purgetower.simulate_tower(purgetower.sequence_length_solid, purgetower.sequence_length_empty)
        if not tower_fits:
            purgetower.tower_auto_expand(10)
            expand += 10

    if expand > 0:
        warning("Tower expanded by {}mm".format(expand))

    comment('Calculated purge volume : {:.3f},{:.3f} -> {:.3f},{:.3f}'.format(v.purge_minx, v.purge_miny, v.purge_maxx,
                                                                              v.purge_maxy))

    line_idx = 0
    line_count = len(v.gcodes)
    for g in v.gcodes:
        line_idx += 1
        gui.setprogress(50 + int(50 * line_idx / line_count))
        if g.command in ["M220"]:
            g.move_to_comment("IGNORED COMMAND")
            g.issue_command()
            continue  # no further mcf required

        if g.command == "M221":
            v.extrusion_multiplier = g.get_parameter("S", v.extrusion_multiplier * 100) / 100
            g.issue_command()
            continue  # no further mcf required

        if g.command in ["T0", "T1", "T2", "T3"]:
            process_tool_change(g)
            g.issue_command()
            continue  # no further mcf required

        if g.command in ["M104", "M106", "M109", "M140", "M190", "M73", "M900", "M84"]:
            g.issue_command()
            continue  # no further mcf required

        if g.is_movement_command():
            v.current_position_x = g.get_parameter("X", v.current_position_x)
            v.current_position_y = g.get_parameter("Y", v.current_position_y)
            v.current_position_z = g.get_parameter("Z", v.current_position_z)
            if purgetower.moveintower():
                error("MODEL COLLIDES WITH TOWER.")
        g.issue_command()

    process_tool_change(None)

    if v.maxdelta > 1 or v.mindelta < -1:
        warning("Tower hight deviates {:.2f}mm above and {:.2f}mm below print level".format(-v.mindelta, v.maxdelta))
        warning("Make sure to keep enough distance between tower and object to avoid collisions")
        warning("If the tower grows over the print height, consider increasing the prime pillar width in S3D")

    gui.completed()


def save_code():
    output_file = v.filename.replace(".gcode", ".mcf.gcode")

    comment("saving output to " + output_file)

    header = omegaheader()
    comment(" number of lines: {}".format(len(header) + len(v.output_code)))

    try:
        opf = open(output_file, "w", encoding='utf-8')
    except TypeError:
        try:
            opf = open(output_file, "w")
        except IOError:
            error("Could not open output file {}".format(output_file))
            return
    except IOError:
        error("Could not read open output {}".format(output_file))
        return
    opf.writelines(header)
    opf.writelines(v.output_code)
    opf.close()
    pass


def process_file():
    parameters.create_regex_objects()
    process_gcode()
    save_code()
