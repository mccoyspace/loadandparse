#!/usr/bin/env python3

global headerData
global minX
global minY
global maxX
global maxY


headerData=[] #store the gcode file's header data in a global for retrieval when we write out the final file
minX = 0.0
minY = 0.0
maxX = 0.1
maxY = 0.1

def loadandparse(theFile):

	global minX
	global minY
	global maxX
	global maxY
	global headerData

	listofObjlists = [] #the list of shapes in the drawing, each shape consists of a list of x,y points which themselves are a 2-item list of floats
	thisObjlist = [] #the working list of points for the current shape

	headerFlag=True #state variable that says we are dealing with header data before the first shape. a '\n' will stop header-mode
	print('loading file')
	with open(theFile, 'r') as file:
		filedata = file.readlines()

		#the logic of this is wholly dependent on the exact structure of the gcode as it is currently produced by my version of pstoedit for my plotter
		for a_line in filedata:
			if (headerFlag):
				if a_line.startswith('\n'): #if a blank line is found, the header is over
					headerFlag=False  #flip the header flag
				else:
					headerData.append(a_line)  #still in header mode, add the line to the list of headerData
				
				#this will trigger at the end of the header sequence, producing a 'bad' line, but a later pop() will knock that out
			if headerFlag == False:
				if a_line.startswith('\n'): #an emply line return signals the start of a discrete drawn object, so add current object list to the master list and reset
					listofObjlists.append(list(thisObjlist))  #add the list of points for this shape to the master list
					thisObjlist.clear()	 	#clear out the working list of points for the current shape
					#giveFeedback() #print a dot progress bar to indicate a shape has been read and added
				else:
					subline = a_line[3:-1].split(" ") #skips the 'G0 ' at the start of the line and the \n character at the end, then splits it into a val 1, val 2 list
					if len(subline) > 1: #makes sure we are dealing with x/y coords, not the single  S165 or F2000 type of commmand
						x_pos=subline[0] #the first eleemnt in the list is the xvalue
						y_pos=subline[1] #the second element in the list is the yvalue
						x_posNum=x_pos[1:] #trim off the X character at the beginning, leaving just the numbers
						y_posNum=y_pos[1:] #trim off the Y character at the beginning, leaving just the numbers

						finalX = round(float(x_posNum),2) #round down to two decimal places == one hundreth of a mm
						finalY = round(float(y_posNum),2) # and convert from string to float
						thisObjlist.append([finalX, finalY]) #add the points (as a 2-item list of floats) to the current shape list DONE!												
						calcMinMax(finalX, finalY)

	listofObjlists.pop(0) #gets rid of the remanant of the header. Now listofObjlists is clean and ready to go with only the shapes data
	return(listofObjlists)


def sortSize(theList, theDirection):
	print('sorting size')
	theList.sort(key = len, reverse = theDirection) #theDirection: True = bigger to smaller,,, False = smaller to bigger
	#giveFeedback()
	return(theList)

def sortDirection(theList, theAxis, theDirection):
	print('sorting direction')
	if (theAxis):
		for shape in theList:
			for coords in shape:
				coords.reverse()
				#giveFeedback()

	theList.sort(reverse=theDirection)

	if (theAxis):
		for shape in theList:
			for coords in shape:
				coords.reverse()
				#giveFeedback()
	return(theList)

def scaleShapes(theList, theMultipleX, theMultipleY):
	print('scaling shapes')
	resetMinMax()
	for shape in theList:
		for coords in shape:
			currentX = coords[0]
			currentY = coords[1]
			coords[0] = round(float(currentX * theMultipleX),2)
			coords[1] = round(float(currentY * theMultipleY),2)
			calcMinMax(coords[0], coords[1])
			#giveFeedback()
	return(theList)

def shiftShapes(theList, theOffsetX, theOffestY):
	print('shifting shapes')
	resetMinMax()
	for shape in theList:
		for coords in shape:
			currentX = coords[0]
			currentY = coords[1]
			coords[0] = round(float(currentX + theOffsetX),2)
			coords[1] = round(float(currentY + theOffestY),2)
			calcMinMax(coords[0], coords[1])
			#giveFeedback()
	return(theList)	

def rotate90(theList):
	print('rotating shapes')
	resetMinMax()
	for shape in theList:
			for coords in shape:
				coords.reverse()
				calcMinMax(coords[0], coords[1])
				#giveFeedback()
	return(theList)

def calcMinMax(theX, theY):
	global minX
	global minY
	global maxX
	global maxY

	if theX > maxX: 
		maxX = theX
	if theY > maxY:
		maxY = theY
	if theX < minX:
		minX = theX
	if theY < minY:
		minY = theY

def resetMinMax():
	global minX
	global minY
	global maxX
	global maxY

	minX = 0.0
	minY = 0.0
	maxX = 0.1
	maxY = 0.1

def giveFeedback():
	print('.', end='')
	#print('.')

def printHeader():
	global headerData
	for line in headerData:
		print(line, end='')
		#print(line)


def printGCode(theList):
	a_shapeData = []
	for shape in theList:
		print('\nM3 S165\n', end='')
		print('G0 F2000\n', end='')
		startCoords = shape[0]
		print ('G0 X'+str(startCoords[0])+' Y'+str(startCoords[1])+'\n', end='')
		print('M3 S148\n', end='')
		print('G0 F2000\n', end='')
		remainder = shape[1:-2] #select a sublist of everything except the first point pair, which were already processed above
		for coord in remainder:
			print ('G0 X'+str(coord[0])+' Y'+str(coord[1])+'\n', end='')
		lastCoords = shape[-1]
		print ('G0 X'+str(lastCoords[0])+' Y'+str(lastCoords[1]))
		#print('\n', end='')
	print('M3 S165\n\n')

def printObjectsList(theList):
	print('\n')
	print (str(len(theList))+ ' shapes:')		#print how mmany shapes there are
	#theList.sort()
	for shape in theList:
		print ('shape ' + str(objectsList.index(shape)+1)+':\n') #the n-th shape
		for coord in shape:
			print ('   '+str(coord[0])+','+ str(coord[1])) #step through all of the points in the shape, displaying them as x/y pairs
		print('\n')	

def printShapeCount(theList):
	theCount = 0
	print (str(len(theList))+ ' shapes:\n')		#print how mmany shapes there are
	for shape in theList:
		for coord in shape:
			theCount=theCount + 1
	print(str(theCount)+ ' points')

def printMinMax():
	global minX
	global minY
	global maxX
	global maxY
	print('min= ' + str(minX)+'mm, '+str(minY) + 'mm  max= '+ str(maxX)+'mm, '+str(maxY)+'mm')

def writeGCode(theList, theFile):
	print('writing file')
	global headerData

	with open(theFile, 'w') as file:
		for line in headerData:
			file.write(line)

		for shape in theList:
			file.write('\n')
			file.write('M3 S165\n')
			file.write('G0 F2000\n')
			startCoords = shape[0]
			file.write ('G0 X'+str(startCoords[0])+' Y'+str(startCoords[1])+'\n')
			file.write('M3 S148\n')
			file.write('G0 F2000\n')
			remainder = shape[1:-2] #select a sublist of everything except the first point pair, which were already processed above
			for coord in remainder:
				file.write ('G0 X'+str(coord[0])+' Y'+str(coord[1])+'\n')
			lastCoords = shape[-1]
			file.write ('G0 X'+str(lastCoords[0])+' Y'+str(lastCoords[1]))
			file.write('\n')
		file.write('M3 S165\n\n')

objectsList = loadandparse(theFile = '/Users/mccoy/Desktop/file.gcode')
#workingList = objectsList.copy()

sortDirection(objectsList, True, True) #first true/false = y-axis vs x-axis sort. second true/false = bigger location to smaller vs smaller location to bigger

#printObjectsList(objectsList)

#shiftShapes(objectsList, 30, -50) #x shift value in mm, y shift value in mm

#rotate90(objectsList)
#scaleShapes(objectsList, 0.3745, 0.2196) #x scale value, y scale value

#sortSize(objectsList, True) #theDirection: True = bigger to smaller,,, False = smaller to bigger
shiftShapes(objectsList, 67, 0)

#print('\n')
#printHeader()
#printObjectsList(objectsList)
#printMinMax()
#printGCode(objectsList)
#print('\n')
#printShapeCount(objectsList)
printMinMax()

writeGCode(objectsList, '/Users/mccoy/Desktop/output.gcode')
#print(workingList)
#print(objectsList)
#print('\n')
#print(newlist)

