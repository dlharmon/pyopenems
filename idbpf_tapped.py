mm = 0.001
import openems
import numpy as np

def idbpf(em, # openems instance
          sub, # substrate, define with openems.Dielectric()
          lidz = 0.0,
          z = [], # z position, z[0] = sub bottom, z[1] = sub top, z[2] = foil top
          space = [], # space between resonator fingers
          rl = [], # length of resonator fingers
          rw = [], # width of resonator fingers
          portlength = 0.2*mm, # length of the openems port
          feedwidth = 0.85*mm, # width of the trace leaving the filter and port
          tapoffset = 1.0*mm, # offset of tap from end of resonator
          end_gap = 0.3*mm, # space between the end of a resonator and ground
          via_radius = 0.15*mm, # radius of the via drills
          via_padradius = 0.3*mm, # radius of the via pads
          pcb_layer = 'F.Cu', # Kicad layer
          mask_thickness = 0, # set to non-zero to enable solder mask over filter
          mask = None, # mask, define with openems.Dielectric()
          endmetal = True, # add metal to filter ends
):
    pec = openems.Metal(em, 'pec_filter')
    ring_y_width = via_padradius * 2.0
    ring_ix = 0.5 * (np.max(rl) + end_gap)
    ring_ox = ring_ix + 2.0 * via_padradius
    via_z = [[z[0], z[1]+lidz], [z[1], z[2]]]
    # fingers
    y = -0.5*space[-1:][0]
    mirror = np.array([1,1,1])
    if len(space) % 2 == 0:
        mirror[0] *= -1
    for i in range(len(space))[::-1]: # reverse order
        x1 = 0.5 * (ring_ox + ring_ix)
        x2 = ring_ix - rl[i]
        y += space[i]
        start = [x1, y, z[1]];
        y += rw[i]
        stop  = [x2, y, z[2]];
        for m in [np.array([1,1,1]),np.array([-1,-1,1])]:
            m *= mirror
            openems.Box(pec, 9, start*m, stop*m, padname = 'poly', pcb_layer=pcb_layer)
            openems.Via(pec, priority=2,
                        x=m[0]*(ring_ix+via_padradius),
                        y=m[1]*(y-0.5*rw[i]),
                        z=via_z,
                        drillradius=via_radius,
                        padradius=via_padradius, padname='2')
        mirror[0] *= -1

        if endmetal:
            v.duplicate().mirror('y')
            v.duplicate().mirror('x')

    mirror *= [-1,1,1]
    # ports
    y1 = y
    y -= 0.5*rw[0] # center of line
    y2 = y + 0.5*feedwidth + ring_y_width # y outside
    px = ring_ix - tapoffset
    py = y2 - portlength
    for m in [-1,1]:
        start = [m*(px + 0.5*feedwidth), m*y2, z[1]]
        stop  = [m*(px - 0.5*feedwidth), m*py, z[2]]
        openems.Port(em, start, stop, direction='y', z=50)
        # feed lines
        start = [m*(px + 0.5*feedwidth), m*py, z[1]]
        stop  = [m*(px - 0.5*feedwidth), m*(y-0.5*rw[0]), z[2]]
        openems.Box(pec, 9, start, stop, padname = '1' if m==1 else '3',
                    pcb_layer=pcb_layer)
    # substrate
    start = np.array([ring_ox, y2, z[0]])
    stop  = openems.mirror(start, 'xy')
    stop[2] = z[1]+lidz
    sub = openems.Box(sub, 1, start, stop)
    # mask
    if mask_thickness > 0.0:
        start = np.array([ring_ox, y2, z[1]])
        stop  = openems.mirror(start, 'xy')
        stop[2] += mask_thickness
        openems.Box(mask, 1, start, stop)
    # grounded end metal
    if endmetal:
        for xm in [-1,1]:
            em1 = openems.Box(pec, 9, start = [xm*ring_ix, y2, z[1]],
                              stop = [xm*(ring_ix + 2.0*via_padradius), -y2, z[2]],
                              padname = '2', pcb_layer=pcb_layer)
