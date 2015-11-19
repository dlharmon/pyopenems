#!/usr/bin/env python
import os
import numpy as np
import scipy.io
from scipy.constants import pi, c, epsilon_0, mu_0
mm = 0.001
import matplotlib.pyplot
import footgen

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


def openems_direction(direction):
    if 'x' in direction:
        return 0
    if 'y' in direction:
        return 1
    if 'z' in direction:
        return 2

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

class Dielectric(Material):
    def __init__(self, em, name, eps_r=1.0, kappa = None, ur=None):
        self.em = em
        self.name = name
        self.eps_r = eps_r
        self.ur = ur
        self.kappa = kappa
        self.type = 'dielectric'
        self.lossy = False # metal loss
        em.materials[name] = self
    def set_tanD(self, tanD, freq):
        self.kappa = tanD * 2*pi*freq * epsilon_0 * self.eps_r;
    # magnetic loss
    def generate_octave(self):
        retval = "CSX = AddMaterial( CSX, '{}' );\n".format(self.name)
        optionals = ""
        if self.ur:
            optionals += ", 'Mue', {}".format(self.ur)
        if self.kappa:
            optionals += ", 'Kappa', {}".format(self.kappa)
        retval += "CSX = SetMaterialProperty( CSX, '{}', 'Epsilon', {}{});\n".format(self.name, self.eps_r, optionals)
        return retval

class LumpedElement(Material):
    """ element_type = 'R' or 'C' or 'L' """
    def __init__(self, em, name, element_type='R', value=50.0, direction = 'x'):
        self.em = em
        self.name = name
        self.element_type = element_type
        self.value = value
        self.direction = direction
        em.materials[name] = self
    def generate_octave(self):
        return "CSX = AddLumpedElement( CSX, '{}', '{}', 'Caps', 0, '{}', {});\n".format(self.name, self.direction, self.element_type, self.value)

class Metal(Material):
    def __init__(self, em, name):
        self.lossy = False
        self.em = em
        self.name = name
        self.type = 'metal'
        em.materials[name] = self
    def generate_octave(self):
        return "CSX = AddMetal( CSX, '{}' );\n".format(self.name)


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
        em.materials[name] = self
    def generate_octave(self):
        return "CSX = AddConductingSheet( CSX, '{}', {}, {} );\n".format(self.name, self.conductivity, self.thickness)


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

from polygon import Polygon

class Box(Object):
    def __init__(self, em, name, material, priority, start, stop, padname = '1', layer='F.Cu'):
        self.priority = priority
        self.material = material
        self.start = np.array(start)
        self.stop = np.array(stop)
        self.em = em
        self.name = self.em.get_name(name)
        self.padname = padname
        self.layer = layer
        em.objects[self.name] = self
    def duplicate(self, name=None):
        return Box(self.em, name, self.material, self.priority, self.start, self.stop, self.padname)
    def generate_kicad(self, g):
        if self.em.materials[self.material].__class__.__name__ == 'Dielectric':
            return
        if self.padname == None:
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
        if self.em.materials[self.material].__class__.__name__ == 'LossyMetal':
            return self.generate_octave_lossy()
        octave = "CSX = AddBox(CSX, '{}', {}, {}, {});\n".format(self.material, self.priority, self.start, self.stop)
        return octave
    def generate_octave_lossy(self):
        #octave = "CSX = AddBox(CSX, '{}', {}, {}, {});\n".format('pec', self.priority, self.start, self.stop)
        octave = "CSX = AddBox(CSX, '{}', {}, {}, {});\n".format(self.material, self.priority, np.array([self.start[0], self.start[1], self.start[2]]), np.array([self.stop[0], self.stop[1], self.start[2]])) # bottom
        octave += "CSX = AddBox(CSX, '{}', {}, {}, {});\n".format(self.material, self.priority, np.array([self.start[0], self.start[1], self.stop[2]]), np.array([self.stop[0], self.stop[1], self.stop[2]])) # top
        octave += "CSX = AddBox(CSX, '{}', {}, {}, {});\n".format(self.material, self.priority, np.array([self.start[0], self.start[1], self.start[2]]), np.array([self.stop[0], self.start[1], self.stop[2]]))
        octave += "CSX = AddBox(CSX, '{}', {}, {}, {});\n".format(self.material, self.priority, np.array([self.start[0], self.stop[1], self.start[2]]), np.array([self.stop[0], self.stop[1], self.stop[2]]))
        octave += "CSX = AddBox(CSX, '{}', {}, {}, {});\n".format(self.material, self.priority, np.array([self.start[0], self.start[1], self.start[2]]), np.array([self.start[0], self.stop[1], self.stop[2]]))
        octave += "CSX = AddBox(CSX, '{}', {}, {}, {});\n".format(self.material, self.priority, np.array([self.stop[0], self.start[1], self.start[2]]), np.array([self.stop[0], self.stop[1], self.stop[2]]))
        return octave

class Cylinder(Object):
    def __init__(self, em, name, material, priority, start, stop, radius):
        self.material = material
        self.start = np.array(start)
        self.stop = np.array(stop)
        self.em = em
        self.name = self.em.get_name(name)
        self.radius = radius
        self.padname = '1'
        self.priority = priority
        em.objects[self.name] = self
    def duplicate(self, name=None):
        return Cylinder(self.em, name, self.material, self.priority, self.start, self.stop, self.radius)
    def generate_octave(self):
        octave = "CSX = AddCylinder(CSX, '{}', {}, {}, {}, {});\n".format(self.material, self.priority, self.start, self.stop, self.radius)
        return octave

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
        start = np.round(1000000.0*np.array([self.x + self.em.via_offset_x, self.y + self.em.via_offset_y, self.z[0][0]]))/1e6
        stop = np.round(1000000.0*np.array([self.x + self.em.via_offset_x, self.y + self.em.via_offset_y, self.z[0][1]]))/1e6
        octave = "CSX = AddCylinder(CSX, '{}', {}, {}, {}, {});\n".format(self.material, self.priority, start, stop, self.drillradius)
        for z in self.z[1:]:
            start = [self.x, self.y, z[0]]
            stop = [self.x, self.y, z[1]]
            octave += "CSX = AddCylinder(CSX, '{}', {}, {}, {}, {});\n".format(self.material, self.priority, start, stop, self.padradius)
        return octave

class Port(Object):
    def __init__(self, em, start, stop, direction, z, padname = None, layer = 'F.Cu'):
        self.em = em
        self.start = np.array(start)
        self.stop = np.array(stop)
        self.direction = direction
        self.z = z
        self.padname = padname
        self.layer = layer
        em.nports += 1
        self.portnumber = em.nports
        name = "p" + str(self.portnumber)
        em.objects[name] = self
    def duplicate(self):
        return Port(self.em, self.start, self.stop, self.direction, self.z, padname = self.padname, layer = self.layer)
    def generate_octave(self):
        dirtable = {'x': [1, 0, 0], 'y': [0, 1, 0], 'z': [0,0,1]};
        excite = 0
        if self.em.excitation_port == self.portnumber:
            excite = 1
        octave = "[CSX, port{{{}}}] = AddLumpedPort(CSX, 999, {}, {}, {}, {}, {}, {});\n".format(self.portnumber,self.portnumber,self.z,self.start,self.stop, openems_direction_vector(self.direction), excite)
        return octave
    def generate_kicad(self, g):
        if self.padname == None:
            return
        g.width = 1000.0 * abs(self.start[0] - self.stop[0]) # mm
        g.height = 1000.0 * abs(self.start[1] - self.stop[1])
        x = 500.0 * (self.start[0] + self.stop[0]) # mm
        y = 500.0 * (self.start[1] + self.stop[1]) # mm
        g.add_pad(x,y,self.padname, layer = self.layer)

class Mesh():
    def __init__(self):
        self.x = np.array([])
        self.y = np.array([])
        self.z = np.array([])
    def add_x(self, x):
        self.x = np.append(self.x, x)
    def add_y(self, y):
        self.y = np.append(self.y, y)
    def add_z(self, z):
        self.z = np.append(self.z, z)


class OpenEMS:
    def __init__(self, name, fmin=1e6, fmax=50e9):
        self.max_timesteps = 1e6
        self.end_criteria = 1e-6
        self.fmin = fmin
        self.fmax = fmax
        self.fsteps = 1601
        self.fc = (fmin+fmax)/2.0
        self.fo = self.fc-fmin
        self.f_0 = 32e9
        self.materials = {}
        self.objects = {}
        self.name = name
        self.nports = 0
        self.excitation_port = 1
        self.excite_ports = [1]
        self.directory = '.'
        self.boundaries = "'PEC' 'PEC' 'PEC' 'PEC' 'PEC' 'PEC'"
        self.sim_path = "openems_data"
        self.metalloss = False
        self.via_offset_x = 0.0
        self.via_offset_y = 0.0
        self.xgrid = None
        self.ygrid = None
        self.legend_location = 2 # upper left
        self.options = ''
        self.octave_mid = ''
        self.octave_end = ''
        self.name_count = 0
        try:
            os.mkdir(self.sim_path)
        except:
            pass
        self.resolution = 0.0001
        self.mesh = Mesh()
    def add_metal(self, name):
        print "add_metal is deprecated - use openems.Metal() directly"
        return Metal(self, name)
    def add_lossy_metal(self, name, conductivity=56e6, frequency=None, thickness=None, ur=1.0):
        print "add_lossy_metal is deprecated - use openems.LossyMetal() directly"
        return LossyMetal(self, name, conductivity, frequency, thickness, ur)
    def add_dielectric(self, name, eps_r=1.0, kappa = None, ur=1.0):
        print "add_dielectric is deprecated - use openems.Dielectric() directly"
        return Dielectric(self, name, eps_r, kappa, ur)
    def add_lumped(self, name, element_type='R', value=50.0, direction = 'x'):
        print "add_lumped is deprecated - use openems.LumpedElement() directly"
        return LumpedElement(self, name, element_type, value, direction)
    def add_box(self, name, material, priority, start, stop, padname='1'):
        print "add_box is deprecated - use openems.Box() directly"
        return Box(self, name, material, priority, start, stop, padname)
    def add_port(self, start, stop, direction, z):
        print "add_port is deprecated - use openems.Port() directly"
        return Port(self, start, stop, direction, z)
    def add_cylinder(self, name, material, priority, start, stop, radius):
        print "add_cylinder is deprecated - use openems.Cylinder() directly"
        return Cylinder(self, name, material, priority, start, stop, radius)
    def add_via(self, name, material, priority, x, y, z, drillradius, padradius, padname = '1'):
        print "add_via is deprecated - use openems.Via() directly"
        return Via(self, name, material, priority, x, y, z, drillradius, padradius, padname)
    def add_resistor(self, name, origin=np.array([0,0,0]), direction='x', value=100.0, invert=False, priority=9, dielectric_name='alumina', metal_name='pec', element_down=False):
        """ currently only supports 'x', 'y' for direction """
        element_name = name + "_element"
        LumpedElement(self, element_name, element_type='R', value = value, direction = direction)
        # resistor end caps
        start = np.array([-0.15*mm, -0.3*mm, 0])
        stop  = np.array([0.15*mm, -0.25*mm/2, 0.25*mm])
        cap1 = Box(self, name+"_end_cap", metal_name, priority, start, stop, padname = None)
        cap2 = cap1.duplicate(name+"+_end_cap2")
        cap2.mirror('y')
        # resistor body
        start = np.array([-0.15, -0.27, 0.02])*mm
        stop  = np.array([0.15, 0.27, 0.23])*mm
        body = Box(self, name+"_body", dielectric_name, priority + 1, start, stop, padname = None)
        # resistor element
        if element_down:
            zoff = 0.0
        else:
            zoff = 0.23
        start = np.array([-0.1, -0.25/2, 0+zoff])*mm
        stop  = np.array([0.1, 0.25/2, 0.02+zoff])*mm
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
        octave = self.generate_octave_header()
        for material in self.materials:
            octave += self.materials[material].generate_octave()
        for object in self.objects:
            octave += self.objects[object].generate_octave()
        octave += self.generate_octave_footer(options)
        with open(self.sim_path+"/sim.m", "w") as f:
            f.write(octave)
        os.system("rm -f {}".format(self.sim_path + "ABORT"))
        os.system("octave {}".format(self.sim_path + "/sim.m"))
        if 'solve' in options:
            if self.nports < 1:
                return
            s = scipy.io.loadmat(self.sim_path + "/sim.mat")
            self.frequencies = s['f'][0]
            self.s11 = s['s11'][0]
            fig, ax = matplotlib.pyplot.subplots()
            if self.nports > 1:
                self.s21 = s['s21'][0]
                ax.plot(self.frequencies/1e9, 20*np.log10(np.abs(self.s21)), label = 'dB(s21)')
            ax.plot(self.frequencies/1e9, 20*np.log10(np.abs(self.s11)), label = 'dB(s11)')
            if self.nports > 2:
                self.s31 = s['s31'][0]
                ax.plot(self.frequencies/1e9, 20*np.log10(np.abs(self.s31)), label = 'dB(s31)')
            if self.nports > 3:
                self.s41 = s['s41'][0]
                ax.plot(self.frequencies/1e9, 20*np.log10(np.abs(self.s41)), label = 'dB(s41)')
            if self.nports > 1:
                save_s2p_symmetric(self.frequencies, self.s11, self.s21, self.name+".s2p")
            ax.set_xlabel('Frequency (GHz)')
            ax.set_ylabel('dB')
            if self.xgrid != None:
                ax.set_xticks(self.xgrid)
            if self.ygrid != None:
                ax.set_yticks(self.ygrid)
            ax.grid(True)
            fig.tight_layout()
            ax.legend(loc=self.legend_location)
            matplotlib.pyplot.savefig(self.name+".png")
            matplotlib.pyplot.savefig(self.name+".svg")
            matplotlib.pyplot.savefig(self.name+".pdf")
            matplotlib.pyplot.show()
            print(len(self.frequencies))
            print(s)
            # print os.system("/home/dlharmon/software/openEMS/openEMS/openEMS {}".format(filename+".xml"))

    def generate_octave_header(self):
        #oh = "close all\nclear\nclc\n"
        oh = "unit = 1.0;\n" # specify everything in m
        oh += "FDTD = InitFDTD('NrTS', {}, 'EndCriteria', {});\n".format(self.max_timesteps, self.end_criteria)
        if not 'no_excite' in self.options:
            oh += "FDTD = SetGaussExcite(FDTD, {}, {});\n".format(self.fo, self.fc)
        #BC = {xmin xmax ymin ymax zmin zmax};
        oh += "FDTD = SetBoundaryCond(FDTD, {{{}}});\n".format(self.boundaries)
        oh += "CSX = InitCSX();\n" # setup CSXCAD geometry & mesh
        return oh

    def generate_octave_footer(self, options=None):
        if not 'no_detect_edges' in self.options:
            footer = "mesh = DetectEdges(CSX);\n"
        else:
            footer = "mesh.x = [];\n"
            footer += "mesh.y = [];\n"
            footer += "mesh.z= [];\n"
        #if self.mesh.z:
        footer += "mesh.x = [mesh.x, {}];\n".format(np.array(self.mesh.x).tolist())
        footer += "mesh.y = [mesh.y, {}];\n".format(np.array(self.mesh.y).tolist())
        footer += "mesh.z = [mesh.z, {}];\n".format(np.array(self.mesh.z).tolist())
        if not 'no_smooth_mesh' in self.options:
            footer += "mesh = SmoothMesh(mesh, {});\n".format(self.resolution)
        footer += "CSX = DefineRectGrid(CSX, unit, mesh);\n"
        footer += self.octave_mid
        footer += "WriteOpenEMS('{}', FDTD, CSX );\n".format(self.sim_path + "/csx.xml")
        if 'view' in options:
            footer += "CSXGeomPlot('{}');\n".format(self.sim_path + "/csx.xml")
        if 'solve' in options:
            if 'remote' in options:
                footer += "Settings.SSH.host = 'dlharmon@dlhdesktop';\n"
                footer += "Settings.SSH.bin = '/home/dlharmon/software/openEMS/bin/openEMS.sh';\n"
                footer += "RunOpenEMS('{}', '{}', '{}', Settings);\n".format(self.sim_path, "csx.xml", "")
            else:
                footer += "RunOpenEMS('{}', '{}');\n".format(self.sim_path, "csx.xml")
            footer += "close all\n"
            footer += "f = linspace({},{},{});\n".format(self.fmin, self.fmax, self.fsteps)
            if self.nports > 1:
                footer += "port = calcPort( port, '{}', f);\n".format(self.sim_path)
            ports = ""
            for p in range(self.nports):
                zratio = np.sqrt(self.objects["p" + str(self.excitation_port)].z / self.objects["p" + str(p+1)].z)
                footer += "s{0}{1} = {2} * port{{{0}}}.uf.ref./ port{{{1}}}.uf.inc;\n".format(p+1, self.excitation_port, zratio)
                ports += "s{}{} ".format(p+1, self.excitation_port)
            if self.nports > 0:
                footer += "save {} f {} -mat4-binary\n".format(self.sim_path+"/sim.mat", ports)
            footer += self.octave_end

        return footer
