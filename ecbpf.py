mm = 0.001
import numpy as np
import openems

def ecbpf(em, rl, rw, space, feedwidth, portlength, z, ms50w = 0.5*mm):
    rl_max = np.max(rl)
    # finger 2
    x = 0.5*rl_max
    y = 0.5*space[2]
    start = [x - rl[2], y, z[1]];
    y += rw[2]
    stop  = [x + rl[2], y, z[2]];
    openems.Box(em, 'r2', 'pec', 9, start, stop).duplicate('r2m').mirror('xy')
    # finger 1
    x += rl_max
    y += space[1]
    start = [x - rl[1], y, z[1]];
    y += rw[1]
    stop  = [x + rl[1], y, z[2]];
    openems.Box(em, 'r1', 'pec', 9, start, stop).duplicate('r1m').mirror('xy')
    # finger 0 (half length coupling)
    x += rl_max
    y += space[0]
    start = [x - rl[0], y, z[1]];
    stop  = [x, y+rw[0], z[2]];
    openems.Box(em, 'r0', 'pec', 9, start, stop).duplicate().mirror('xy')
    # ports ext
    start = [x, y, z[1]];
    stop  = [x + rw[0], y+rw[0], z[2]];
    openems.Box(em, 'pext', 'pec', 9, start, stop).duplicate().mirror('xy')
    # ports ext
    x += rw[0]
    start = [x, y+rw[0], z[1]];
    stop  = [x + 0.5*mm, y+rw[0]-ms50w, z[2]];
    openems.Box(em, 'pext2', 'pec', 9, start, stop).duplicate().mirror('xy')
    x += 0.5*mm
    # ports
    start = [x, y+rw[0], z[1]];
    stop  = [x+0.2*mm, y+rw[0]-ms50w, z[2]];
    openems.Port(em, start, stop, direction='x', z=50).duplicate().mirror('xy')
    x += 0.2*mm
    y += 0.5*mm

    y += 0.25*mm
    # substrate
    start = [x, y,  z[0]]
    stop  = [-x, -y, z[1]]
    sub = openems.Box(em, None, 'sub', 1, start, stop);
