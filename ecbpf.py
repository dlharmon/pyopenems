#!/usr/bin/env python
mm = 0.001
import numpy as np
import openems

class ECBPF():
    def __init__(self, em, nresonators):
        self.n = nresonators
        self.em = em
        self.metal_name = 'pec'
        self.metal_z = [0, 0.2*mm]
        self.space = [0.15*mm, 0.25*mm, 0.3*mm]
        self.length = [2.6*mm]*self.n
        self.width = [0.15*mm]*self.n
        self.priority = 9
    def generate(self):
        rl_max = np.max(self.length)
        # finger 2
        x = 0.5*rl_max
        y = 0.5*self.space[2]
        start = [x - self.length[2], y, self.metal_z[0]];
        y += self.width[2]
        stop  = [x + self.length[2], y, self.metal_z[1]];
        openems.Box(self.em, 'r2', self.metal_name, self.priority, start, stop).duplicate('r2m').mirror('xy')
        # finger 1
        x += rl_max
        y += self.space[1]
        start = [x - self.length[1], y, self.metal_z[0]];
        y += self.width[1]
        stop  = [x + self.length[1], y, self.metal_z[1]];
        openems.Box(self.em, 'r1', self.metal_name, self.priority, start, stop).duplicate('r1m').mirror('xy')
        # finger 0 (half length coupling)
        x += rl_max
        y += self.space[0]
        start = [x - self.length[0], y, self.metal_z[0]];
        y += self.width[0]
        stop  = [x, y, self.metal_z[1]];
        openems.Box(self.em, 'r0', self.metal_name, self.priority, start, stop).duplicate('r0m').mirror('xy')
        self.xmax = x
        self.ymax = y
