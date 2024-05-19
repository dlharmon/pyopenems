#!/usr/bin/env python
import os, tempfile
import numpy as np
from scipy.constants import pi, c, epsilon_0, mu_0
mm = 0.001
import matplotlib.pyplot
import openems.kicadfpwriter

from CSXCAD  import ContinuousStructure
from openEMS import openEMS

np.set_printoptions(precision=8)

# convert an array of complex numbers to an array of [x,y]
def complex_to_xy(a):
    rv = np.zeros((len(a),2))
    for i in range(len(a)):
        rv[i][0] = a[i].real
        rv[i][1] = a[i].imag
    return rv

# generate an array of [x,y] for an arc
def arc(x, y, r, a0, a1, npoints=32):
    angles = np.linspace(a0,a1,npoints)
    return complex_to_xy(r*np.exp(1j*angles) + x + 1j*y)

def mirror(point, axes):
    retval = np.array(point).copy()
    if 'x' in axes:
        retval *= np.array([-1,1,1])
    if 'y' in axes:
        retval *= np.array([1,-1,1])
    if 'z' in axes:
        retval *= np.array([1,1,-1])
    return retval

def db_angle(s):
    logmag = float(20.0*np.log10(np.abs(s)))
    angle = float(180.0*np.angle(s)/pi)
    return "{:>12f} {:>12f}".format(logmag, angle)

def save_s1p(f, s11, filename, z):
    fdata = "# GHz S DB R {}\n".format(z)
    for i in range(len(f)):
        fdata += "{0:>12f} {1}\n".format(f[i]/1e9, db_angle(s11[i]))
    with open(filename, "w") as f:
        f.write(fdata)

def save_s2p_symmetric(f, s11, s21, filename, z):
    print("warning: save_s2p_symmetric is only valid for a symmetric 2 port")
    fdata = "# GHz S DB R {}\n".format(z)
    for i in range(len(f)):
        fdata += "{0:>12f} {1} {2} {2} {1}\n".format(f[i]/1e9, db_angle(s11[i]), db_angle(s21[i]))
    with open(filename, "w") as f:
        f.write(fdata)

class Material():
    def __init__(self, em, name):
        self.lossy = False
        self.em = em
        self.name = name
    def AddBox(self, start, stop, priority, **kwargs):
        return Box(self, start=start, stop=stop, priority=priority, **kwargs)
    def AddPolygon(self, **kwargs):
        return Polygon(self, **kwargs)
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
    def __init__(self, em, name=None, element_type='R', value=50.0, direction = 'x'):
        self.em = em
        self.name = self.em.get_name(name)
        self.element_type = element_type
        self.value = value
        self.direction = direction
        self.material = em.CSX.AddLumpedElement(name=self.name, caps=False, ny = self.direction, R=self.value)

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
        self.material = em.CSX.AddConductingSheet(name, conductivity=self.conductivity, thickness=self.thickness)

class Object():
    def generate_kicad(self, g):
        pass

from .polygon import Polygon

class Box(Object):
    def __init__(self, material, priority, start, stop, padname = '1', pcb_layer='F.Cu', mirror='', mesh=True):
        mirror = [-1 if 'x' in mirror else 1, -1 if 'y' in mirror else 1, -1 if 'z' in mirror else 1]
        self.priority = priority
        self.material = material
        self.start = np.array(start) * mirror
        self.stop = np.array(stop) * mirror
        self.em = material.em
        self.name = self.em.get_name(None)
        self.padname = padname
        self.layer = pcb_layer
        self.em.objects[self.name] = self
        self.mesh = mesh
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
                  ysize = 1000.0 * abs(self.start[1] - self.stop[1]))
    def generate_octave(self):
        self.material.material.AddBox(start=self.start, stop=self.stop,
                                      priority=self.priority)
        if self.mesh:
            for vertex in [self.start, self.stop]:
                self.em.mesh.AddLine('x', vertex[0])
                self.em.mesh.AddLine('y', vertex[1])
                self.em.mesh.AddLine('z', vertex[2])

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
    def __init__(self, material, priority, x, y, z, drillradius, padradius, padname='1',
                 wall_thickness=0):
        self.material = material
        self.priority = priority
        self.x = x
        self.y = y
        self.z = z
        self.drillradius = drillradius
        self.wall_thickness = wall_thickness
        self.padradius = padradius
        self.em = material.em
        self.name = self.em.get_name(None)
        self.padname = padname
        self.em.objects[self.name] = self
    def generate_kicad(self, g):
        g.add_pad(x = self.x * 1000.0,
                  y = self.y * 1000.0,
                  diameter = self.padradius * 2000.0, # footgen uses mm
                  drill = self.drillradius * 2000.0,
                  shape = "circle",
                  name = self.padname)
    def generate_octave(self):
        start = [self.x + self.em.via_offset_x, self.y + self.em.via_offset_y, self.z[0][0]]
        stop = [self.x + self.em.via_offset_x, self.y + self.em.via_offset_y, self.z[0][1]]
        self.material.material.AddCylinder(start=start, stop=stop, priority=self.priority,
                                           radius = self.drillradius + self.wall_thickness)
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
    def generate_kicad(self, g):
        g.add_pad(x = self.x * 1000.0,
                  y = self.y * 1000.0,
                  diameter = self.padradius * 2000.0, # footgen uses mm
                  mask_clearance = 0.0,
                  shape = "circle",
                  name = self.padname)
    def generate_octave(self):
        self.material.material.AddCylinder(start = [self.x, self.y, self.z[0]],
                                           stop = [self.x, self.y, self.z[1]],
                                           priority=self.priority,
                                           radius = self.padradius)

def Resistor(em, origin=np.array([0,0,0]), direction='x', value=100.0, invert=False, priority=9, dielectric=None, metal=None, element_down=False, size='0201', thickness=None, FC=False):
    zm = -1 if invert else 1
    def orient(x):
        if not 'y' in direction:
            return np.array([x[1], x[0], x[2]])
        return x
    if thickness is None:
        if size == '0402':
            thickness = 0.35e-3
        thickness = 0.25e-3
    x1 = 0.15e-3
    y1 = 0.3e-3
    y3 = 125e-6
    x2 = 0.1e-3 # element half width
    if size == '0402':
        x1 = 0.25e-3
        y1 = 0.5e-3
        y3 = 250e-6
        x2 = 0.2e-3
    y2 = y1-30e-6

    """ currently only supports 'x', 'y' for direction """
    element = LumpedElement(
        em, name=em.get_name(None), element_type='R', value=value, direction=direction)
    # resistor end caps
    start = np.array([-x1, -y1, 0])
    stop  = np.array([ x1, -0.25*mm/2, 20e-6 if FC else thickness])
    if size == '0402':
        stop[1] = -0.25*mm
    for m in [np.array([1,-1,zm]), np.array([1,1,zm])]:
        Box(metal, priority, origin+orient(start*m), origin+orient(stop*m), padname = None)
    # resistor body
    start = np.array([-x1, -y2, 20e-6*zm])
    stop  = np.array([ x1,  y2, (thickness - 20e-6)*zm])
    body = Box(dielectric, priority+1, origin+orient(start), origin+orient(stop), padname=None)
    # resistor element
    zoff = 0.0 if element_down else thickness - 20e-6
    start = np.array([-x2, -y3, zoff*zm])
    stop  = np.array([ x2, y3, (20e-6+zoff)*zm])
    Box(element, priority+1, origin+orient(start), origin+orient(stop), padname = None)

class Port(Object):
    def __init__(self, em, start, stop, direction, z, padname = None, layer = 'F.Cu', mirror = ''):
        self.em = em
        mirror = [-1 if 'x' in mirror else 1, -1 if 'y' in mirror else 1, 1]
        self.start = np.array(start)*mirror
        self.stop = np.array(stop)*mirror
        self.direction = direction
        self.z = z
        self.padname = padname
        self.layer = layer
        self.portnumber = len(em.ports)
        name = "p" + str(self.portnumber)
        em.objects[name] = self
        em.ports.append(self)
    def generate_octave(self):
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
        g.add_pad(self.padname,
                  layer = self.layer,
                  x = 500.0 * (self.start[0] + self.stop[0]), # mm
                  y = 500.0 * (self.start[1] + self.stop[1]), # mm
                  xsize = 1000.0 * abs(self.start[0] - self.stop[0]), # mm
                  ysize = 1000.0 * abs(self.start[1] - self.stop[1]))

class OpenEMS:
    def __init__(self, name, fmin=0, fmax=50e9,
                 NrTS=1e6,
                 EndCriteria=1e-6,
                 #BC = {xmin xmax ymin ymax zmin zmax};
                 boundaries = ['PEC', 'PEC', 'PEC', 'PEC', 'PEC', 'PEC'],
                 fsteps = 1601
    ):
        self.FDTD = openEMS(NrTS=NrTS, EndCriteria=EndCriteria)
        self.FDTD.SetGaussExcite((fmin+fmax)/2.0, (fmax-fmin)/2.0)
        self.FDTD.SetBoundaryCond(boundaries)
        self.CSX = ContinuousStructure()
        self.FDTD.SetCSX(self.CSX)
        self.mesh = self.CSX.GetGrid()
        self.mesh.SetDeltaUnit(1.0) # specify everything in m
        self.fmin = fmin
        self.fmax = fmax
        self.fsteps = fsteps
        self.objects = {}
        self.name = name
        self.ports = []
        self.excitation_port = 0
        self.excite_ports = [1]
        self.via_offset_x = 0.0
        self.via_offset_y = 0.0
        self.xgrid = None # for plot
        self.ygrid = None
        self.legend_location = 2 # upper left
        self.options = ''
        self.name_count = 0
        self.resolution = 0.0001

    def AddPort(self, start, stop, direction, z):
        return Port(self, start, stop, direction, z)

    def get_name(self, name):
        if name:
            return name
        self.name_count += 1
        return "pad_{}".format(self.name_count)

    def write_kicad(self, fpname, mirror=""):
        g = kicadfpwriter.Generator(fpname)
        g.mirror = mirror
        for object in self.objects:
            g.drill = 0
            self.objects[object].generate_kicad(g)
        fp = g.finish()
        with open(self.name+".kicad_mod", "w") as f:
            f.write(fp)

    def run_openems(self, options='view solve', z=50, initialize=True, show_plot=True, numThreads=8):
        cwd = os.getcwd()
        basename = cwd + '/' + self.name
        simpath = r'/tmp/openems_data' + self.name.split("/")[-1]
        if not os.path.exists(simpath):
            os.mkdir(simpath)

        for object in self.objects:
            self.objects[object].generate_octave()

        import collections.abc
        if not isinstance(self.resolution, collections.abc.Sequence):
            self.resolution = np.ones(3) * self.resolution

        ratio = 1.5
        for i in range(3):
            if self.resolution[i] is not None:
                self.mesh.SmoothMeshLines('xyz'[i], self.resolution[i], ratio)

        if 'view' in options:
                CSX_file = simpath + '/csx.xml'
                self.CSX.Write2XML(CSX_file)
                os.system(r'AppCSXCAD "{}"'.format(CSX_file))
        if 'solve' in options:
            self.FDTD.Run(simpath, verbose=3, cleanup=True, numThreads=numThreads)
            f = np.linspace(self.fmin, self.fmax, self.fsteps)
            for p in self.ports:
                p.port.CalcPort(simpath, f, ref_impedance = z)
            nports = len(self.ports)

            s = []

            for p in range(nports):
                s.append(self.ports[p].port.uf_ref / self.ports[0].port.uf_inc)

            if nports < 1:
                return

            self.frequencies = f
            fig, ax = matplotlib.pyplot.subplots()
            s11 = s[0]
            if nports == 1:
                save_s1p(f, s11, basename+".s1p", z=z)
            if nports > 1:
                s21 = s[1]
                ax.plot(f/1e9, 20*np.log10(np.abs(s21)), label = 'dB(s21)')
                save_s2p_symmetric(f, s11, s21, basename+".s2p", z=z)
            ax.plot(f/1e9, 20*np.log10(np.abs(s11)), label = 'dB(s11)')
            if nports > 2:
                for i in range(2,nports):
                    ax.plot(f/1e9, 20*np.log10(np.abs(s[i])), label = f'dB(s{i+1}1)')

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
            if show_plot:
                matplotlib.pyplot.show()
            return s
