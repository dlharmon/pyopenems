import openems
import numpy as np

def generate(sub, metal, z,
             coupler_length, miter, coupler_width, coupler_gap,
             ms_width, port_length, pin_length, box_length, box_y, main_line_width=None,
             cpw_gap=None, feed_coupled=False, dual=False, priority=9):
    if main_line_width == None:
        main_line_width = coupler_width
    em = sub.em
    # substrate
    start = np.array([ 0.5*box_length, box_y[0], z[0]])
    stop  = np.array([-0.5*box_length, box_y[1], z[1]])
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
    xm = xc1 + miter
    # through line middle
    diff = 0.5 * np.abs(ms_width - main_line_width)
    ppoints = np.array(
        [[     x1,  0.5*ms_width],
         [-1.0*x1,  0.5*ms_width],
         [-1.0*x1, -0.5*ms_width],
         [-1.0*xm + diff, -0.5*ms_width],
         [-1.0*xm - diff,  0.5*ms_width - main_line_width],
         [ 1.0*xm + diff,  0.5*ms_width - main_line_width],
         [     xm - diff, -0.5*ms_width],
         [     x1,  -0.5*ms_width]])
    em.mesh.AddLine('y', 0.5*ms_width - main_line_width)
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
    p = metal.AddPolygon(
        priority = priority,
        points = np.array([[xc1 + miter,  yc0],
                           [xc1, yc0 + miter],
                           [xc1, yc3],
                           [xc2, yc3],
                           [xc2, yc1],
                           [-1.0*xc2, yc1],
                           [-1.0*xc2, yc3],
                           [-1.0*xc1, yc3],
                           [-1.0*xc1, yc0 + miter],
                           [-1.0*xc1 - miter, yc0]]),
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
    # ground via
    if cpw_gap != None:
        start = np.array([-0.5*box_length, -0.5*ms_width - cpw_gap, z[0]])
        stop  = np.array([ 0.5*box_length, box_y[0], z[2]])
        metal.AddBox(start, stop, priority, padname = None)
        start = np.array([-0.5*box_length, 0.5*ms_width + cpw_gap, z[0]])
        stop  = np.array([xc1 - cpw_gap, box_y[1], z[2]])
        metal.AddBox(start, stop, padname = None, priority = priority).duplicate().mirror('x')
