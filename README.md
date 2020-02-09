# loadandparse

a basic python script for processing g-code data. 
Right now this is just a collection of functions with no real interface.
I just edit the function calls that I need, comment out the ones I don't and run the script

This is designed to read in the g-code as it is structured from my version of pstoedit
from https://github.com/mccoyspace/pstoedit

This tool can: 

read in objects from a g-code file 

scale the drawing (independently in X/Y axis)

shift the drawing (pos/neg in X and Y)

rotate (90 degrees ccw)

sort the drawing order (from right to left/left to right/top to bottom/bottom to top)

sort drawing order by size (biggest to smallest/smallest to biggest)

calculate the bounding box of the drawing

count the total number of shapes and points


It writes the modified g-code out to a file.



to do: 


calculate total distance travelled to help estimate ink usage. 

scale to fit given paper sizes

split output to different files 

