import openems
import numpy as np

def generate(
        em,
        sub,
        z, # [bottom of substrate, top of substrate, top of metal]
        port_length,
        ms_width,
        section, # pairs of x and y size of a segment
        box_width):
    box_length = 2.0*(port_length) + np.sum(section[:,0])
    pec = openems.Metal(em, 'pec')
    # substrate
    start = np.array([ 0.5*box_length, 0.5*box_width, z[0]])
    stop  = np.array([-0.5*box_length, -0.5*box_width, z[1]])
    openems.Box(sub, 1, start, stop)
    # pads
    x0 = -0.5*box_length
    x1 = x0 + port_length
    x2 = x1 + ms_width
    start = np.array([x1,  0.5*ms_width, z[1]])
    stop  = np.array([x2, -0.5*ms_width, z[2]])
    l1 = openems.Box(pec, 9, start, stop, padname = '1')
    l2 = l1.duplicate("line_p2").mirror('x')
    l2.padname = '2'
    x = x1
    points = np.zeros((2*len(section),2))
    i = 0
    for s in section:
        points[i,0] = x
        x += s[0]
        points[i+1,0] = x
        points[i,1] = 0.5*s[1]
        points[i+1,1] = 0.5*s[1]
        i += 2
    print(points)
    points = np.concatenate((points, points[::-1]*[1,-1.0]))
    print(points)
    pec.AddPolygon(
        points = points,
        priority = 9,
        elevation = z[1:],
        normal_direction = 'z',
        pcb_layer = 'F.Cu',
        pcb_width = 1e-5)

    # main line ports
    start = [x0, -0.5*ms_width, z[1]]
    stop  = [x1,  0.5*ms_width, z[2]]
    em.AddPort(start, stop, direction='x', z=50).duplicate().mirror('x')
