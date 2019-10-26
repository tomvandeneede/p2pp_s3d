__author__ = 'Tom Van den Eede'
__copyright__ = 'Copyright 2019, Palette2 Splicer Post Processing Project for Simplify 3D'
__credits__ = ['Tom Van den Eede']
__license__ = 'GPLv3'
__maintainer__ = 'Tom Van den Eede'

__email__ = 't.vandeneede@pandora.be'

from p2pp.formatnumbers import hexify_short, hexify_float, hexify_long, hexify_byte
from p2pp.logging import error, warning, comment
import p2pp.variables as v


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
    for i in range(4):
        if v.toolsused[i] and v.filament_type[i] not in materials.keys():
            materials[v.filament_type[i]] = len(materials.keys())+1

    for i in range(4):
        if v.toolsused[i]:
            toolinfo[i] = "D{}000000input{}_{}".format(materials[v.filament_type[i]], i,v.filament_type[i])

    header.append('O25 {} {} {} {}'.format(toolinfo[0],toolinfo[1],toolinfo[2],toolinfo[3]) + "\n")
    header.append('O26 ' + hexify_short(len(v.toolchangeinfo)) + "\n")
    header.append('O27 ' + hexify_short(len(v.pingpositions)) + "\n")
    header.append('O28 ' + hexify_short(len(v.algooverview)) + "\n")


    previous_change = 0
    header.append('O29 ' + hexify_short(0) + "\n")

    v.processcomments.append("\n")
    v.processcomments.append(";------------------------------------\n")
    v.processcomments.append(";SPLICE INFORMATION - {} SPLICES\n".format(len(v.toolchangeinfo)))
    v.processcomments.append(";------------------------------------\n")

    previoussplice = 0
    for i in range(len(v.toolchangeinfo)):
        nextpos = v.toolchangeinfo[i]["E"]

        if previous_change==0 and nextpos < 100:
            error("First splice is {:.1f}mm too short.  Try adding brim or skirt".format(100-nextpos))
        else:
            splicelength = nextpos - previous_change
            if splicelength < 70:
                error("Short splice {} is {:.1f}mm too short. Try increasing purge".format(i+1, 70-splicelength))
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

    header.append("O1 D{} {}\n"
                  .format("_S3D_P2PP_PRINT_", hexify_long(int(v.total_extrusion + v.extra_extrusion_at_end))))
    header.append("M0\nT0\n\n")

    header = header + v.processcomments
    header.append(";--- END OF P2 HEADER ---\n")
    header.append("\n")



    return header