__author__ = 'Tom Van den Eede'
__copyright__ = 'Copyright 2019, Palette2 Splicer Post Processing Project for Simplify 3D'
__credits__ = ['Tom Van den Eede']
__license__ = 'GPLv3'
__maintainer__ = 'Tom Van den Eede'
__email__ = 't.vandeneede@pandora.be'


import p2pp.variables as v

towergrid = []

gridsize_mm = 5


BED_UNUSED = 0
BED_PRINT  = 1

_bbx_min = 9999
_bby_min = 9999
_bbx_max = -9999
_bby_max = -9999


purge_minx = 0
purge_miny = 0
purge_maxx = 0
purge_maxy = 0


def calculate_purgevolume():

    global purge_minx, purge_miny, purge_maxx, purge_maxy

    gridXsize = len(towergrid)-2
    gridYsize = len(towergrid[0])-2

    if _bbx_min > gridXsize - _bbx_max:
        purge_minx = purge_minx + gridsize_mm * 2
        purge_maxx = min(40 , _bbx_min * gridsize_mm * 2)
    else:
        purge_maxx = v.bed_min_x + v.bed_size_x - gridsize_mm * 2
        purge_minx = purge_maxx - min(40 ,(gridXsize - _bbx_max+1)* gridsize_mm )

    if _bby_min > gridYsize - _bby_max:
        purge_miny = gridsize_mm * 2
        purge_maxy = purge_miny+ min(40 , _bby_min * gridsize_mm * 2)
    else:
        purge_maxy = v.bed_min_y + v.bed_size_y - gridsize_mm * 2
        purge_miny = purge_maxy - min(40 ,(gridYsize - _bby_max+1)* gridsize_mm)



def check_tower( x1, y1, x2, y2) :

    if x1 == 0  or y1 == 0 or x2 == len(towergrid)-1 or y2 == len(towergrid[0])-1:
        return False
    if x2 < x1:
        x1 = x2 = x1
    if  y2 < y1:
        y1 = y2 = y1
    for i in range (x1,x2+1):
        for j in range(y1, y2+1):
            if towergrid[i][j] == BED_PRINT:
                return False
    return True

def tower_expand():
    global purge_minx, purge_maxx, purge_miny, purge_maxy

    gridminx = gridpos("X", purge_minx)
    gridmaxx = gridpos("X", purge_maxx)
    gridminy = gridpos("Y", purge_miny)
    gridmaxy = gridpos("Y", purge_maxy)

    if check_tower(gridminx - 1 , gridminy  , gridmaxx, gridmaxy ):
        purge_minx -= 5
        return True

    if check_tower(gridminx , gridminy - 1 , gridmaxx, gridmaxy):
        purge_miny -= 5
        return True

    if check_tower(gridminx , gridminy  , gridmaxx  + 1, gridmaxy):
        purge_maxx += 5
        return True

    if check_tower(gridminx , gridminy  , gridmaxx , gridmaxy + 1):
        purge_maxy += 5
        return True



def gridpos( axis , value):
    if axis == "X":
        m = v.bed_min_x
        s = int(v.bed_size_x / gridsize_mm)
    else:
        m = v.bed_min_y
        s = int(v.bed_size_y / gridsize_mm)


    if value < m:
        return 0
    g = int((value-m)/gridsize_mm)
    return min(g,s)



def markgrid(x,y):

    global _bbx_min, _bbx_max, _bby_min, _bby_max

    _bbx_max = max( _bbx_max, x)
    _bbx_min = min( _bbx_min, x)
    _bby_max = max( _bby_max, y)
    _bby_min = min( _bby_min, y)

    towergrid[x][y] = BED_PRINT


def line( x0, y0, x1, y1):
    "Bresenham's line algorithm"
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    x, y = x0, y0
    sx = -1 if x0 > x1 else 1
    sy = -1 if y0 > y1 else 1
    if dx > dy:
        err = dx / 2.0
        while x != x1:
            markgrid(int(x), int(y))
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2.0
        while y != y1:
            markgrid(int(x), int(y))
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy
    markgrid(int(x), int(y))

def filament_mark (x1, y1, x2, y2):
    xx1 = gridpos("X", x1)
    yy1 = gridpos("Y", y1)
    xx2 = gridpos("X", x2)
    yy2 = gridpos("Y", y2)

    line(xx1, yy1, xx2, yy2)

def init_autotower():
    global towergrid
    sx = int(v.bed_size_x / gridsize_mm) + 1
    sy = int(v.bed_size_y / gridsize_mm) + 1
    towergrid = [[BED_UNUSED]*sy for _ in range(sx)]




