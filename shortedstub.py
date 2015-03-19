#!/usr/bin/env python
from scipy.constants import pi, c, epsilon_0, mu_0, mil, inch
mm = 0.001
import openems
import numpy as np

mm = 0.001
import numpy as np

def generate(em, # openems instance
             metal_name = 'pec', # metal instance, define with openems.Metal()
             z = [], # z position vector, z[0] = substrate bottom, z[1] = substrate top, z[2] = foil top
             space = None, # space between stub and coplanar ground
             width = 0.25, # width of stub
             length = 5.0, # length of stub
             priority = 9, # openems priority of all filter metal
             portlength = 0.2*mm, # length of the openems port
             feedwidth = 0.85*mm, # width of the trace leaving the filter and port
             feedgap = 0.2*mm, # space from trace leaving the filter to via ring
             via_radius = 0.15*mm, # radius of the via drills
             via_padradius = 0.3*mm, # radius of the via pads
             mask_thickness = 0, # set to non-zero to enable solder mask over filter
             inner_metal = False, # set to True to enable inner metal layers in via ring
             inner_metal_z = [[]]):
    ymin = -1.0 * (0.5*feedwidth + feedgap + 2.0*via_padradius)
    ymax = length + 2.0*via_padradius
    xmax = 0.5*width + space + 2.0*via_padradius
    # stub line
    x1 = xmax - portlength
    x2 = 0.5*width
    ppoints = np.array(
            [[     x1,  -0.5*feedwidth],
             [     x1,   0.5*feedwidth],
             [     x2,   0.5*feedwidth],
             [     x2,  ymax],
             [-1.0*x2,  ymax],
             [-1.0*x2,   0.5*feedwidth],
             [-1.0*x1,   0.5*feedwidth],
             [-1.0*x1,   -0.5*feedwidth]])
    openems.Polygon(em, name = 'stub',
                    material = metal_name,
                    priority = priority,
                    points = ppoints,
                    elevation = z[1:],
                    normal_direction = 'z',
                    pcb_layer = 'F.Cu',
                    pcb_width = 0.001*mm)
    # feed lines
    start = [x1, 0.5*feedwidth, z[1]]
    stop  = [x1 - feedwidth, - 0.5*feedwidth, z[2]]
    box2 = openems.Box(em, 'pe1', metal_name, priority, start, stop,
                       padname = '1').duplicate('pe2').mirror('x')
    box2.padname = '2'
    # ports
    start = [x1, 0.5*feedwidth, z[1]]
    stop  = [x1+portlength, -0.5*feedwidth, z[2]]
    openems.Port(em, start, stop, direction='x', z=50).duplicate().mirror('x')
    # metal ring (sides)
    start = [xmax - 2.0*via_padradius, 0.5*feedwidth + feedgap, z[1]]
    stop  = [xmax, ymax, z[2]]
    openems.Box(em, 'ring1', metal_name, priority, start, stop,
                padname = '3').duplicate('ring2').mirror('x')
    # metal ring (bottom)
    start = [xmax, length, z[1]]
    stop  = [-1.0*xmax, ymax, z[2]]
    openems.Box(em, 'ring3', metal_name, priority, start, stop,
                padname = '3')
    # metal ring (top)
    start = [xmax, -0.5*feedwidth - feedgap, z[1]]
    stop  = [-1.0*xmax, ymin, z[2]]
    box = openems.Box(em, 'ring4', metal_name, priority,
                      start, stop, padname = '3')
    # substrate
    start = np.array([-1.0*xmax, ymin, z[0]])
    stop  = np.array([     xmax, ymax, z[1]])
    openems.Box(em, 'sub1', 'sub', 1, start, stop);
    # mask
    if mask_thickness > 0.0:
            start[2] = z[1]
            stop[2] = z[1] + mask_thickness
            openems.Box(em, 'mask', 'mask', 1, start, stop);
    # vias (along y)
    via_z = [[z[0], z[2]]]#, [z[1], z[2]]]
    y_start = ymax - via_padradius
    y_stop = 0.5*feedwidth + feedgap + via_padradius
    x = xmax - via_padradius
    n_via = 0
    n_vias = 1 + np.floor(np.abs(y_start-y_stop)/(2.0*via_padradius))
    print "n vias Y = ", n_vias
    for y in np.linspace(y_start, y_stop, n_vias):
        v = openems.Via(em, 'via{}'.format(n_via), 'pec', 2, x=x, y=y, z=via_z,
                        drillradius=via_radius, padradius=via_padradius,
                        padname='3')
        v.duplicate('via{}'.format(n_via+1)).mirror('x')
        n_via += 2
    # vias (along )x
    y = y_start
    x_start = x
    x_stop = -1.0*x_start
    n_vias = 1 + np.floor(np.abs(x_start-x_stop)/(2.0*via_padradius))
    print "n vias X = ", n_vias
    for x in np.linspace(x_start, x_stop, n_vias)[1:-1]:
        v = openems.Via(em, 'via{}'.format(n_via), 'pec', 2, x=x, y=y, z=via_z,
                        drillradius=via_radius, padradius=via_padradius,
                        padname='3')
        n_via += 1
    y = ymin + via_padradius
    for x in np.linspace(x_start, x_stop, n_vias):
        v = openems.Via(em, 'via{}'.format(n_via), 'pec', 2, x=x, y=y, z=via_z,
                        drillradius=via_radius, padradius=via_padradius,
                        padname='3')
        n_via += 1
