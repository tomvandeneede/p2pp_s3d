__author__ = 'Tom Van den Eede'
__copyright__ = 'Copyright 2019, Palette2 Splicer Post Processing Project for Simplify 3D'
__credits__ = ['Tom Van den Eede']
__license__ = 'GPLv3'
__maintainer__ = 'Tom Van den Eede'

__email__ = 't.vandeneede@pandora.be'

from p2pp.logging import error, comment
import p2pp.variables as v
import re
import p2pp.gui as gui

MODE_START = 0
MODE_INFILL = 1
MODE_PERIMETER = 2
MODE_OTHER = 3
MODE_PURGE = 4


def create_regex_objects():
    v.regex_layer = re.compile("^; layer (\d+), Z = (\d+\.\d+)")
    v.regex_p2pp = re.compile("^;\s*P2PP\s+([^=]+)=?(.*)$")
    v.regex_layer_height = re.compile("^;\s*layerHeight,(\d+\.\d+)")
    v.regex_extrusion_width = re.compile("^;\s*extruderWidth,(\d+\.\d+)")
    v.regex_use_prime_pillar = re.compile("^;\s*usePrimePillar,(\d)")
    v.regex_purge_info = re.compile("(\w+):\[\s*(\d+)\s*;\s*(\d+)\s*\]")
    v.regex_bed_size = re.compile("^;\s*stroke([X|Y])override,(-?\d+)")
    v.regex_bed_origin = re.compile("^;\s*originOffset([X|Y])override,(-?\d+)")
    v.regex_primepillar = re.compile("^;\s*primePillarLocation,(-?\d+)")
    v.regex_tower_width = re.compile("^;\s*primePillarWidth,(-?\d+)")
    v.regex_process = re.compile("^;\s*process Input\s*\d")


def parse_comment(line):
    m = v.regex_layer.match(line)
    if m:
        v.process_layer = int(m.group(1))
        v.process_layer_z = float(m.group(2))
        v.layer_toolchange_count.append(0)
        v.layer_purge_volume.append(0.0)
        v.layer_purge_structure.append(0)

    m = v.regex_p2pp.match(line)
    if m:
        p2pp_command(m.group(1), m.group(2))

    m = v.regex_bed_size.match(line)
    if m:
        if m.group(1) == "X":
            v.bed_size_x = int(m.group(2))
        else:
            v.bed_size_y = int(m.group(2))

    m = v.regex_bed_origin.match(line)
    if m:
        if m.group(1) == "X":
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

    # if line.startswith("; process Input"):
    #     return("; ---pr0cess input removed----")

    return line


def p2pp_command(command, parameter):
    command = command.upper()

    if command == "LINEARPINGLENGTH":
        v.pinglength = float(parameter)
        v.pingincrease = 1

    if command == "WIPESPEED":
        v.wipe_feedrate = int(parameter)

    if command == "LAYERONEWIPESPEED"
        v.wipe_feedrate1 = int(parameter)


    if command == "TOWERDELTA":
        v.towerdelta = float(parameter)

    if command == "PRINTERPROFILE":
        v.printerid = parameter
        gui.set_printer_id(v.printerid)

    if command == "EXTRAENDFILAMENT":
        v.extra_extrusion_at_end = float(parameter)

    if command == "SPLICEOFFSET":
        unit = "mm"
        if parameter.endswith("%"):
            parameter = parameter.replace("%", "")
            v.splice_procent = True
            unit = "% of purge length"
        v.spliceoffset = float(parameter)

        comment("Splice offset is {}{}.".format(v.spliceoffset, unit))

    if command == "AUTOEXPANDTOWER":
        v.expand_tower = True

    if command in ["TOOL_0", "TOOL_1", "TOOL_2", "TOOL_3"]:
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
            m = re.search(_deflt, command)
            if m:
                v.algorithm["DEFAULT"] = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
