mm = 0.001
import openems
import numpy as np
pi = np.pi
cat = np.concatenate

def arc(x, y, r, a0, a1):
    angles = np.linspace(a0,a1,32)
    return r*np.exp(1j*angles) + x + 1j*y

def complex_to_xy(a):
    rv = np.zeros((len(a),2))
    for i in range(len(a)):
        rv[i][0] = a[i].real
        rv[i][1] = a[i].imag
    return rv

def ratrace(
        metal, substrate,
        z, # [bottom of substrate, top of substrate, top of metal]
        port_length,
        ms_width, priority = 9,
        lq=8.9*mm, w=0.175*mm, r1=0.7*mm, r2 = 0.7*mm, kicad=False, loopr=1.0*mm):
    em = metal.em
    ms_width = ms_width
    endspace = 0.5 * mm

    feedx = -lq + -r2 + pi*r2/2.0
    arcx = feedx - lq + (r1+r2)*pi/2
    endspace = ms_width + port_length if kicad else endspace

    def addy_sym(y):
        em.mesh.AddLine('y',y)
        em.mesh.AddLine('y',-y)

    addy_sym(r1 - 0.5*w)
    addy_sym(r1 + 0.5*w)
    addy_sym(r1+r2 - 0.5*w)
    addy_sym(r1+r2 + 0.5*w)

    # substrate
    start = np.array([endspace, r1+r2+endspace, z[0]])
    stop  = np.array([arcx - r1 - r2 - endspace, -1.0*start[1], z[1]])
    substrate.AddBox(start, stop, 1)

    # outer loop
    c1 = arcx
    lo = cat((
        arc(-1.0*r2, r1, r2+0.5*w, 0*pi, 0.5*pi),
        arc(c1, 0, r1+r2+0.5*w, 0.5*pi, 1.5*pi),
        arc(-1.0*r2, -r1, r2+0.5*w, 1.5*pi, 2*pi),
    ))
    li = cat((
        arc(-1.0*r2, r1, r2-0.5*w, 0*pi, 0.5*pi),
        arc(c1, 0, r1+r2-0.5*w, 0.5*pi, 1.5*pi),
        arc(-1.0*r2, -r1, r2-0.5*w, 1.5*pi, 2*pi),
    ))
    l = cat((lo, li[::-1]))
    metal.AddPolygon(
        priority = priority,
        points = complex_to_xy(l),
        elevation = z[1:],
        normal_direction = 'z',
        pcb_layer = 'F.Cu',
        pcb_width = 0.001)

    # inner loop
    lo = arc(np.pi*r1/2.0 - lq, 0, r1+0.5*w, 0.5*pi, 1.5*pi)
    li = arc(np.pi*r1/2.0 - lq, 0, r1-0.5*w, 0.5*pi, 1.5*pi)
    lo = cat((lo, [0.5*w - 1j*(r1+0.5*w), 0.5*w - 1j*(r1-0.5*w)]))
    li = cat(([0.5*w + 1j*(r1+0.5*w), 0.5*w + 1j*(r1-0.5*w)], li))
    l = cat((lo, li[::-1]))
    metal.AddPolygon(
        priority = priority,
        points = complex_to_xy(l),
        elevation = z[1:],
        normal_direction = 'z',
        pcb_layer = 'F.Cu',
        pcb_width = 0.001)

    # delta port
    start = [feedx + 0.5*ms_width, -1.0*(r1+r2)-endspace, z[1]]
    stop  = [start[0] - ms_width,  start[1] + port_length, z[2]]
    em.AddPort(start, stop, direction='y', z=50)

    # delta line
    start[1]  = -1.0*(r1+r2)
    metal.AddBox(start, stop, priority, padname = '1')

    # 0/180 ports
    start = [endspace, r1-0.5*ms_width, z[1]]
    stop  = [endspace - port_length,  r1+0.5*ms_width, z[2]]
    em.AddPort(start, stop, direction='x', z=50).duplicate().mirror('y')

    # 0/180 lines
    start[0]  = 0
    metal.AddBox(start, stop, priority, padname = '3')
    metal.AddBox(start, stop, priority, padname = '4').mirror('y')

    # sum port
    portx1 = feedx - 0.5*mm
    portx2 = portx1 - port_length
    start = [portx1, -0.5*ms_width, z[1]]
    stop  = [portx2,  0.5*ms_width, z[2]]
    em.AddPort(start, stop, direction='x', z=50)

    # sum line
    start[0] = feedx
    stop[0] = portx1
    metal.AddBox(start, stop, priority, padname = '2')

    # sum ground
    start[0] = portx2
    stop[0] = portx2 - 0.5*mm
    start[2] = 0
    if not kicad:
        metal.AddBox(start, stop, priority)

    # ground loops
    if kicad:
        r = loopr
        y1 = r1+r
        x = -lq + pi*r
        w = ms_width
        l = cat((
            arc(0, y1, r+0.5*w, -0.5*pi, 0.5*pi),
            [x + 1j*(y1+r+0.5*w), x + 1j*(y1+r-0.5*w)],
            arc(0, y1, r-0.5*w, 0.5*pi, -0.5*pi),
        ))
        metal.AddPolygon(
            priority = priority,
            points = complex_to_xy(l),
            elevation = z[1:],
            normal_direction = 'z',
            pcb_layer = 'F.Cu',
            pcb_width = 0.001).duplicate().mirror('y')
        openems.Via(metal, priority=2, x=x, y=y1+r, z=[[0, z[2]], [z[1], z[2]]],
                    drillradius=0.1*mm,
                    padradius=0.225*mm, padname='5').duplicate().mirror('y')
