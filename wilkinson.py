from scipy.constants import pi, c, epsilon_0, mu_0, mil, inch
mm = 0.001
import openems
import numpy as np

class Wilkinson():
    def __init__(self, em, metal, substrate, miter, z, port_length,
                 ms_width, ms_width_70, fork_length, priority = 9):
        self.em = em
        self.metal = metal
        self.substrate = substrate
        self.z = z # [bottom of substrate, top of substrate, top of metal]
        self.port_length = port_length
        self.priority = priority
        self.ms_width = ms_width
        self.ms_width_70 = ms_width_70
        self.miter = miter
        self.fork_length = fork_length
        self.endspace = 0.5 * mm
        self.resistor_gap = 0.15 * mm # gap between resistor pads
    def generate(self):
        x0 = self.endspace
        x1 = -1.0 * self.fork_length
        x2 = x1 - self.ms_width_70
        x4 = x2 - self.endspace
        x3 = x4 + self.port_length
        y1 = self.resistor_gap
        y2 = y1 + self.ms_width_70
        y4 = y2 + self.endspace
        y3 = y4 - self.port_length

        # substrate
        start = np.array([x0, y4, self.z[0]])
        stop  = np.array([x4, -1.0*y4, self.z[1]])
        openems.Box(self.substrate, 1, start, stop);

        # common port line (pad 1)
        start = np.array([x1,  0.5*self.ms_width, self.z[1]])
        stop  = np.array([x3, -0.5*self.ms_width, self.z[2]])
        openems.Box(self.metal, self.priority, start, stop, padname = '1')

        # fork line
        openems.Polygon(self.metal,
                        priority = self.priority,
                        points = np.array([[0, y1],
                                           [0, y2],
                                           [x2+self.miter, y2],
                                           [x2, y2 - self.miter],
                                           [x2, self.miter - y2],
                                           [x2+self.miter, -1.0 * y2],
                                           [0, -1.0 * y2],
                                           [0, -1.0 * y1],
                                           [x1, -1.0 * y1],
                                           [x1, y1]]),
                        elevation = self.z[1:],
                        normal_direction = 'z',
                        pcb_layer = 'F.Cu',
                        pcb_width = 0.001)

        # output lines
        start = np.array([-0.5*self.ms_width, y1, self.z[1]])
        stop  = np.array([ 0.5*self.ms_width, y3, self.z[2]])
        lp2 = openems.Box(self.metal, self.priority, start, stop, padname = '2')
        lp3 = lp2.duplicate()
        lp3.mirror('y')
        lp3.padname = '3'

        # main line port
        start = [x3, -0.5*self.ms_width, self.z[1]]
        stop  = [x4,  0.5*self.ms_width, self.z[2]]
        openems.Port(self.em, start, stop, direction='x', z=50)

        # coupled line ports
        start = [-0.5*self.ms_width, y3, self.z[1]]
        stop  = [ 0.5*self.ms_width, y4, self.z[2]]
        openems.Port(self.em, start, stop, direction='y', z=50).duplicate().mirror('y')

        # resistor
        self.em.add_resistor('r1', origin=np.array([0,0,self.z[2]]), direction='y', value=100.0, invert=False, priority=9, dielectric_name='alumina', metal=self.metal, element_down=False)
