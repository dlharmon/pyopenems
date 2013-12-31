#!/usr/bin/env python

class OpenEMS():
    def __init__(self):
        self.octfile = ""
        self.max_timesteps = 1e6
        self.end_criteria = 1e-6
        self.fmax = 50e9
        self.fo = fmax/2
        self.fc = fmax/2
        self.f_0 = 32e9
    def add_line(self,l):
        self.octfile += l + "\n"
    def write_header(self,):
        self.add_line("close all")
        self.add_line("clear")
        self.add_line("clc")
        # setup the simulation
        self.add_line("unit = 1e-3;") # specify everything in mm
        # setup FDTD parameters & excitation function
        self.add_line("FDTD = InitFDTD({}, {});".format(self.max_timesteps, self.end_criteria))
        self.add_line("FDTD = SetGaussExcite(FDTD, {}, {});".format(self.fo, self.fc))
        #BC = {xmin xmax ymin ymax zmin zmax};
        self.add_line("FDTD = SetBoundaryCond(FDTD, {'PEC' 'PEC' 'PEC' 'PEC' 'PEC' 'PEC'});")
        # setup CSXCAD geometry & mesh
        self.add_line("CSX = InitCSX();")
    def add_metal(self, name):
        self.add_line("CSX = AddMetal( CSX, '{}' );".format(name))
    def add_material(self, name, eps_r, tanD=None, kappa=None):
        self.add_line("CSX = AddMaterial( CSX, '{}' );".format(name))
        if tanD:
            kappa = tanD * 2*pi*self.f_0 * epsilon_0 * eps_r;
        if kappa:
            self.add_line("CSX = SetMaterialProperty( CSX, '{}', 'Epsilon', {},  'Kappa', {});".format(name, eps_r, kappa))
        else:
            self.add_line("CSX = SetMaterialProperty( CSX, '{}', 'Epsilon', {});".format(name, eps_r))            
    def add_box(self, material, start, stop):
        self.add_line("CSX = AddBox( CSX, '{}', {}, {}, {});".format(material, priority, start, stop))        
    def add_port(self, n, z, start, stop, direction, excite):
        if direction == 'x':
            direction = [1, 0, 0]
        elif direction == 'y':
            direction = [0, 1, 0]
        elif direction == 'z':
            direction = [0, 0, 1]
        self.add_line("[CSX, port\{{}\}] = AddLumpedPort(CSX, 999, 1, {}, {}, {}, {}, {});".format(n, z, start, stop, direction, excite))


em = OpenEMS()
em.add_metal('r0')
em.add_metal('r1')
em.add_metal('r2')
eps_r = 3.0;
tanD = 0.0035;
em.add_material('substrate', eps_r, tanD=tanD)
CSX = AddMaterial( CSX, 'substrate' );

# substrate
start = [0.5*box_xsize, box_end, substrate_bottom];
stop  = start * [-1, -1, 0] + [0, 0, substrate_thickness];
em.add_box('substrate', 1, start, stop);

# port 1
start = [0.5*box_xsize, finger_0_y_0, substrate_top]
stop  = [2.5*finger_length, finger_0_y_1, foil_top]
z = 50
excite = 1
em.add_port(1, z, start, stop, 'x', excite)

max_epr = 4.00;
f_max = 50e9;
epsilon_0 = 8.854187817e-12;
mu_0 = 1.2566370614e-6;
foil_thickness = 0.035;
substrate_thickness = 0.508;
ms_air_above = 1.0;
f_0 = 36e9;

s0 = 0.25;
s1 = 0.15;
s2 = 0.25;
s3 = 0.3;
finger_width = 0.15;
finger_length = 2.6;
port_length = 0.2;
via = 0.5;
via_pad = 1.0;
# dimensions X
box_xsize = 5 * finger_length + 2*port_length;
# dimensions Y
finger_2_y_0 = 0.5*s3;
finger_2_y_1 = finger_2_y_0 + finger_width;
finger_1_y_0 = finger_2_y_1 + s2;
finger_1_y_1 = finger_1_y_0 + finger_width;
finger_0_y_0 = finger_1_y_1 + s1;
finger_0_y_1 = finger_0_y_0 + finger_width;
box_end = finger_0_y_1 + s0

# dimensions Z
substrate_bottom = 0.0;
substrate_top = substrate_bottom + substrate_thickness;
foil_top = substrate_top + foil_thickness;
housing_top = foil_top + ms_air_above;
resolution = c0/(f_max*sqrt(max_epr))/unit /50; % resolution of	% lambda/50





%finger 2
start = [-0.5*finger_length, finger_2_y_0, substrate_top];
stop  = [1.5*finger_length, finger_2_y_1, foil_top];
CSX = AddBox( CSX, 'r2', 9, start, stop );
CSX = AddBox( CSX, 'r2', 9, start.*[-1 -1 1], stop.*[-1 -1 1]);

%finger 1
start = [0.5*finger_length, finger_1_y_0, substrate_top];
stop  = [2.5*finger_length, finger_1_y_1, foil_top];
CSX = AddBox( CSX, 'r1', 9, start, stop );
CSX = AddBox( CSX, 'r1', 9, start.*[-1 -1 1], stop.*[-1 -1 1]);

%finger 0
start = [1.5*finger_length, finger_0_y_0, substrate_top];
stop  = [2.5*finger_length, finger_0_y_1, foil_top];
CSX = AddBox( CSX, 'r0', 9, start, stop );
CSX = AddBox( CSX, 'r0', 9, start.*[-1 -1 1], stop.*[-1 -1 1]);

# port 1
start = [0.5*box_xsize, finger_0_y_0, substrate_top];
stop  = [2.5*finger_length, finger_0_y_1, foil_top];
z = 50;
dir = [1 0 0];
excite = 1;
[CSX, port{1}] = AddLumpedPort(CSX, 999, 1, z, start, stop, dir, excite);

# port 2
start = [-1 -1 1] .* start;
stop  = [-1 -1 1] .* stop;
z = 50;
dir = [1 0 0];
excite = 0;
[CSX, port{2}] = AddLumpedPort(CSX, 999, 2, z, start, stop, dir, excite);

mesh = DetectEdges(CSX);
mesh.z = [mesh.z, housing_top]
mesh = SmoothMesh(mesh, resolution);
CSX = DefineRectGrid(CSX, unit, mesh);
 
%% write/show/run the openEMS compatible xml-file
Sim_Path = 'coax';
Sim_CSX = 'msl.xml';

[status, message, messageid] = rmdir( Sim_Path);#, 's' ); % clear previous directory
[status, message, messageid] = mkdir( Sim_Path ); % create empty simulation folder

WriteOpenEMS( [Sim_Path '/' Sim_CSX], FDTD, CSX );
CSXGeomPlot( [Sim_Path '/' Sim_CSX] );
RunOpenEMS( Sim_Path, Sim_CSX );
%% post-processing
close all
f = linspace( 1e6, f_max, 1601 );
port = calcPort( port, Sim_Path, f, 'RefImpedance', 50);

s11 = port{1}.uf.ref./ port{1}.uf.inc;
s21 = port{2}.uf.ref./ port{1}.uf.inc;
#s22 = port{2}.uf.ref./ port{2}.uf.inc;

plot(f/1e9,20*log10(abs(s11)),'k-','LineWidth',2);
hold on;
grid on;
plot(f/1e9,20*log10(abs(s21)),'r--','LineWidth',2);
legend('S_{11}','S_{21}');
ylabel('S-Parameter (dB)','FontSize',12);
xlabel('frequency (GHz) \rightarrow','FontSize',12);
ylim([-100 2]);

z11=(50.*(1-(abs(s11).^2)))./(1+(abs(s11).^2)-(2.*abs(s11).*cos(arg(s11))))+j*(2*abs(s11).*sin(arg(s11)*50)./(1+abs(s11).^2-2*abs(s11).*cos(arg(s11))));
