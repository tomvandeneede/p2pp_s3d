__author__ = 'Tom Van den Eede'
__copyright__ = 'Copyright 2018-2019, Palette2 Splicer Post Processing Project'
__credits__ = ['Tom Van den Eede',
               'Tim Brookman'
               ]
__license__ = 'GPLv3'
__maintainer__ = 'Tom Van den Eede'
__email__ = 'P2PP@pandora.be'

import p2pp.gcode as gcode
import p2pp.variables as v
import math

solidlayer = []
emptylayer = []
filllayer = []
brimlayer = []

PURGE_SOLID = 1
PURGE_EMPTY = 2

current_purge_form = PURGE_SOLID
current_purge_index = 0
purge_width = 999
purge_height = 999

sequence_length_solid = 0
sequence_length_empty = 0
sequence_length_brim = 0

last_posx = None
last_posy = None

last_brim_x = None
last_brim_y = None

ew = 0


def if_defined(x, y):
    if x:
        return x
    return y


def filament_volume_to_length(x):
    return x / (1.75 / 2 * 1.75 / 2 * math.pi)


def filament_length_to_volume(x):
    return x * (1.75 / 2 * 1.75 / 2 * math.pi)


def calculate_purge(movelength):
    volume = ew * v.layer_height * (abs(movelength) + v.layer_height)
    return filament_volume_to_length(volume)


def calc_purge_length(_from, _to):
    tmp = (v.unloadinfo[_from] + v.loadinfo[_to]) / 2
    if not tmp:
        tmp = 0
    return tmp


def moveintower():
    if v.current_position_x < v.purge_minx:
        return False
    if v.current_position_y < v.purge_miny:
        return False
    if v.current_position_x > v.purge_maxx:
        return False
    if v.current_position_y > v.purge_maxy:
        return False
    return True


def find_highest_purge(search_for, start_from_layer):
    for idx in range(start_from_layer, 0, -1):
        if v.layer_purge_structure[idx] == search_for:
            return idx
    return None


def simulate_tower(amount_solid, amount_sparse):
    purge_layer = 0
    totalpurge = 0

    ld = amount_solid - amount_sparse

    for i in range(len(v.layer_purge_structure)):
        v.layer_purge_structure[i] = 0

    v.layer_purge_structure[0] = PURGE_SOLID
    purge_layer_left = amount_solid

    for i in range(len(v.layer_purge_structure)):

        lp = v.layer_purge_volume[i]
        totalpurge += lp

        if lp > purge_layer_left:

            lp -= purge_layer_left
            purge_layer_left = 0

            # now we have a remainder of purge we still need to handle
            # we start by filling um empty layers from the bottom-up:

            while lp > 0:
                if purge_layer == i:
                    break
                purge_layer += 1
                v.layer_purge_structure[purge_layer] = PURGE_EMPTY
                if lp < amount_sparse:
                    purge_layer_left = amount_sparse - lp
                lp -= amount_sparse

            idx = True
            while lp > 0 and idx:
                idx = find_highest_purge(PURGE_EMPTY, purge_layer - 1)
                if idx:
                    v.layer_purge_structure[idx] = PURGE_SOLID
                    if lp > ld:
                        lp -= ld
                    else:
                        purge_layer_left += ld - lp
                        lp -= ld
            if lp > 0:
                return False
        else:
            purge_layer_left -= lp
        # print("Layer - {}  purge {}  - Purgelayer {} - Delta {} -  PurgeLeft {} - {} ".format(i,
        #                                                                          v.layer_purge_volume[i],
        #                                                                          purge_layer,
        #                                                                          i - purge_layer,
        #                                                                          purge_layer_left,
        #                                                                          v.layer_purge_structure[0:purge_layer]
        #        ))

    return True


def tower_auto_expand(diff):
    v.purge_minx -= diff / 2
    v.purge_maxx += diff / 2

    if v.purge_minx < v.bed_min_x:
        moveright = v.bed_min_x - v.purge_minx + 5
        v.purge_minx += moveright
        v.purge_maxx += moveright

    if v.purge_maxx > v.bed_min_x + v.bed_size_x:
        moveleft = v.bed_min_x + v.bed_size_x - v.purge_maxx - 5
        v.purge_minx += moveleft
        v.purge_maxx += moveleft


def generate_rectangle(result, x, y, w, h):
    x2 = x + w
    y2 = y + h
    result.append(gcode.GCodeCommand("G1 X{:.3f} Y{:.3f}".format(x, y)))
    result.append(gcode.GCodeCommand("G1 X{:.3f} Y{:.3f} E{:.4f}".format(x2, y, calculate_purge(w))))
    result.append(gcode.GCodeCommand("G1 X{:.3f} Y{:.3f} E{:.4f}".format(x2, y2, calculate_purge(h))))
    result.append(gcode.GCodeCommand("G1 X{:.3f} Y{:.3f} E{:.4f}".format(x, y2, calculate_purge(w))))
    result.append(gcode.GCodeCommand("G1 X{:.3f} Y{:.3f} E{:.4f}".format(x, y, calculate_purge(h))))

    result.append(gcode.GCodeCommand("G1 X{:.3f} Y{:.3f}".format(x + ew, y + ew)))
    result.append(gcode.GCodeCommand("G1 X{:.3f} Y{:.3f} E{:.4f}".format(x2 - ew, y + ew, calculate_purge(w - 2 * ew))))
    result.append(
        gcode.GCodeCommand("G1 X{:.3f} Y{:.3f} E{:.4f}".format(x2 - ew, y2 - ew, calculate_purge(h - 2 * ew))))
    result.append(gcode.GCodeCommand("G1 X{:.3f} Y{:.3f} E{:.4f}".format(x + ew, y2 - ew, calculate_purge(w - 2 * ew))))
    result.append(gcode.GCodeCommand("G1 X{:.3f} Y{:.3f} E{:.4f}".format(x + ew, y + ew, calculate_purge(h - 2 * ew))))


def _purge_calculate_sequences_length():
    global sequence_length_solid, sequence_length_empty, sequence_length_brim

    sequence_length_solid = 0
    sequence_length_empty = 0
    sequence_length_brim = 0

    for i in solidlayer:
        if i.E:
            sequence_length_solid += i.E

    for i in emptylayer:
        if i.E:
            sequence_length_empty += i.E

    for i in brimlayer:
        if i.E:
            sequence_length_brim += i.E


def _calculate_filling_box(x, y, w, h):
    _x = x + 2 * ew
    _y = y + 2 * ew
    _w = w - 4 * ew
    _h = h - 4 * ew
    return _x, _y, _x + _w, y + _h, _w, _h


def _purge_create_sequence(code, main_axis, x, y, w, h, step1):
    cw = w - 4 * ew
    ch = h - 4 * ew

    offset_x = x + 2 * ew
    offset_y = y + 2 * ew

    start1 = offset_x - ew * 0.15
    end1 = offset_x + cw + ew * 0.15

    start2 = offset_y - ew * 0.15
    end2 = offset_y + ch + ew * 0.15

    if main_axis == "Y":
        # start1, end1, start2, end2 = start2, end2, start1, end1
        short_axis = "X"
        code.append(gcode.GCodeCommand("G1 X{:.3f} Y{:.3f}".format(start2, start1)))
    else:
        short_axis = "Y"
        code.append(gcode.GCodeCommand("G1 X{:.3f} Y{:.3f}".format(start1, start2)))

    stroke_length = abs(end2 - start2)

    stroke_num = False

    while start1 < end1:
        stroke_num = not stroke_num
        stroke = min(end1 - start1, step1)
        start1 = start1 + stroke
        if stroke_num:
            code.append(
                gcode.GCodeCommand("G1 {}{:.3f} E{:.4f}".format(short_axis, end2, calculate_purge(stroke_length))))
        else:
            code.append(
                gcode.GCodeCommand("G1 {}{:.3f} E{:.4f}".format(short_axis, start2, calculate_purge(stroke_length))))

        code.append(gcode.GCodeCommand("G1 {}{:.3f} E{:.4f}".format(main_axis, start1, calculate_purge(stroke))))


def dist(x1, y1, x2, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def clipline(slope, left, bottom, right, top, startx):
    func_x = lambda y: slope * (y - bottom) + startx
    func_y = lambda x: (x - startx) / slope + bottom
    func_inrange = lambda x, y: (left <= x) and (x <= right) and (bottom <= y) and (y <= top)

    rx = [func_x(bottom), func_x(top), left, right]
    ry = [bottom, top, func_y(left), func_y(right)]

    for i in range(3, -1, -1):
        if not func_inrange(rx[i], ry[i]):
            del rx[i]
            del ry[i]

    if (len(rx) == 2) and (len(ry) == 2):
        return [[rx[0], ry[0]], [rx[1], ry[1]]]


def _generate_hatch(code, slope, x1, y1, x2, y2, infill):
    assert infill > 0, "Infill must be >0"
    assert abs(slope) == 1, "Slope value must be -1 or 1"

    step = 100 / infill * ew

    if slope > 0:
        last_x = x1
        last_y = y1
        start_x = x1 - (y2 - y1) + step
        endx = x2
    else:
        last_x = x1
        last_y = y1
        start_x = x1 + step
        endx = x2 + (y2 - y1) - step

    index = 0

    code.append(gcode.GCodeCommand("G1 X{:3f} Y{:.3f}".format(last_x, last_y)))

    while start_x < endx:
        next_points = clipline(slope, x1, y1, x2, y2, start_x)

        start_x = start_x + step
        if next_points:
            if dist(last_x, last_y, next_points[index][0], next_points[index][1]) > dist(last_x, last_y,
                                                                                         next_points[1 - index][0],
                                                                                         next_points[1 - index][1]):
                index = 1 - index

                code.append(
                    gcode.GCodeCommand("G1 X{:3f} Y{:.3f} E{:.4f}".format(next_points[index][0], next_points[index][1],
                                                                          dist(last_x, last_y, next_points[index][0],
                                                                               next_points[index][1]))))
                last_x = next_points[index][0]
                last_y = next_points[index][1]
                index = 1 - index
                code.append(
                    gcode.GCodeCommand("G1 X{:3f} Y{:.3f} E{:.4f}".format(next_points[index][0], next_points[index][1],
                                                                          dist(last_x, last_y, next_points[index][0],
                                                                               next_points[index][1]))))
                last_x = next_points[index][0]
                last_y = next_points[index][1]


def purge_create_layers(x, y, w, h):
    global solidlayer, emptylayer, filllayer, ew

    solidlayer = []
    emptylayer = []
    filllayer = []

    ew = v.extrusion_width

    w = int(w / ew) * ew
    h = int(h / ew) * ew

    solidlayer.append(gcode.GCodeCommand(";---- SOLID WIPE -------"))
    generate_rectangle(solidlayer, x, y, w, h)

    emptylayer.append(gcode.GCodeCommand(";---- EMPTY WIPE -------"))
    generate_rectangle(emptylayer, x, y, w, h)

    filllayer.append(gcode.GCodeCommand(";---- FILL LAYER -------"))
    generate_rectangle(filllayer, x, y, w, h)

    _purge_create_sequence(solidlayer, "X", x, y, w, h, ew)
    _purge_create_sequence(emptylayer, "Y", y, x, h, w, 2)
    _purge_create_sequence(filllayer, "Y", y, x, h, w, 15)

    _purge_generate_tower_brim(x, y, w, h)

    _purge_calculate_sequences_length()


def _purge_number_of_gcodelines():
    if current_purge_form == PURGE_SOLID:
        return len(solidlayer)
    else:
        return len(emptylayer)


def _purge_update_sequence_index(purgelength):
    global current_purge_form, current_purge_index
    global lastpos_x, lastpos_y

    current_purge_index = (current_purge_index + 1) % _purge_number_of_gcodelines()

    if current_purge_index == 0:
        v.purgelayer += 1
        if v.purgelayer > len(v.layer_purge_structure):
            current_purge_form = PURGE_SOLID
        else:
            current_purge_form = v.layer_purge_structure[v.purgelayer - 1]

        lastpos_x = float(v.purge_minx)
        lastpos_y = float(v.purge_miny)

        if purgelength > 0:
            v.output_code.append("G1 Z{:.2f} F10800\n".format(v.purgelayer * v.layer_height))
            if v.purgelayer == 1:
                v.output_code.append("G1 F{}\n".format(v.wipe_feedrate1))
            else:
                v.output_code.append("G1 F{}\n".format(v.wipe_feedrate))


def _purge_get_nextcommand_in_sequence():
    if current_purge_form == PURGE_SOLID:
        return solidlayer[current_purge_index]
    else:
        return emptylayer[current_purge_index]


def _purge_generate_tower_brim(x, y, w, h):
    global brimlayer, last_brim_x, last_brim_y

    brimlayer = []
    y -= ew
    w += ew
    h += 2 * ew

    brimlayer.append(gcode.GCodeCommand("G0 X{:.3f} Y{:.3f} F4000".format(x, y)))
    brimlayer.append(gcode.GCodeCommand("G0 Z{:.3f}".format(v.layer_height)))

    for i in range(4):
        brimlayer.append(gcode.GCodeCommand("G1 X{:.3f} Y{:.3f}  E{:.4f} F{}".format(x + w, y, calculate_purge(w), v.wipe_feedrate1)))
        brimlayer.append(gcode.GCodeCommand("G1 X{:.3f} Y{:.3f}  E{:.4f}".format(x + w, y + h, calculate_purge(h))))
        x -= ew
        w += 2 * ew
        brimlayer.append(gcode.GCodeCommand("G1 X{:.3f} Y{:.3f}  E{:.4f}".format(x, y + h, calculate_purge(w))))
        y -= ew
        h += 2 * ew
        brimlayer.append(gcode.GCodeCommand("G1 X{:.3f} Y{:.3f}  E{:.4f}".format(x, y, calculate_purge(h))))

    last_brim_x = x
    last_brim_y = y


tmp_pos_x = 0
tmp_pos_y = 0
tmpe = 0
intermediate = False


def purge_generate_sequence(purgelength):
    global last_posx, last_posy, tmp_pos_x, tmp_pos_y, intermediate, tmpe

    if not purgelength > 0:
        return 0

    keep_x = v.current_position_x
    keep_y = v.current_position_y

    actual = 0

    p_delta = v.current_position_z - v.purgelayer * v.layer_height

    v.output_code.append("; --------------------------------------------------\n")
    v.output_code.append("; --- P2PP WIPE SEQUENCE START  FOR {:5.2f}mm\n".format(purgelength))
    v.output_code.append("; --- DELTA = {:.2f}\n".format(p_delta))
    v.output_code.append("; --------------------------------------------------\n")

    v.maxdelta = max(v.maxdelta, p_delta)
    v.mindelta = min(v.mindelta, p_delta)

    if not last_posx:
        last_posx = float(v.purge_minx)
    if not last_posy:
        last_posy = float(v.purge_miny)

    v.output_code.append("G1 X{:.3f} Y{:.3f} F{}\n".format(last_posx, last_posy, v.wipe_feedrate))
    v.output_code.append("G1 Z{:.2f} F10800\n".format(v.purgelayer * v.layer_height))
    if v.purgelayer == 1:
        v.output_code.append("G1 F{}\n".format(v.wipe_feedrate1))
    else:
        v.output_code.append("G1 F{}\n".format(v.wipe_feedrate))

    # generate wipe code
    while purgelength > 1:

        if not intermediate:

            next_command = _purge_get_nextcommand_in_sequence()

            while not next_command.E or not next_command.E > 0:
                next_command.issue_command()
                _purge_update_sequence_index(purgelength)
                next_command = _purge_get_nextcommand_in_sequence()
        else:
            next_command = gcode.GCodeCommand(
                "G1 X{:.3f} Y{:.3f} E{:.4f} ;inter resume ".format(tmp_pos_x, tmp_pos_y, tmpe))

        intermediate = False

        if float(next_command.E) > (purgelength + 1):

            tmp_pos_x = float(if_defined(next_command.X, last_posx))
            tmp_pos_y = float(if_defined(next_command.Y, last_posy))

            last_posx = last_posx + (tmp_pos_x - last_posx) * (purgelength / float(next_command.E))
            last_posy = last_posy + (tmp_pos_y - last_posy) * (purgelength / float(next_command.E))
            tmpe = float(next_command.E) - purgelength
            intermediate = True
            actual += purgelength

            gcode.GCodeCommand(
                "G1 X{:.3f} Y{:.3f} E{:.4f}   ;inter {:.3f} {:.3f}".format(last_posx, last_posy, purgelength, tmp_pos_x,
                                                                           tmp_pos_y)).issue_command()
            purgelength = 0

        else:
            last_posx = if_defined(next_command.X, last_posx)
            last_posy = if_defined(next_command.Y, last_posy)
            purgelength -= if_defined(next_command.E, 0)
            actual += if_defined(next_command.E, 0)
            next_command.issue_command()

        if not intermediate:
            _purge_update_sequence_index(purgelength)

        # if v.toolchange > 0 and v.total_extrusion >= v.toolchangepos:
        #     gcode.GCodeCommand( "; process Input {}".format(v.toolchange)).issue_command()
        #     v.toolchange = 0

    # return to print height
    v.output_code.append("; -------------------------------------\n")
    v.output_code.append("G1 Z{:.2f} F10800\n".format(v.current_position_z + 0.4))
    v.output_code.append("G0 X{:.3f} Y{:.3f} F{}\n".format(keep_x, keep_y, v.wipe_feedrate))
    v.output_code.append("; --- P2PP WIPE SEQUENCE END DONE\n")
    v.output_code.append("; -------------------------------------\n")

    # if we extruded more we need to account for that in the total count

    return actual
