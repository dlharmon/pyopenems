# pyopenems

A wrapper for the OpenEMS FDTD solver adding Kicad footprint generation for the simulated object.

This is mostly an internal tool at Harmon Instruments and is likely to have the interfaces change at any time.

## Dependencies
### [OpenEMS](http://openems.de) > 0.35  with Python support.

Install on Debian Buster:

```bash
 sudo apt build-dep openems
 git clone https://github.com/thliebig/openEMS-Project.git
 cd openEMS-Project
 export OPENEMS=$HOME/software/openems
 ./update_openEMS.sh $OPENEMS
 cd CSXCAD/python; python3 setup.py build_ext -I$OPENEMS/include -L$OPENEMS/lib -R$OPENEMS/lib; sudo python3 setup.py install
 cd openEMS/python; python3 setup.py build_ext -I$OPENEMS/include -L$OPENEMS/lib -R$OPENEMS/lib; sudo python3 setup.py install
 ```
