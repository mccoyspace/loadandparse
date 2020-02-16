#!/usr/bin/env python3

import random
import math

##### GLOBAL VARIABLES #####

global headerData #list that contains the header portion of the gcode file data, before the first object's coordinates
global objectsList #a list of objects, each object is a list of 2 coordinate values, themselves stored as a list
global splitObjectsList #a list of objects cut out from the main list according to different criteria
global minX # X axis coordinate of the lowest most drawing mark
global minY # Y axis coordinate of the lowest most drawing mark
global maxX # X axis coordinate of the highest most drawing mark
global maxY # Y axis coordinate of the highest most drawing mark
global dimX # X axis dimension of the drawing's bounding box natively in mm
global dimY # Y axis dimension of the drawing's bounding box natively in mm
global totalDistance # the total distance of all line seqments in mm

####### INITIAL VALUES #######

headerData=[] #store the gcode file's header data in a global for retrieval when we write out the final file
splitObjectsList=[] #some functions cut out groups of objects based on various criteria. the cut ones are saved here
minX = 800.0 #this value should be the maximum drawable point on the X axis
minY = 1250.0 #this value should be the maximum drawable point on the Y axis
maxX = 0.1
maxY = 0.1
dimX = 0.1
dimY = 0.1
totalDistance = 0.0


###### READING FROM FILE FUNCTION  ##########

def loadandparse(theFile): #reads in gcode file. initial header data is stored in headerData global, file data reduced to distinct shapes stored as co-ord pairs

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

						finalX = round(float(x_posNum),1) #round down to two decimal places == one hundreth of a mm
						finalY = round(float(y_posNum),1) # and convert from string to float
						thisObjlist.append([finalX, finalY]) #add the points (as a 2-item list of floats) to the current shape list DONE!												
						calcMinMax(finalX, finalY)

	listofObjlists.pop(0) #gets rid of the remanant of the header. Now listofObjlists is clean and ready to go with only the shapes data

	return(listofObjlists)


###### SORTING FUNCTIONS ########

def sortSize(theList, theDirection): #shapes list is sorted from either bigger to smaller (True) or smaller to bigger (False)
	print('sorting size')
	theList.sort(key = len, reverse = theDirection) #theDirection: True = bigger to smaller,,, False = smaller to bigger
	#giveFeedback()
	return(theList)

def sortDirection(theList, theAxis, theDirection): #shapes list is sorted by either X or Y axis, from larger to smaller or smaller to larger
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


######## SCALING AND SHIFTING FUNCTIONS #########

def scaleToFitInd(theList, theSizeX, theSizeY): #scales drawing to fit dims specified in mm on each axis independently. if value=0 original co-ord is maintained
	print('scaling to fit independently')
	if theSizeX != 0:
		scaleFactorX = float(theSizeX/(maxX-minX)) 
	else: 
		scaleFactorX = 1.0 

	if theSizeY != 0:
		scaleFactorY = float(theSizeY/(maxY-minY))  
	else: 
		scaleFactorY = 1.0 
	xOffset = minX
	yOffset = minY
	resetMinMax()
	for shape in theList:
		for coords in shape:
			if scaleFactorX != 1.0:
				currentX = coords[0] - xOffset
				coords[0] = round(float(currentX * scaleFactorX),1)
			if scaleFactorY != 1.0:
				currentY = coords[1] - yOffset
				coords[1] = round(float(currentY * scaleFactorY),1)
			calcMinMax(coords[0], coords[1])

def scaleToFitProp(theList, theSizeX, theSizeY): #scales drawing to fit dims specified in mm on each axis proportionally. value=0 is the follow axis
	print('scaling to fit proportionally')
	if theSizeX != 0:
		scaleFactorX = float(theSizeX/(maxX-minX)) 

	if theSizeY != 0:
		scaleFactorY = float(theSizeY/(maxY-minY)) 

	xOffset = minX
	yOffset = minY
	resetMinMax()
	for shape in theList:
		for coords in shape:
			currentX = coords[0] - xOffset
			currentY = coords[1] - yOffset
			if theSizeX != 0:
				coords[0] = round(float(currentX * scaleFactorX),1)
				coords[1] = round(float(currentY * scaleFactorX),1) + round(float(yOffset*(1/scaleFactorX)))
			if theSizeY != 0:
				coords[1] = round(float(currentY * scaleFactorY),1)
				coords[0] = round(float(currentX * scaleFactorY),1) + round(float(xOffset*(1/scaleFactorY)))
			calcMinMax(coords[0], coords[1])


def scaleShapes(theList, theMultipleX, theMultipleY): #scales drawing independently along X and Y axis (<1=shrink| <0=scale with mirror)
	print('scaling shapes')
	resetMinMax()
	for shape in theList:
		for coords in shape:
			currentX = coords[0]
			currentY = coords[1]
			coords[0] = round(float(currentX * theMultipleX),1)
			coords[1] = round(float(currentY * theMultipleY),1)
			calcMinMax(coords[0], coords[1])
			#giveFeedback()
	return(theList)

def shiftShapes(theList, theOffsetX, theOffestY): #shifts the drawing pos/neg along X/Y axis in mm
	print('shifting shapes')
	resetMinMax()
	for shape in theList:
		for coords in shape:
			currentX = coords[0]
			currentY = coords[1]
			coords[0] = round(float(currentX + theOffsetX),1)
			coords[1] = round(float(currentY + theOffestY),1)
			calcMinMax(coords[0], coords[1])
			#giveFeedback()
	return(theList)	


####### ROTATING AND FLIPPING FUNCTIONS ########

def mirror90(theList): #reflects the drawing 90 degrees clockwise, Y axis mirrors/reverses (probs not so useful)
	print('mirroring shapes')
	resetMinMax()
	for shape in theList:
			for coords in shape:
				coords.reverse()
				calcMinMax(coords[0], coords[1])
				#giveFeedback()
	return(theList)


def rotate90(theList): #rotates the drawing 90 degrees clockwise, no mirroring
	print('rotating shapes')
	tempMinX=minX
	tempMinY=minY
	tempMaxX=maxX
	tempMaxY=maxY
	resetMinMax()
	if (maxX >= maxY):
		for shape in theList:
			for coords in shape:
				currentX = coords[0]
				currentY = coords[1]
				coords[1] = (round(float(currentX * -1),1))+(tempMaxX+tempMinX)
				coords[0] = round(float(currentY * 1),1)
				calcMinMax(coords[0], coords[1])
	else:
		for shape in theList:
			for coords in shape:
				currentX = coords[0]
				currentY = coords[1]
				coords[0] = (round(float(currentY * -1),1))+(tempMaxY+tempMinY)
				coords[1] = round(float(currentX * 1),1)
				calcMinMax(coords[0], coords[1])
	return(theList)


###### PRUNING AND SPLITING FUNCTIONS ########

def pruneShapes(theList, cutoff):    #deletes shapes with point counts that fall below a given cutoff value. ie 'delete the specs'
	global objectsList               #pruned objects are NOT saved. The data is lost. Cut/split objects (not this function) are saved
	print('pruning shapes smaller than '+str(cutoff))
	tempList = []
	for shape in theList:
		#print(len(shape))
		if (len(shape)>=cutoff):
			tempList.append(shape)
			#print('added')
	#print(len(tempList))
	objectsList.clear()
	objectsList=tempList.copy()
	tempList.clear()

def splitSizes(theList, cutoff): #shapes list is split into 2 lists based on the number of points in the shape
	global objectsList           #bigger objects are stored here
	global splitObjectsList      #smaller objects are stored here
	print('spliting out shapes smaller than '+str(cutoff))
	tempListBig = []
	tempListSmall = []
	for shape in theList:
		#print(len(shape))
		if (len(shape)>cutoff):
			tempListBig.append(shape)
		else:
			tempListSmall.append(shape)
			#print('added')
	#print(len(tempList))
	objectsList.clear()
	splitObjectsList.clear()
	objectsList=tempListBig.copy()
	splitObjectsList=tempListSmall.copy()
	tempListBig.clear()
	tempListSmall.clear()

def splitXLoc(theList, cutoff): #shapes list is split into 2 lists based on whether or not the shape starts at a specific X axis location (useful...??)
	global objectsList           #objects beginning at or above the cutoff point are stored here
	global splitObjectsList      #objects beginning below the cutoff point are stored here
	print('spliting out shapes that begin on the x-axis at or below '+str(cutoff))
	tempListBig = []
	tempListSmall = []
	for shape in theList:
		#print(shape[0][0])
		if (shape[0][0]>=cutoff):
			tempListBig.append(shape)
		else:
			tempListSmall.append(shape)
			#print('added')
	#print(len(tempList))
	objectsList.clear()
	splitObjectsList.clear()
	objectsList=tempListBig.copy()
	splitObjectsList=tempListSmall.copy()
	tempListBig.clear()
	tempListSmall.clear()

def splitYLoc(theList, cutoff): #shapes list is split into 2 lists based on whether or not the shape starts at a specific Y axis location (useful...??)
	global objectsList           #objects beginning at or above the cutoff point are stored here
	global splitObjectsList      #objects beginning below the cutoff point are stored here
	print('spliting out shapes that begin on the y-axis at or below '+str(cutoff))
	tempListBig = []
	tempListSmall = []
	for shape in theList:
		#print(shape[0][0])
		if (shape[0][1]>=cutoff):
			tempListBig.append(shape)
		else:
			tempListSmall.append(shape)
			#print('added')
	#print(len(tempList))
	objectsList.clear()
	splitObjectsList.clear()
	objectsList=tempListBig.copy()
	splitObjectsList=tempListSmall.copy()
	tempListBig.clear()
	tempListSmall.clear()

def splitRandom(theList): #shapes list is split into 2 lists randomly
	global objectsList           
	global splitObjectsList      
	print('spliting out shapes randomly')
	tempListBig = []
	tempListSmall = []
	for shape in theList:
		#print(len(shape))
		if (random.randint(1,101)>50):
			tempListBig.append(shape)
		else:
			tempListSmall.append(shape)
			#print('added')
	#print(len(tempList))
	objectsList.clear()
	splitObjectsList.clear()
	objectsList=tempListBig.copy()
	splitObjectsList=tempListSmall.copy()
	tempListBig.clear()
	tempListSmall.clear()


###### CALCULATING AND ANALYZING FUNCTIONS #######

def calcMinMax(theX, theY): #calculates the min and max drawing coordinate loaction for X and Y and calcs the drawing bounding box
	global minX
	global minY
	global maxX
	global maxY
	global dimX
	global dimY

	if theX > maxX: 
		maxX = theX
	if theY > maxY:
		maxY = theY
	if theX < minX:
		minX = theX
	if theY < minY:
		minY = theY

	dimX = round((maxX - minX),2)
	dimY = round((maxY - minY),2)

def resetMinMax(): #zeros out the global min/max variables as part of re-calculating them
	global minX
	global minY
	global maxX
	global maxY
	global dimX
	global dimY

	minX = 800.0
	minY = 1250.0
	maxX = 0.1
	maxY = 0.1
	dimX = 0.1
	dimY = 0.1

def calculateDistance(theList): #uses Pythagorus to calculate the cumulative length of all the line segments in the drawing. to estimate ink usage
	print('calculating total distance')
	global totalDistance
	runningTally = 0.0
	for shape in theList:
		for coord in range(len(shape[:-1])):
			runningTally += math.sqrt(math.pow(shape[coord][0]-shape[coord+1][0],2)+math.pow(shape[coord][1]-shape[coord+1][1],2))
	totalDistance = round(runningTally,1)

def analyzeShapes(theList):  #prints a count of how many shapes of different point counts there are, quantized to set bucket sizes
	print('analyzing shapes')
	shapesDict={}
	quantizedTally={
		9000: 0,
		1000: 0,
		500: 0,
		400: 0,
		300: 0,
		250: 0,
		200: 0,
		150: 0,
		100: 0,
		50: 0,
		10: 0
	}

	for shape in theList:
		theKey = len(shape)
		if theKey in shapesDict:
			thisCount = shapesDict.get(theKey)
			newCount = thisCount + 1
			shapesDict[theKey] = newCount
		else:
			shapesDict[theKey] = 1


	for pointsInShape, theTally in shapesDict.items():
		
		if pointsInShape<=10:
			thisCount = quantizedTally.get(10)
			newCount = thisCount + theTally
			quantizedTally[10] = newCount	
		elif pointsInShape<=50:
			thisCount = quantizedTally.get(50)
			newCount = thisCount + theTally
			quantizedTally[50] = newCount	
		elif pointsInShape<=100:
			thisCount = quantizedTally.get(100)
			newCount = thisCount + theTally
			quantizedTally[100] = newCount	
		elif pointsInShape<=150:
			thisCount = quantizedTally.get(150)
			newCount = thisCount + theTally
			quantizedTally[150] = newCount
		elif pointsInShape<=200:
			thisCount = quantizedTally.get(200)
			newCount = thisCount + theTally
			quantizedTally[200] = newCount
		elif pointsInShape<=250:
			thisCount = quantizedTally.get(250)
			newCount = thisCount + theTally
			quantizedTally[250] = newCount
		elif pointsInShape<=300:
			thisCount = quantizedTally.get(300)
			newCount = thisCount + theTally
			quantizedTally[300] = newCount
		elif pointsInShape<=400:
			thisCount = quantizedTally.get(400)
			newCount = thisCount + theTally
			quantizedTally[400] = newCount
		elif pointsInShape<=500:
			thisCount = quantizedTally.get(500)
			newCount = thisCount + theTally
			quantizedTally[500] = newCount
		elif pointsInShape<=1000:
			thisCount = quantizedTally.get(1000)
			newCount = thisCount + theTally
			quantizedTally[1000] = newCount
		else:
			thisCount = quantizedTally.get(9000)
			newCount = thisCount + theTally
			quantizedTally[9000] = newCount

	for pointsInShape, theTally in quantizedTally.items():
		print ('up to '+ str(pointsInShape) +' points: ', theTally)


###### PRINTING AND INTERFACE FUNCTIONS ########

def giveFeedback(): #a rudimentary progress bar. not really so useful
	print('.', end='')
	#print('.')

def printHeader(): #prints the file header data to the console output
	global headerData
	for line in headerData:
		print(line, end='')
		#print(line)


def printGCode(theList): #prints to screen the reconstituted gcode data from the co-ordinate values of the objects list. this output should match the input structure
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

def printObjectsList(theList): #print the list of objects with their individual co-ord pairs -- useful for debugging
	print('\n')
	print (str(len(theList))+ ' shapes:')		#print how mmany shapes there are
	#theList.sort()
	for shape in theList:
		print ('shape ' + str(objectsList.index(shape)+1)+':\n') #the n-th shape
		for coord in shape:
			print ('   '+str(coord[0])+','+ str(coord[1])) #step through all of the points in the shape, displaying them as x/y pairs
		print('\n')	

def printShapeCount(theList): #prints the current total number of shapes and the current total number of x,y points
	theCount = 0
	print (str(len(theList))+ ' shapes:\n')		#print how mmany shapes there are
	for shape in theList:
		for coord in shape:
			theCount=theCount + 1
	print(str(theCount)+ ' points')

def printMinMax(): #prints the minimum and maximun drawing point for both X and Y axis. also prints the dims of the drawing's bounding box in mm and inches
	global minX
	global minY
	global maxX
	global maxY
	print('min= ' + str(minX)+'mm, '+str(minY) + 'mm  max= '+ str(maxX)+'mm, '+str(maxY)+'mm')
	print('drawing dimension: '+str(dimX)+'mm by '+str(dimY)+'mm')
	print('drawing dimension: '+str(round(dimX/25.4,2))+'in by '+str(round(dimY/25.4,2))+'in\n')


###### WRITING TO FILE FUNCTION ########

def writeGCode(theList, theFile): #writes the current contents of the shapes list out to a gcode file approprate for my plotter. includes header data
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



###### all functions ######                            #DESCRIPTIONS
#  loadandparse(theFile)                               #reads in gcode file. initial header data is stored in headerData global, file data reduced to distinct shapes stored as co-ord pairs
#  sortSize(theList, theDirection)                     #shapes list is sorted from either bigger to smaller (True) or smaller to bigger (False)
#  sortDirection(theList, theAxis, theDirection)       #shapes list is sorted by either X or Y axis, from larger to smaller or smaller to larger
#  scaleToFitInd(theList, theSizeX, theSizeY)          #scales drawing to fit dims specified in mm on each axis independently. if value=0 original co-ord is maintained
#  scaleToFitProp(theList, theSizeX, theSizeY)         #scales drawing to fit dims specified in mm on each axis proportionally. value=0 is the follow axis
#  scaleShapes(theList, theMultipleX, theMultipleY)    #scales drawing independently along X and Y axis (<1=shrink, negative values=scale with mirror)
#  shiftShapes(theList, theOffsetX, theOffestY)        #shifts the drawing pos/neg along X/Y axis in mm
#  mirror90(theList)                                   #reflects the drawing 90 degrees clockwise, Y axis mirrors/reverses (probs not so useful)
#  rotate90(theList)                                   #rotates the drawing 90 degrees clockwise, no mirroring
#  pruneShapes(theList, cutoff)                        #deletes shapes with point counts that fall below a given cutoff value. ie 'delete the specs'
#  splitSizes(theList, cutoff):                        #shapes list is split into 2 lists based on the number of points in the shape
#  splitXLoc(theList, cutoff):                         #shapes list is split into 2 lists based on whether or not the shape starts at a specific X axis location (useful...??)
#  splitYLoc(theList, cutoff):                         #shapes list is split into 2 lists based on whether or not the shape starts at a specific Y axis location (useful...??)
#  splitRandom(theList):                               #shapes list is split into 2 lists randomly
#  calcMinMax(theX, theY):                             #calculates the min and max drawing coordinate loaction for X and Y and calcs the drawing bounding box
#  resetMinMax():                                      #zeros out the global min/max variables as part of re-calculating them
#  calculateDistance(theList):                         #uses Pythagorean theorem to calculate the cumulative length of all the line segments in the drawing. to estimate ink usage
#  analyzeShapes(theList):                             #prints a count of how many shapes of different point counts there are, quantized to set bucket sizes
#  giveFeedback():                                     #a rudimentary progress bar. not really so useful
#  printHeader():                                      #prints the file header data to the console output
#  printGCode(theList):                                #prints to screen the reconstituted gcode data from the co-ordinate values of the objects list. this output should match the input structure
#  printObjectsList(theList):                          #prints the list of objects with their individual co-ord pairs -- useful for debugging
#  printShapeCount(theList):                           #prints the current total number of shapes and the current total number of x,y points
#  printMinMax():                                      #prints the minimum and maximun drawing point for both X and Y axis. also prints the dims of the drawing's bounding box in mm and inches
#  writeGCode(theList, theFile):                       #writes the current contents of the shapes list out to a gcode file approprate for my plotter. includes header data

###### below are the function calls that actually do things you want to do. should always start with 'loadandparse' 
###### these are executed in order, the effects are cumulative, so order should be load, then rotate/shift/scale, then sort, then analyze/print/save....
objectsList = loadandparse(theFile = '/Users/mccoy/Desktop/joined.gcode')


#printObjectsList(objectsList)

#shiftShapes(objectsList, 30, -50) #x shift value in mm, y shift value in mm

printMinMax()

pruneShapes(objectsList,30)
rotate90(objectsList)
#scaleShapes(objectsList, 0.87, -1) #x scale value, y scale value
#sortDirection(objectsList, True, False) #first true/false = y-axis vs x-axis sort. second true/false = bigger location to smaller vs smaller location to bigger
scaleToFitProp(objectsList, 0, 1250)
analyzeShapes(objectsList)
printShapeCount(objectsList)
printMinMax()
calculateDistance(objectsList)
print(totalDistance)


