import openems
import numpy as np

def generate(sub,
             metal,
             z,
             coupler_length,
             coupler_width,
             coupler_gap,
             ms_width,
             port_length,
             pin_length,
             box_length,
             box_y,
             feed_coupled=False,
             dual=False,
             sub_top = 0.0,
             priority=9):
    em = sub.em
    # substrate
    start = np.array([ 0.5*box_length, box_y[0], z[0]])
    stop  = np.array([-0.5*box_length, box_y[1], z[1]+sub_top])
    sub.AddBox(start, stop, 1)
    # through line ends (pads)
    x0 = -0.5*box_length
    x1 = x0 + port_length
    start = np.array([x1, 0.5*ms_width, z[1]])
    stop  = np.array([x1 + pin_length, -0.5*ms_width, z[2]])
    l1 = metal.AddBox(start, stop, priority, padname = '1')
    l2 = l1.duplicate("line_p2")
    l2.mirror('x')
    l2.padname = '2'
    xc1 = -0.5*coupler_length - 0.5*ms_width
    xc2 = xc1 + ms_width
    # through line middle
    ppoints = np.array(
        [[     x1,  0.5*ms_width],
         [-1.0*x1,  0.5*ms_width],
         [-1.0*x1, -0.5*ms_width],
         [     x1,  -0.5*ms_width]])
    em.mesh.AddLine('y', -0.5*ms_width)
    metal.AddPolygon(priority = priority, points = ppoints, elevation = z[1:],
                     normal_direction = 'z',
                     pcb_layer = 'F.Cu',
                     pcb_width = 1e-6)
    # coupled line
    yc0 = 0.5*ms_width + coupler_gap
    yc1 = yc0 + coupler_width
    yc4 = box_y[1]
    yc3 = yc4 - port_length
    yc2 = yc3 - pin_length
    # pads
    start = np.array([xc1, yc2, z[1]])
    stop  = np.array([xc2, yc3, z[2]])
    l3 = metal.AddBox(start, stop, priority=priority, padname = '3')
    l4 = l3.duplicate("line_p4").mirror('x')
    l4.padname = '4'
    if dual:
        l5 = l3.duplicate().mirror('y')
        l5.padname = '5'
        l6 = l4.duplicate().mirror('y')
        l6.padname = '6'

    em.mesh.AddLine('y', yc0)
    em.mesh.AddLine('y', yc1)
    lcx = np.linspace(xc1,-xc1,10)
    xi = np.abs(np.linspace(0 ,1,10))
    lcy = yc0 + xi * 0.2e-3 + xi*xi * 0.1e-3 + xi*xi*xi * 0.2e-3
    lowercoupled = np.array((lcx, lcy)).swapaxes(0,1)[::-1]
    ucx = np.linspace(xc2,-xc2,10)
    ucy = yc1 + xi * 0.2e-3 + xi*xi * 0.1e-3 + xi*xi*xi * 0.2e-3
    uppercoupled = np.array((ucx, ucy)).swapaxes(0,1)
    p = metal.AddPolygon(
        priority = priority,
        points = np.concatenate((
            lowercoupled,
            np.array([
                [xc1, yc3],
                [xc2, yc3]]),
            uppercoupled,
            np.array([
                [-1.0*xc2, yc3],
                [-1.0*xc1, yc3]]))),
        elevation = z[1:],
        normal_direction = 'z',
        pcb_layer = 'F.Cu',
        pcb_width = 1e-6)

    if dual:
        p.duplicate().mirror('y')

    if not feed_coupled:
        # main line ports
        start = [x0, -0.5*ms_width, z[1]]
        stop  = [x1,  0.5*ms_width, z[2]]
        openems.Port(em, start, stop, direction='x', z=50).duplicate().mirror('x')
    # coupled line ports
    start = [xc1, yc4, z[1]]
    stop  = [xc2, yc3, z[2]]
    cp1 = openems.Port(em, start, stop, direction='y', z=50)
    cp2 = cp1.duplicate().mirror('x')
    if dual:
        cp1.duplicate().mirror('y')
        cp2.duplicate().mirror('y')

    if feed_coupled:
        # main line ports
        start = [x0, -0.5*ms_width, z[1]]
        stop  = [x1,  0.5*ms_width, z[2]]
        openems.Port(em, start, stop, direction='x', z=50).duplicate().mirror('x')
