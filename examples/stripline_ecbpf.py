#!/usr/bin/env python3
import sys
from scipy.constants import pi, c, mil
from openems import OpenEMS, Box, Cylinder, Port, Metal, Dielectric, Polygon, arc
import numpy as np

band = 5

g = np.ones(10) * 0.28e-3
g[0] = 0.18e-3

cw = 4e-3
mesh = [53e-6, 53e-6, 53e-6]

# 7 updated
w = np.array([7.25,15.75,19.25,19.25])*mil
s = np.array([7.25,11.5,15.75,16.25])*mil

boundaries = ['PEC', 'PEC', 'PEC', 'PEC', 'PEC', 'PEC']

if band == 1:
    fc = 16.95e9*.985
    fmax = 25e9
    g = np.ones(10) * 0.28e-3
    g[0] = 0.15e-3
    mesh = [34e-6, 32e-6, 27e-6]
    # 12.09183645866654

elif band == 2:
    fc = 21.35e9*0.9875#/(21.62/21.35)
    fmax = 30e9
    mesh = [34e-6, 32e-6, 27e-6]
    #14.964134888145727

elif band == 3:
    fc = 26.9e9*0.9955
    fmax = 35e9
    mesh = [34e-6, 32e-6, 27e-6]
    #18.483322945104838

elif band == 4:
    fc = 33.9e9*0.9955
    fmax = 50e9
    mesh = [52e-6, 52e-6, 35e-6]
    boundaries = ['PEC', 'PEC', 'MUR', 'MUR', 'PEC', 'PEC']

elif band == 5:
    fc = 42.7e9
    fmax = 60e9
    mesh = [52e-6, 52e-6, 35e-6]
    boundaries = ['PEC', 'PEC', 'MUR', 'MUR', 'PEC', 'PEC']

elif band == 6:
    fc = 53.8e9
    fmax = 70e9
    mesh = [52e-6, 52e-6, 35e-6]
    #g *= 0
    boundaries = ['PEC', 'PEC', 'MUR', 'MUR', 'PEC', 'PEC']

else:
    raise Exception("undefined band")

em = OpenEMS(
    'sss_ecbpf{}'.format(band),
    EndCriteria = 1e-6,
    fmin = 0e6,
    fmax = fmax,
    fsteps = 1001,
    boundaries = boundaries,
)

copper = Metal(em, 'copper')
sub = Dielectric(em, 'polyimide', eps_r=3.2, tand=0.0035, fc=fc)
zport = 100
foil_thickness = 0.05e-3
substrate_thickness = 4*mil
port_length = 0.42e-3

sl_width = 0.597e-3

qw = 0.25 * c / (fc * np.sqrt(1.35))
print("quarter wave length:", qw)

etch = 0e-6
g += 0.5*etch
w -= etch
s += etch

# dimensions Z
zair = 0.75e-3
z0 = 0
z1 = z0 + zair # bottom of bottom foil
z2 = z1 + foil_thickness # top of bottom foil
z3 = z2 + substrate_thickness # bottom of top foil
z4 = z3 + foil_thickness # top of top foil
z5 = z4 + zair

em.resolution = mesh

em.mesh.AddLine('z', z0)
em.mesh.AddLine('z', z5)
em.mesh.AddLine('z', z4 + 50e-6)
#em.mesh.AddLine('z', z4 - 25e-6)
em.mesh.AddLine('z', (z3+z2)*0.5)
#em.mesh.AddLine('z', (3*z3+z2)*0.25)

x = 0
y = 0.5*w[-1]

# resonators
for i in range(len(w))[::-1]:
    gp = g[0]
    for m in [-1,1]:
        start = np.array([(x-gp)*m, (y-w[i])*m, z3])
        stop = np.array([(x+qw-g[i])*m, y*m, z4])
        Box(copper, 1, start, stop, padname='poly')
    y += s[i]
    for m in [-1,1]:
        start = np.array([(x+g[i])*m, y*m, z3])
        stop = np.array([(x+qw)*m, (y+w[i])*m, z4])
        Box(copper, 1, start, stop, padname='poly')
    y += w[i]
    x += qw

# port (ms), port line
y -= w[0]
hl = x + .75e-3
pname = 1
for m in [-1,1]:
    start = np.array([m*(hl-port_length), m*y, z3])
    stop  = np.array([m*x, m*(y+sl_width), z4])
    Box(copper, 1, start, stop, padname = str(pname))
    pname += 1
    stop[0] = m*hl
    Port(em, start, stop, direction='x', z=zport)

y += sl_width
theta = np.arctan(y/hl)
print("theta =", theta*180/np.pi)
yoff = 0.5*cw/np.cos(theta)
print("yoff =", yoff)
ymax = y + yoff

points = np.array([[-hl, -ymax], [hl, -ymax], [hl, ymax-2*yoff]])
for m in ['xy', '']:
    if boundaries[2] == 'PEC':
        Polygon(copper, points, [z0, z5], x=0, y=0, mirror=m, priority=9)

theta = np.arctan((2*ymax-2*yoff)/(2*hl))
print("theta =", theta*180/np.pi)

# substrate
start = np.array([-hl, -ymax, z2])
stop  = np.array([hl, ymax, z3])
Box(sub, 1, start, stop)

em.write_kicad(em.name)
command = 'view solve'
if len(sys.argv) > 1:
    command = sys.argv[1]
print(command)
em.run_openems(command, z=zport)
