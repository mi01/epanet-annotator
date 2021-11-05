# EPANET Annotator
This tool allows visualizing a [EPANET](https://github.com/USEPA/EPANET2.2) water network (INP file) and adding a custom background layer (e.g. a satellite image). Additionaly simple operations like scaling and moving are possible. Subsequent annotations on the building infrastructure can be made on an overlay. The result can be saved to or loaded from a file in a JSON format. The tool is written in Python with Gtk/Cairo. Parsing the EPANET file is done with [WNTR](https://github.com/USEPA/WNTR).

![Screenshot](screenshot.png?raw=true)