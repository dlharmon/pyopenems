mm = 0.001
from openems import OpenEMS, Box, Cylinder, Via, Port, Metal, Dielectric, geometries, mirror
import numpy as np

def idbpf(
    em, # openems instance
    sub, # substrate, define with Dielectric()
    z = [], # z position, z[0] = sub bottom, z[1] = sub top, z[2] = foil top
    lidz = 0, # upper substrate thickness
    rl = [], # length of resonator fingers
    rw = [], # width of resonator fingers
    space = [], # space between resonator fingers
    endmetal = True, # add metal to filter ends
    portlength = 0.2*mm, # length of the openems port
    feedwidth = 0.85*mm, # width of the trace leaving the filter and port
    end_gap = 0.3*mm, # space between the end of a resonator and ground
    via_radius = 0.15*mm, # radius of the via drills
    via_padradius = 0.3*mm, # radius of the via pads
    pcb_layer = 'F.Cu', # Kicad layer
    mask = None, # mask, define with Dielectric()
    mask_thickness = 0, # set to non-zero to enable solder mask over filter
):
    edge_space = 0.5*mm
    pec = Metal(em, 'pec_filter')
    ring_ix = 0.5 * (np.max(rl) + end_gap)
    ring_ox = ring_ix + 2.0 * via_padradius
    via_z = [[z[0], z[1]+lidz], [z[1], z[2]]]
    # fingers
    y = -0.5*space[-1:][0]
    mirror = False
    mirrorstring = ['', 'x']
    for i in range(len(space))[::-1]: # reverse order
        x1 = 0.5 * (ring_ox + ring_ix)
        x2 = ring_ix - rl[i]
        y += space[i]
        start = [x1, y, z[1]];
        y += rw[i]
        stop  = [x2, y, z[2]];
        box = Box(pec, 9, start, stop, padname = 'poly', pcb_layer=pcb_layer)
        box.mirror(mirrorstring[mirror])
        mirror = not mirror
        box2 = box.duplicate()
        box2.mirror('xy')
        if i == 0:
            continue
        v = Via(
            pec, priority=2,
            x=ring_ix+via_padradius,
            y=y-0.5*rw[i], z=via_z,
            drillradius=via_radius,
            padradius=via_padradius, padname='2')
        if not mirror:
            v.mirror('x')
        v.duplicate().mirror('xy')
    mirror = not mirror
    # ports
    y1 = y + feedwidth - rw[0] # outer edge of feed
    y2 = y - rw[0] # inner edge
    px = ring_ox
    start = [px, y2, z[1]]
    stop  = [px - portlength, y1, z[2]]
    p = Port(em, start, stop, direction='x', z=50)
    p.mirror(mirrorstring[mirror])
    p2 = p.duplicate().mirror('xy')
    # feed lines
    start = [-ring_ix + rl[0], y1, z[1]]
    stop  = [px - portlength, y2, z[2]]
    box = Box(pec, 9, start, stop, padname = '1', pcb_layer=pcb_layer)
    box.mirror(mirrorstring[mirror])
    box2 = box.duplicate()
    box2.mirror('xy')
    box2.padname = '3'
    # substrate
    start = np.array([ring_ox, y1 + edge_space, z[0]])
    stop  = mirror(start, 'xy')
    stop[2] = z[1]+lidz
    sub = Box(sub, 1, start, stop)
    # mask
    if mask_thickness > 0.0:
        start = np.array([ring_ox, y2, z[1]])
        stop  = mirror(start, 'xy')
        stop[2] += mask_thickness
        Box(mask, 1, start, stop)
    # grounded end metal
    if endmetal:
        for m in ['', 'xy']:
            Box(pec, 9,
                start = [ring_ix, -y2+space[0], z[1]],
                stop = [ring_ix + 2.0*via_padradius, y1+edge_space, z[2]],
                padname = '2', pcb_layer=pcb_layer,
                mirror=m)
