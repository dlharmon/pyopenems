from openems import OpenEMS, Box, Cylinder, Via, Port, Metal, Dielectric, geometries, arc, Polygon
import numpy as np

def smp_connector(em, x, y, z, zmax, coax_port_length = 0.2e-3, pin_diameter=0.85e-3):
    copper_shield = Metal(em, 'smp_shield')
    copper = Metal(em, 'smp_pin')
    lcp = Dielectric(em, 'lcp', eps_r=3.2)

    # shield
    outside = np.array([[-2.5,1.0], [-2.5,2.5], [2.5,2.5], [2.5,-2.5], [-2.5,-2.5], [-2.5,-1.0]])*1e-3
    angle = np.arcsin(1.0/2.25)
    inside = arc(0,0, 4.5e-3 / 2.0, -np.pi + angle, np.pi - angle)
    Polygon(copper_shield,
            priority=9,
            pcb_layer=None,
            points = [x,y] + np.concatenate((inside, outside)),
            elevation = [z, z + 0.9e-3],
            normal_direction = 'z')

    outside = np.array([[0,2.5], [2.5,2.5], [2.5,-2.5], [0,-2.5]])*1e-3
    inside = arc(0,0, 1.95e-3 / 2.0, -np.pi*0.5, np.pi*0.5)
    for m in ['', 'x']:
        Polygon(copper_shield, 9,
                pcb_layer=None,
                points = [x,y] + np.concatenate((inside, outside)),
                elevation = [z + 0.9e-3, zmax],
                normal_direction = 'z',
                mirror=m)
    # pin
    start = np.array([x, y, zmax - coax_port_length])
    stop  = np.array([x, y, z + 0.9e-3])
    Cylinder(copper, 9, start, stop, 0.5*pin_diameter)

    # smaller part of pin
    Cylinder(copper, 9, start, [x, y, z], 0.5*0.8e-3)

    # insulator
    Cylinder(lcp, 1, [x, y, z], [x, y, z + 0.9e-3], 2.25e-3)

    if coax_port_length != 0:
        # port (coax)
        start = [x + 0.5*coax_port_length, y + 0.5*coax_port_length, zmax - coax_port_length]
        stop  = [x - 0.5*coax_port_length, y - 0.5*coax_port_length, zmax]
        Port(em, start, stop, direction='z', z=50)
        em.mesh.AddLine('z', start[2])

class planar_full_box:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def add(self, sub, z, priority=1):
        start = np.array([self.x[0], self.y[0], z[0]])
        stop  = np.array([self.x[1], self.y[1], z[1]])
        sub.AddBox(start, stop, priority=priority)

    # add a plane with a hole in the middle
    def add_center_hole(self, sub, z, r, priority=1, pcb_layer = None):
        outside = np.array([[0,self.y[1]],
                            [self.x[1],self.y[1]],
                            [self.x[1],self.y[0]],
                            [0,self.y[0]]])
        inside = arc(0,0, r, -np.pi*0.5, np.pi*0.5)
        for m in ['', 'x']:
            Polygon(sub,
                    priority=priority,
                    pcb_layer=pcb_layer,
                    points = np.concatenate((inside, outside)),
                    elevation = z,
                    normal_direction = 'z',
                    mirror = m
            )
