import openems
import numpy as np

arc = openems.arc

def generate(
        em,
        sub,
        mask,
        min_width, # minimum copper width, typically design rule minimum
        cutout_width, # width of ground plane cutouts
        inductors,
        capacitors,
        z, # bottom of [air below, bottom metal, substrate, top metal, air above, lid]
        port_length,
        ms_width,
        box_width):

    em.mesh.AddLine('z', z[0]) # air above, below
    em.mesh.AddLine('z', z[5])
    em.mesh.AddLine('z', 0.5*(z[2]+z[3]))
    em.mesh.AddLine('z', 0.25*(3*z[2]+z[3]))
    em.mesh.AddLine('z', 0.25*(z[2]+3*z[3]))
    em.mesh.AddLine('y', -0.5*min_width)
    em.mesh.AddLine('y', 0.5*min_width)

    box_length = 2.0*(np.sum(inductors) + capacitors[0] + 0.5e-3)

    x0 = -0.5*box_length
    x1 = x0 + port_length
    x2 = x1 + ms_width

    yb = 0.5*cutout_width
    yo = -0.1e-3 # overlap

    pec = openems.Metal(em, 'pec')

    # substrate
    start = np.array([ 0.5*box_length, 0.5*box_width, z[2]])
    stop  = np.array([-0.5*box_length, -0.5*box_width, z[3]])
    openems.Box(sub, 1, start, stop)
    # solder mask
    if mask != None:
        start[2] = z[3] + 25e-6
        openems.Box(mask, 1, start, stop)

    # top copper polygon
    points = np.zeros((6+10*len(inductors),2))
    points[0] = [x1, 0.5*ms_width]
    x = -np.sum(inductors)
    points[1] = [x - 0.5*ms_width, 0.5*ms_width]
    points[2:10] = arc(x, 0, capacitors[0], 3*np.pi/4.0, np.pi/4.0, npoints = 8)
    points[10] = [x + 0.5*min_width, 0.5*min_width]
    i = 11
    x += inductors[0]
    for j in range(1, len(inductors)):
        points[i+0] = [x-0.5*min_width, 0.5*min_width]
        points[i+1:i+9] = arc(x, 0, capacitors[j], 3*np.pi/4.0, np.pi/4.0, npoints = 8)
        points[i+9] = [x+0.5*min_width, 0.5*min_width]
        i += 10
        x += inductors[j]
    # center cap
    points[i+0] = [-0.5*min_width, 0.5*min_width]
    points[i+1:i+5] = arc(0, 0, capacitors[-1], 3*np.pi/4.0, np.pi/2.0 + 0.001, npoints = 4)
    print(points)
    points = np.concatenate((points, points[::-1]*[-1,1]))
    points = np.concatenate((points, points[::-1]*[1,-1]))
    pec.AddPolygon(
        points = points,
        priority = 9,
        elevation = z[3:5],
        pcb_layer = 'F.Cu')

    # ground plane
    gpec = openems.Metal(em, 'ground_plane')
    points = np.zeros((2+6*len(inductors),2))
    points[0] = [x0, 0.5*box_width]
    points[1] = [x0, yo]
    i = 2
    x = -np.sum(inductors)
    for l in inductors:
        hmw = 0.5*min_width
        xl = x + hmw
        points[i+0] = [xl,yo]
        points[i+1] = [xl,hmw]
        xl = x + yb
        points[i+2] = [xl,yb]
        xl = x + l - yb
        points[i+3] = [xl,yb]
        xl = x + l - hmw
        points[i+4] = [xl,hmw]
        points[i+5] = [xl,yo]
        i += 6
        x += l
    print("ground plane",points)
    for ym in [1,-1]:
        gpec.AddPolygon(
            points = [1,ym] * np.concatenate((points, points[::-1]*[-1,1])),
            priority = 9,
            elevation = z[1:3],
            pcb_layer = 'B.Cu',
            is_custom_pad = True,
            x=0,
            y=ym*(yb+0.1e-3),
            pad_name='3',
        )

    for (xm,padname) in [(-1,2),(1,1)]:
        # main line ports
        start = [x0*xm, -0.5*ms_width, z[3]]
        stop  = [x1*xm,  0.5*ms_width, z[4]]
        em.AddPort(start, stop, direction='x', z=50)
        # pads
        start[0] = x2*xm
        l1 = openems.Box(pec, 9, start, stop, padname=padname)
