import openems
import numpy as np

def smp_connector(em, x, y, z, zmax, coax_port_length = 0.2e-3, pin_diameter=0.85e-3):
    copper_shield = openems.Metal(em, 'smp_shield')
    copper = openems.Metal(em, 'smp_pin')
    lcp = openems.Dielectric(em, 'lcp', eps_r=3.2)

    # shield
    outside = np.array([[-2.5,1.0], [-2.5,2.5], [2.5,2.5], [2.5,-2.5], [-2.5,-2.5], [-2.5,-1.0]])*1e-3
    angle = np.arcsin(1.0/2.25)
    inside = openems.arc(0,0, 4.5e-3 / 2.0, -np.pi + angle, np.pi - angle)
    openems.Polygon(copper_shield,
                    priority=9,
                    pcb_layer=None,
                    points = [x,y] + np.concatenate((inside, outside)),
                    elevation = [z, z + 0.9e-3],
                    normal_direction = 'z')

    outside = np.array([[0,2.5], [2.5,2.5], [2.5,-2.5], [0,-2.5]])*1e-3
    inside = openems.arc(0,0, 1.95e-3 / 2.0, -np.pi*0.5, np.pi*0.5)
    openems.Polygon(copper_shield,
                    priority=9,
                    pcb_layer=None,
                    points = [x,y] + np.concatenate((inside, outside)),
                    elevation = [z + 0.9e-3, zmax],
                    normal_direction = 'z').duplicate().mirror('x')

    # pin
    start = np.array([x, y, zmax - coax_port_length])
    stop  = np.array([x, y, z + 0.9e-3])
    copper.AddCylinder(start, stop, 0.5*pin_diameter, priority=9)

    # smaller part of pin
    stop[2] = z
    copper.AddCylinder(start, stop, 0.5*0.8e-3, priority=9)

    # insulator
    start = np.array([x, y, z])
    stop  = np.array([x, y, z + 0.9e-3])
    lcp.AddCylinder(start, stop, 4.5e-3*0.5, priority=1)

    if coax_port_length != 0:
        # port (coax)
        start = [x + 0.5*coax_port_length, y + 0.5*coax_port_length, zmax - coax_port_length]
        stop  = [x - 0.5*coax_port_length, y - 0.5*coax_port_length, zmax]
        openems.Port(em, start, stop, direction='z', z=50)
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
        inside = openems.arc(0,0, r, -np.pi*0.5, np.pi*0.5)
        openems.Polygon(sub,
                        priority=priority,
                        pcb_layer=pcb_layer,
                        points = np.concatenate((inside, outside)),
                        elevation = z,
                        normal_direction = 'z').duplicate().mirror('x')
