#!/usr/bin/env python
import os, tempfile
import numpy as np
import scipy.io
from scipy.constants import pi, c, epsilon_0, mu_0
mm = 0.001
import matplotlib.pyplot
import footgen

from CSXCAD  import ContinuousStructure
from openEMS import openEMS

np.set_printoptions(precision=8)

def mirror(point, axes):
    retval = np.array(point).copy()
    if 'x' in axes:
        retval *= np.array([-1,1,1])
    if 'y' in axes:
        retval *= np.array([1,-1,1])
    if 'z' in axes:
        retval *= np.array([1,1,-1])
    return retval

def openems_direction_vector(direction):
    if 'x' in direction:
        return [1,0,0]
    if 'y' in direction:
        return [0,1,0]
    if 'z' in direction:
        return [0,0,1]

def db_angle(s):
    logmag = float(20.0*np.log10(np.abs(s)))
    angle = float(180.0*np.angle(s)/pi)
    return "{:>12f} {:>12f}".format(logmag, angle)

def save_s1p(f, s11, filename):
    fdata = "# GHz S DB R 50\n"
    for i in range(len(f)):
        fdata += "{0:>12f} {1}\n".format(f[i]/1e9, db_angle(s11[i]))
    with open(filename, "w") as f:
        f.write(fdata)

def save_s2p_symmetric(f, s11, s21, filename):
    fdata = "# GHz S DB R 50\n"
    for i in range(len(f)):
        fdata += "{0:>12f} {1} {2} {2} {1}\n".format(f[i]/1e9, db_angle(s11[i]), db_angle(s21[i]))
    with open(filename, "w") as f:
        f.write(fdata)


class Material():
    def __init__(self, em, name):
        self.lossy = False
        self.em = em
        self.name = name
    def AddBox(self, start, stop, priority, padname=None, pcb_layer='F.Cu'):
        return Box(self.em, start=start, stop=stop, priority=priority,
                   name=None, material=self, padname=padname, pcb_layer=pcb_layer)
    def AddPolygon(self, points, elevation, priority=1,
                   normal_direction='z',
                   pcb_layer = 'F.Cu',
                   pcb_width = 0.0):
        return Polygon(self, points, elevation, priority, normal_direction, pcb_layer, pcb_width)
    def AddCylinder(self, start, stop, radius, priority):
        return Cylinder(self, priority, start, stop, radius)

class Dielectric(Material):
    def __init__(self, em, name, eps_r=1.0, kappa = 0, ur=1.0, tand=0.0, fc = 0):
        if tand > 0.0:
            kappa = tand * 2*pi*fc * epsilon_0 * eps_r
        self.material = em.CSX.AddMaterial(name, epsilon = eps_r, kappa = kappa, mue = ur)
        self.em = em
        self.name = name
        self.eps_r = eps_r
        self.ur = ur
        self.kappa = kappa
        self.type = 'dielectric'
        self.lossy = False # metal loss
        # magnetic loss

class LumpedElement(Material):
    """ element_type = 'R' or 'C' or 'L' """
    def __init__(self, em, name, element_type='R', value=50.0, direction = 'x'):
        self.em = em
        self.name = name
        self.element_type = element_type
        self.value = value
        self.direction = direction
        em.CSX.AddLumpedElement(name=self.name, caps=False, ny = self.direction, R=self.value)

class Metal(Material):
    def __init__(self, em, name):
        self.lossy = False
        self.em = em
        self.name = name
        self.type = 'metal'
        self.material=em.CSX.AddMetal(name)

class LossyMetal(Material):
    def __init__(self, em, name, conductivity=56e6, frequency=None, thickness=None, ur=1.0):
        self.conductivity = conductivity
        if not thickness:
            # compute the skin depth
            self.thickness = np.sqrt((2.0/conductivity)/(2*pi*frequency*mu_0*ur))
            print('thickness = {}'.format(self.thickness))
        else:
            self.thickness = thickness
        self.em = em
        self.name = name
        self.type = 'metal'
        self.lossy = True
        self.material = em.AddConductingSheet(name, self.conductivity, self.thickness)

class Object():
    def mirror(self, axes):
        self.start = mirror(self.start, axes)
        self.stop = mirror(self.stop, axes)
        return self
    def rotate_ccw_90(self):
        """ rotate 90 degrees CCW in XY plane """
        self.start = np.array([-1.0*self.start[1], self.start[0], self.start[2]])
        self.stop = np.array([-1.0*self.stop[1], self.stop[0], self.stop[2]])
    def offset(self, val):
        self.start += val
        self.stop += val
    def generate_kicad(self, g):
        pass
    def duplicate_n(self, name=None, step=[0,0,0], count=1):
        for i in range(count-1):
            self.duplicate("{}_{}".format(self.em.get_name(name), i+2)).offset(np.array(step)*(i+1))

from .polygon import Polygon

class Box(Object):
    def __init__(self, em, name, material, priority, start, stop, padname = '1', pcb_layer='F.Cu'):
        self.priority = priority
        self.material = material
        self.start = np.array(start)
        self.stop = np.array(stop)
        self.em = em
        self.name = self.em.get_name(name)
        self.padname = padname
        self.layer = pcb_layer
        em.objects[self.name] = self
    def duplicate(self, name=None):
        return Box(self.em, name, self.material, self.priority,
                   self.start, self.stop, self.padname, self.layer)
    def generate_kicad(self, g):
        if self.material.__class__.__name__ == 'Dielectric':
            return
        if self.padname == None:
            return
        if self.padname == 'poly': # use a polygon rather than a pad
            x1 = self.start[0]
            x2 = self.stop[0]
            y1 = self.start[1]
            y2 = self.stop[1]
            points = np.array([[x1,y1],[x2,y1],[x2,y2],[x1,y2]])
            g.add_polygon(points = 1000.0 * points, layer = self.layer, width = 1e-6)
            return
        g.add_pad(self.padname,
                  layer = self.layer,
                  x = 500.0 * (self.start[0] + self.stop[0]), # mm
                  y = 500.0 * (self.start[1] + self.stop[1]), # mm
                  xsize = 1000.0 * abs(self.start[0] - self.stop[0]), # mm
                  ysize = 1000.0 * abs(self.start[1] - self.stop[1]),
                  masked = True,
                  paste = False)
    def generate_octave(self):
        self.material.material.AddBox(start=self.start, stop=self.stop,
                                      priority=self.priority)
        self.em.mesh.AddLine('x', self.start[0])
        self.em.mesh.AddLine('y', self.start[1])
        self.em.mesh.AddLine('z', self.start[2])
        self.em.mesh.AddLine('x', self.stop[0])
        self.em.mesh.AddLine('y', self.stop[1])
        self.em.mesh.AddLine('z', self.stop[2])

class Cylinder(Object):
    def __init__(self, material, priority, start, stop, radius):
        self.material = material
        self.start = np.array(start)
        self.stop = np.array(stop)
        self.em = material.em
        self.name = self.em.get_name(None)
        self.radius = radius
        self.padname = '1'
        self.priority = priority
        self.em.objects[self.name] = self
    def duplicate(self, name=None):
        return Cylinder(self.material, self.priority, self.start, self.stop, self.radius)
    def generate_octave(self):
        self.material.material.AddCylinder(priority=self.priority,
                                           start=self.start,
                                           stop=self.stop,
                                           radius=self.radius)

class Via(Object):
    """PCB via in Z direction
    em = OpenEMS instance
    name = any string for reference
    material = a string matching a defined material (see Material class)
    priority = integer, when objects overlap, higher takes precedence
    x, y = position
    z[0] = [barrel top, barrel bottom]
    z[1:] = [pad top, pad bottom]
    drill radius
    pad rad
    """
    def __init__(self, em, name, material, priority, x, y, z, drillradius, padradius, padname='1'):
        self.material = material
        self.priority = priority
        self.x = x
        self.y = y
        self.z = z
        self.drillradius = drillradius
        self.padradius = padradius
        self.em = em
        self.name = self.em.get_name(name)
        self.padname = padname
        em.objects[self.name] = self
    def mirror(self, axes):
        if 'x' in axes:
            self.x *= -1.0
        if 'y' in axes:
            self.y *= -1.0
        return self
    def generate_kicad(self, g):
        g.add_pad(x = self.x * 1000.0,
                  y = self.y * 1000.0,
                  diameter = self.padradius * 2000.0, # footgen uses mm
                  drill = self.drillradius * 2000.0,
                  mask_clearance = -500.0*(self.padradius-self.drillradius) + 0.03,
                  shape = "circle",
                  name = self.padname)
    def offset(self, val):
        self.x += val[0]
        self.y += val[1]
    def duplicate(self, name=None):
        return Via(self.em, name, self.material, self.priority, self.x, self.y, self.z, self.drillradius, self.padradius, self.padname)
    def generate_octave(self):
        start = [self.x + self.em.via_offset_x, self.y + self.em.via_offset_y, self.z[0][0]]
        stop = [self.x + self.em.via_offset_x, self.y + self.em.via_offset_y, self.z[0][1]]
        self.material.material.AddCylinder(start=start, stop=stop, priority=self.priority, radius = self.drillradius)
        for z in self.z[1:]:
            start = [self.x, self.y, z[0]]
            stop = [self.x, self.y, z[1]]
            self.material.material.AddCylinder(start=start, stop=stop, priority=self.priority, radius = self.padradius)

class RoundPad(Object):
    """PCB pad in Z direction
    em = OpenEMS instance
    material = a string matching a defined material (see Material class)
    priority = integer, when objects overlap, higher takes precedence
    x, y = position
    z[0] = [barrel top, barrel bottom]
    z[1:] = [pad top, pad bottom]
    drill radius
    pad rad
    """
    def __init__(self, em, material, priority, x, y, z, padradius, padname='1'):
        self.material = material
        self.priority = priority
        self.x = x
        self.y = y
        self.z = z
        self.padradius = padradius
        self.em = em
        self.name = self.em.get_name(None)
        self.padname = padname
        em.objects[self.name] = self
    def mirror(self, axes):
        if 'x' in axes:
            self.x *= -1.0
        if 'y' in axes:
            self.y *= -1.0
        return self
    def generate_kicad(self, g):
        g.add_pad(x = self.x * 1000.0,
                  y = self.y * 1000.0,
                  diameter = self.padradius * 2000.0, # footgen uses mm
                  mask_clearance = 0.0,
                  shape = "circle",
                  name = self.padname)
    def offset(self, val):
        self.x += val[0]
        self.y += val[1]
    def duplicate(self, name=None):
        return RoundPad(self.em, name, self.material, self.priority, self.x, self.y, self.z, self.drillradius, self.padradius, self.padname)
    def generate_octave(self):
        self.material.material.AddCylinder(start = [self.x, self.y, self.z[0]],
                                           stop = [self.x, self.y, self.z[1]],
                                           priority=self.priority,
                                           radius = self.padradius)

class Port(Object):
    def __init__(self, em, start, stop, direction, z, padname = None, layer = 'F.Cu'):
        self.em = em
        self.start = np.array(start)
        self.stop = np.array(stop)
        self.direction = direction
        self.z = z
        self.padname = padname
        self.layer = layer
        self.portnumber = len(em.ports)
        name = "p" + str(self.portnumber)
        em.objects[name] = self
        em.ports.append(self)
    def duplicate(self):
        return Port(self.em, self.start, self.stop, self.direction, self.z, padname = self.padname, layer = self.layer)
    def generate_octave(self):
        #AddMSLPort
        self.port = self.em.FDTD.AddLumpedPort(
            self.portnumber,
            R=self.z,
            start=self.start,
            stop=self.stop,
            p_dir=self.direction,
            excite=1.0 if self.em.excitation_port == self.portnumber else 0)
    def generate_kicad(self, g):
        if self.padname == None:
            return
        g.width = 1000.0 * abs(self.start[0] - self.stop[0]) # mm
        g.height = 1000.0 * abs(self.start[1] - self.stop[1])
        x = 500.0 * (self.start[0] + self.stop[0]) # mm
        y = 500.0 * (self.start[1] + self.stop[1]) # mm
        g.add_pad(x,y,self.padname, layer = self.layer)

class OpenEMS:
    def __init__(self, name, fmin=1e6, fmax=50e9,
                 NrTS=1e6,
                 EndCriteria=1e-6,
                 #BC = {xmin xmax ymin ymax zmin zmax};
                 boundaries = ['PEC', 'PEC', 'PEC', 'PEC', 'PEC', 'PEC']):
        self.FDTD = openEMS(NrTS=NrTS, EndCriteria=EndCriteria)
        self.FDTD.SetGaussExcite((fmin+fmax)/2.0, (fmax-fmin)/2.0)
        self.FDTD.SetBoundaryCond(boundaries)
        self.CSX = ContinuousStructure()
        self.FDTD.SetCSX(self.CSX)
        self.mesh = self.CSX.GetGrid()
        self.mesh.SetDeltaUnit(1.0) # specify everything in m
        self.fmin = fmin
        self.fmax = fmax
        self.fsteps = 1601
        self.objects = {}
        self.name = name
        self.ports = []
        self.excitation_port = 0
        self.excite_ports = [1]
        self.metalloss = False
        self.via_offset_x = 0.0
        self.via_offset_y = 0.0
        self.xgrid = None # for plot
        self.ygrid = None
        self.legend_location = 2 # upper left
        self.options = ''
        self.name_count = 0
        self.resolution = 0.0001

    def add_metal(self, name):
        print("add_metal is deprecated - use openems.Metal() directly")
        return Metal(self, name)
    def add_dielectric(self, name, eps_r=1.0, kappa = None, ur=1.0):
        print("add_dielectric is deprecated - use openems.Dielectric() directly")
        return Dielectric(self, name, eps_r, kappa, ur)
    def add_lumped(self, name, element_type='R', value=50.0, direction = 'x'):
        print("add_lumped is deprecated - use openems.LumpedElement() directly")
        return LumpedElement(self, name, element_type, value, direction)
    def add_box(self, name, material, priority, start, stop, padname='1'):
        print("add_box is deprecated - use openems.Box() directly")
        return Box(self, name, material, priority, start, stop, padname)
    def AddPort(self, start, stop, direction, z):
        return Port(self, start, stop, direction, z)
    def add_via(self, name, material, priority, x, y, z, drillradius, padradius, padname = '1'):
        print("add_via is deprecated - use openems.Via() directly")
        return Via(self, name, material, priority, x, y, z, drillradius, padradius, padname)
    def add_resistor(self, name, origin=np.array([0,0,0]), direction='x', value=100.0, invert=False, priority=9, dielectric_name='alumina', metal_name='pec', element_down=False, size='0201'):
        """ currently only supports 'x', 'y' for direction """
        element_name = name + "_element"
        LumpedElement(self, element_name, element_type='R', value = value, direction = direction)
        # resistor end caps
        start = np.array([-0.15*mm, -0.25*mm, 0])
        stop  = np.array([0.15*mm, -0.25*mm/2, 0.25*mm])
        if size == '0402':
            start = np.array([-0.25*mm, -0.5*mm, 0])
            stop  = np.array([0.25*mm, -0.5*mm/2, 0.35*mm])
        cap1 = Box(self, name+"_end_cap", metal_name, priority, start, stop, padname = None)
        cap2 = cap1.duplicate(name+"+_end_cap2")
        cap2.mirror('y')
        # resistor body
        start = np.array([-0.15, -0.27, 0.02])*mm
        stop  = np.array([0.15, 0.27, 0.23])*mm
        if size == '0402':
            start = np.array([-0.25, -0.47, 0.02])*mm
            stop  = np.array([0.25, 0.47, 0.33])*mm
        body = Box(self, name+"_body", dielectric_name, priority + 1, start, stop, padname = None)
        # resistor element
        if element_down:
            zoff = 0.0
        else:
            zoff = 0.33 if size == '0402' else 0.23
        start = np.array([-0.1, -0.25/2, 0+zoff])*mm
        stop  = np.array([0.1, 0.25/2, 0.02+zoff])*mm
        if size == '0402':
            start = np.array([-0.2, -0.25, 0+zoff])*mm
            stop  = np.array([0.2, 0.25, 0.02+zoff])*mm
        element = Box(self, element_name, element_name, priority + 1, start, stop, padname = None)
        # reposition
        if invert:
            cap1.mirror('z')
            cap2.mirror('z')
            body.mirror('z')
            element.mirror('z')
        if not 'y' in direction:
            cap1.rotate_ccw_90()
            cap2.rotate_ccw_90()
            body.rotate_ccw_90()
            element.rotate_ccw_90()
        cap1.offset(origin)
        cap2.offset(origin)
        body.offset(origin)
        element.offset(origin)
    def get_name(self, name):
        if name:
            return name
        self.name_count += 1
        return "pad_{}".format(self.name_count)

    def write_kicad(self, fpname, mirror=""):
        f = footgen.Footgen(fpname)
        g = f.generator
        g.mirror = mirror
        for object in self.objects:
            g.options = "masked"
            g.drill = 0
            self.objects[object].generate_kicad(g)
        f.finish()

    def run_openems(self, options='view solve'):
        cwd = os.getcwd()
        basename = cwd + '/' + self.name
        simpath = r'/tmp/openems_data'
        if not os.path.exists(simpath):
            os.mkdir(simpath)

        for object in self.objects:
            self.objects[object].generate_octave()

        import collections
        if not isinstance(self.resolution, collections.Sequence):
            self.resolution = np.ones(3) * self.resolution

        self.mesh.SmoothMeshLines('x', self.resolution[0])
        self.mesh.SmoothMeshLines('y', self.resolution[1])
        self.mesh.SmoothMeshLines('z', self.resolution[2])

        if 'view' in options:
                CSX_file = simpath + '/csx.xml'
                self.CSX.Write2XML(CSX_file)
                os.system(r'AppCSXCAD "{}"'.format(CSX_file))
        if 'solve' in options:
            self.FDTD.Run(simpath, verbose=3, cleanup=True)
            f = np.linspace(self.fmin, self.fmax, self.fsteps)
            for p in self.ports:
                p.port.CalcPort(simpath, f, ref_impedance = 50)
            nports = len(self.ports)

            s = []

            for p in range(nports):
                s.append(self.ports[p].port.uf_ref / self.ports[0].port.uf_inc)
            #    zratio = np.sqrt(self.objects["p" + str(self.excitation_port)].z / self.objects["p" + str(p+1)].z)
                #footer += "s{0}{1} = {2} * port{{{0}}}.uf.ref./ port{{{1}}}.uf.inc;\n".format(p+1, self.excitation_port, zratio)
                #ports += "s{}{} ".format(p+1, self.excitation_port)

            if nports < 1:
                return

            self.frequencies = f
            fig, ax = matplotlib.pyplot.subplots()
            s11 = s[0]
            if nports == 1:
                save_s1p(f, s11, basename+".s1p")
            if nports > 1:
                s21 = s[1]
                ax.plot(f/1e9, 20*np.log10(np.abs(s21)), label = 'dB(s21)')
                save_s2p_symmetric(f, s11, s21, basename+".s2p")
            ax.plot(f/1e9, 20*np.log10(np.abs(s11)), label = 'dB(s11)')
            if nports > 2:
                s31 = s[2]
                ax.plot(f/1e9, 20*np.log10(np.abs(s31)), label = 'dB(s31)')
            if nports > 3:
                s41 = s[3]
                ax.plot(f/1e9, 20*np.log10(np.abs(s41)), label = 'dB(s41)')

            ax.set_xlabel('Frequency (GHz)')
            ax.set_ylabel('dB')
            if hasattr(self.xgrid, "__len__"):
                ax.set_xticks(self.xgrid)
            if hasattr(self.ygrid, "__len__"):
                ax.set_yticks(self.ygrid)
            ax.grid(True)
            fig.tight_layout()
            ax.legend(loc=self.legend_location)
            matplotlib.pyplot.savefig(basename+".png")
            matplotlib.pyplot.savefig(basename+".svg")
            matplotlib.pyplot.savefig(basename+".pdf")
            matplotlib.pyplot.show()
            print(len(self.frequencies))
            print(s)
