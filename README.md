# loadandparse
a tool for processing g-code data
a basic python script for processing g-code data. 
Right now this is just a collection of functions with no real interface.
I just edit the function calls that I need and comment out the ones I don't

This is designed to read in the g-code as it is structured from my version of pstoedit
from https://github.com/mccoyspace/pstoedit

This tool can read in objects from a g-code file, scale, shift, rotate, sort (right/left/up/down or by size),
and give the bounding box of the drawing.

It writes the modified g-code out to a file.
