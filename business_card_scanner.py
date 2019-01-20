import cv2
import imutils
import time
import numpy as np
import io


import urllib.request
import firebase_admin
from firebase_admin import credentials, firestore, storage
import json


def download_file():
	
	my_url = "https://firebasestorage.googleapis.com/v0/b/businesscard-3b1f6.appspot.com/o/card1.jpg?alt=media"
	while True:
		try:
			loader = urllib.request.urlretrieve(my_url, "image.jpg")
			break
		except urllib.error.URLError as e:
			pass
		else:
			print(loader)
		##time.sleep(0.2)


## crops the rectangle from the rest of the image and returns cropped section
def cropRects(file, rotate = True):
	img = cv2.imread(file)
	if rotate:
		img = imutils.rotate_bound(img, 90)
	##img = cv2.resize(img,(384,512))
	##cv2.imwrite("resized.jpg",img)

	#time.sleep(10)
	h,w,c = img.shape
	area = h*w ## area of image
	## preprocessing and finding contours
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	ret,thresh = cv2.threshold(gray,127,255,1)
	contours,hierarchy = cv2.findContours(thresh,1,2)
	imgcrops = []
	##print (len(contours))
	for cnt in contours:
		approx = cv2.approxPolyDP(cnt,0.01*cv2.arcLength(cnt,True),True) ## approx vertices for each contour			
		if len(approx) == 4 and cv2.contourArea(cnt) > 10000 and int(cv2.contourArea(cnt)) < area-2000:
			print (cv2.contourArea(cnt), len(approx), area)

			cv2.drawContours(img,[cnt],0,255,1)
			(coord) = np.where(img == 255)

			(topx, topy) = (np.min(coord[0]), np.min(coord[1]))
			(bottomx, bottomy) = (np.max(coord[0]), np.max(coord[1]))

			if bottomx == 1023:
				continue
			##print "hit"
			imgcrop = img[topx:bottomx, topy:bottomy]
			
			imgcrops.append(imgcrop)
			
			height, width = bottomx-topx, bottomy-topy

			#print topx,bottomx
			#print math.atan()

			cv2.imwrite("imgcrop.jpg",imgcrop)


	return imgcrops if imgcrops != [] else None

def detectText(path):
	"""Detects text in the file."""
	from google.cloud import vision
	client = vision.ImageAnnotatorClient()

	with io.open(path, 'rb') as image_file:
		content = image_file.read()

	image = vision.types.Image(content=content)

	response = client.text_detection(image=image)
	texts = response.text_annotations
	##print('Texts:')
	
	t = []
	for text in texts:
		##print('\n"{}"'.format(text.description))
		t.append(text.description)
		vertices = ([(vertex.x,vertex.y) for vertex in text.bounding_poly.vertices])
		##print('bounds: {}'.format(','.join(map(str,vertices))))

	return t

def binsearch(target, array):
	lower = 0
	upper = len(array)
	while lower < upper:   # use < instead of <=
		x = lower + (upper - lower) // 2
		val = array[x].strip()
		if target == val:
			return True
		elif target > val:
			if lower == x:   # these two are the actual lines
				return False        
			lower = x
		elif target < val:
			upper = x


def sortIntoCats(t):
	text = t[0].strip().split("\n")
	print (text)
	def hasNumbers(input): 
	## checks if string has numbers
		return any(char.isdigit() for char in input)

	def makeNumbers(input):
		## makes new string with only numbers
		output = ""
		for x in input:
			if x.isdigit():
				output = output + x
		return output

	def checkEmail(input):
		## checks if valid email address
		output = None
		if " " in input:
			output = input[:input.index(" ")]
		elif "." in input: 
			output = input[:input.index(".")]
		if output == None:
			return output
		output = output + ".com"
		return output

	## gets name, phone, email, company
	#text = [x.split() for x in text]
	info = {} ## order of info: name, phone number, email, company

	names = open("sortednames.txt","r").readlines()
	companies = open("companies.txt","r").readlines()
	streets = open("streetnames.txt","r").readlines()

	for item in text:
		split = item.split()

		if binsearch(split[0].lower(), names): ## if first name is in database of names
			info["name"] = " ".join([x for x in split if any(y.isalpha() for y in x)])
		
		if "@" in item: ## if item is emai
			check = checkEmail(item.split()[0])
			if not check == None:
				info["email"] = check

		elif hasNumbers(item) and "f" not in item and "F" not in item: ## if item phone number
			info["number"] = makeNumbers("".join([x for x in split if any(y.isdigit() for y in x)]))
		
		elif "llc" in item.lower() or "inc" in item.lower() or binsearch(split[0].lower(), companies): ## if item is in company database
			info["company"] = " ".join([x for x in split if any(y.isalpha() for y in x)])

	

	return info



# detect card and crop it 


import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'googleapikey.json'
my_url = "https://firebasestorage.googleapis.com/v0/b/businesscard-3b1f6.appspot.com/o/card1.jpg?alt=media"

cred=credentials.Certificate('businesscard-3b1f6-firebase-adminsdk-5ra2x-82a43c6ea4.json')
firebase_admin.initialize_app(cred, {
	'storageBucket': 'businesscard-3b1f6.appspot.com'
})
db = firestore.client()

while True:
	download_file()


	cropRects("image.jpg")
	os.remove("image.jpg")

	text = detectText("imgcrop.jpg")
	data = sortIntoCats(text)
	print (data, "DATA!!!!!")
	bucket = storage.bucket()
	blob = bucket.blob('contact.json')

	with open("contact.json","w") as file:
		json.dump(data,file)

	outfile='contact.json'
	blob.upload_from_filename(outfile)
	
	#blob.delete()
	

	b = bucket.blob('imgcrop.jpg')

	outfile = 'imgcrop.jpg'
	b.upload_from_filename(outfile)
	#b.delete()
	time.sleep(0.2)


"""
cropRects("movers1.jpg",False)

text = detectText("imgcrop.jpg")
data = sortIntoCats(text)
print (data)
"""

