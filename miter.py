from scipy.constants import pi, c, epsilon_0, mu_0, mil, inch
mm = 0.001
import openems
import numpy as np

def generate(em, metal, substrate, miter, z, port_length, ms_width, box_size, priority = 9):
    d1 = 0.5 * box_size
    d2 = d1 - port_length
    d3 = d2 - 0.2*mm
    d4 = -0.5*ms_width + miter

    # substrate
    start = np.array([ 0.5*box_size,  0.5*box_size, z[0]])
    stop  = np.array([-0.5*box_size, -0.5*box_size, z[1]])
    openems.Box(substrate, 1, start, stop);

    # port pads
    start = np.array([ 0.5*ms_width, d2, z[1]])
    stop  = np.array([-0.5*ms_width, d3, z[2]])
    openems.Box(metal, priority, start, stop, padname = '1')
    start = np.array([d2,  0.5*ms_width, z[1]])
    stop  = np.array([d3, -0.5*ms_width, z[2]])
    openems.Box(metal, priority, start, stop, padname = '2')

    # line
    openems.Polygon(metal,
                    priority = priority,
                    points = np.array([[-0.5*ms_width, d2],
                                       [ 0.5*ms_width, d2],
                                       [ 0.5*ms_width, 0.5*ms_width],
                                       [ d2,  0.5*ms_width],
                                       [ d2, -0.5*ms_width],
                                       [ d4, -0.5*ms_width],
                                       [ -0.5*ms_width, d4]]),
                    elevation = z[1:],
                    normal_direction = 'z',
                    pcb_layer = 'F.Cu',
                    pcb_width = 0.001)

    # ports
    start = np.array([ 0.5*ms_width, d1, z[1]])
    stop  = np.array([-0.5*ms_width, d2, z[2]])
    openems.Port(em, start, stop, direction='y', z=50)
    start = np.array([d1,  0.5*ms_width, z[1]])
    stop  = np.array([d2, -0.5*ms_width, z[2]])
    openems.Port(em, start, stop, direction='x', z=50)
