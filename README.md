# pyopenems

A wrapper for the OpenEMS FDTD solver adding Kicad footprint generation for the simulated object.

This is mostly an internal tool at Harmon Instruments and is likely to have the interfaces change at any time.

## [Examples](examples)

## Dependencies
### [OpenEMS](http://openems.de) > 0.35  with Python support.

Install on Debian Buster:

There is currently no installer, you need to place the repo somewhere in your python path.

```bash
 sudo apt build-dep openems
 sudo apt install cython3 build-essential cython3 python3-numpy python3-matplotlib
 sudo apt install python3-scipy python3-h5py

 git clone https://github.com/thliebig/openEMS-Project.git
 cd openEMS-Project
 git submodule init
 git submodule update
 export OPENEMS=$HOME/software/openems
 ./update_openEMS.sh $OPENEMS
 cd CSXCAD/python; python3 setup.py build_ext -I$OPENEMS/include -L$OPENEMS/lib -R$OPENEMS/lib; sudo python3 setup.py install; cd ../..
 cd openEMS/python; python3 setup.py build_ext -I$OPENEMS/include -L$OPENEMS/lib -R$OPENEMS/lib; sudo python3 setup.py install; cd ../..
 ```

Install on Ubuntu 18.04 (user submitted):

instead of `sudo apt build-dep openems`

```bash
sudo apt install libtinyxml-dev libhdf5-serial-dev libcgal-dev vtk6 libvtk6-qt-dev
sudo python3 -m pip install --upgrade pip
sudo python3 -m pip install vtk scipy matplotlib h5py
```