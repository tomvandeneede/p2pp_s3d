__author__ = 'Tom Van den Eede'
__copyright__ = 'Copyright 2019, Palette2 Splicer Post Processing Project for Simplify 3D'
__credits__ = ['Tom Van den Eede']
__license__ = 'GPLv3'
__maintainer__ = 'Tom Van den Eede'
__email__ = 't.vandeneede@pandora.be'

import p2pp.variables as v
from p2pp.formatnumbers import hexify_float

RELATIVE = True
ABSOLUTE = False

_tool = 0

class GCodeCommand:

    command = None
    parameters = {}
    comment = None
    flags = []
    layer = 0
    layerz = 0
    tool =  0
    codesection = None
    X = None
    Y = None
    Z = None
    E = None

    def __init__(self, gcode_line):
        global _tool
        self.command = None
        self.parameters = {}
        self.comment = None
        gcode_line = gcode_line.strip()
        pos = gcode_line.find(";")
        if pos != -1:
            self.comment = gcode_line[pos + 1:]
            gcode_line = (gcode_line.split(';')[0]).strip()

        fields = gcode_line.split(' ')

        if len(fields[0]) > 0:
            self.command = fields[0]
            fields = fields[1:]
            if self.command[0] == "T":
                _tool = int(self.command[1:])

            while len(fields) > 0:
                param = fields[0].strip()
                if len(param) > 0:
                    par = param[0]
                    val = param[1:]

                    try:
                        if "." in val:
                            val = float(val)
                        else:
                            val = int(val)
                    except ValueError:
                        pass

                    self.parameters[par] = val

                fields = fields[1:]

        self.tool = _tool
        self.X = self.get_parameter("X", None)
        self.Y = self.get_parameter("Y", None)
        self.Z = self.get_parameter("Z", None)
        self.E = self.get_parameter("E", None)
        self.codesection = v.mode
        self.layer = v.process_layer
        self.layerz = v.process_layer_z

    def __str__(self):
        p = ""
        for key in self.parameters:
            p = p + "{}{} ".format(key, self.parameters[key])

        c = self.command
        if not c:
            c = ""

        if not self.comment:
            co = ""
        else:
            co = ";" + self.comment

        return ("{} {} {}".format(c, p, co)).strip() + "\n"


    def update_parameter(self, parameter, value):
        self.parameters[parameter] = value


    def remove_parameter(self, parameter):
        if parameter in self.parameters:
            self.parameters.pop(parameter)


    def move_to_comment(self, text):
        if self.command:
            self.comment = "-- P2PP/S3D -- removed [{}] - {}".format(text, self)

        self.command = None
        self.parameters.clear()


    def has_parameter(self, parametername):
        return parametername in self.parameters


    def get_parameter(self, parm, defaultvalue=0):
        if self.has_parameter(parm):
            return self.parameters[parm]
        return defaultvalue


    def issue_command(self):
        v.output_code.append(self.__str__())
        if self.E and self.is_movement_command():

            # perform ping checks
            v.total_extrusion += self.E * v.extrusion_multiplier
            if v.total_extrusion - v.lastping >= v.pinglength:
                v.pingpositions.append(v.total_extrusion)
                v.output_code.append(";----------------------------------\n")
                v.output_code.append(
                    "; P2 PING {} COMMAND AT {:.3f}mm\n".format(len(v.pingpositions), v.total_extrusion))
                v.output_code.append("O31 {}\n".format(hexify_float(v.total_extrusion)))
                v.output_code.append(";----------------------------------\n")
                v.lastping = v.total_extrusion
                v.pinglength *= v.pingincrease


    def add_comment(self, text):
        if self.comment:
            self.comment += text
        else:
            self.comment = text


    def is_comment(self):
        return self.command == None and not (self.comment == None)


    def is_toolchange(self):
        if self.command and self.command[0] == 'T':
            return int(self.command[1])
        return None


    def is_movement_command(self):
        return self.command in ['G0', 'G1', 'G2', 'G3', 'G5']
