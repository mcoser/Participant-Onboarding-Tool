import os
import time
import operator
import requests
import json
import csv
import datetime
import pymsgbox
import urllib2
import zipfile

start = time.time()

#Qualtrics globals
apiToken = #qualtrics api token
allSurvs =  []

#directory globals
RequestFile = #location of RequestFile.zip from Qualtrics API
ExtractLocation = #location where you want qualtrics files to be extracted to 
CanvasAutoExportPath = #path of canvas export files
SharedDriveTestLocation = #location on shared drive to test K drive connectivity

def getSurveys():
    #get the survv
    url = "https://az1.qualtrics.com/API/v3/surveys"
    survHeaders = {
        "content-type": "application/json",
        "x-api-token": apiToken,
        }

    payload = {}

    while url:
        r = requests.get(url, params=payload, headers=survHeaders)
        data = r.json()
        for x in data['result']['elements']:
            if ("Alt Email" in x['name']):
                survID = x['id']
                allSurvs.append(survID)
        url = data['result']['nextPage']

def gatherResponses(surveyID):
    

    #Setting user Parameters

    fileFormat = "json"

    #Setting static parameters
    requestCheckProgress = 0
    baseUrl = "https://az1.qualtrics.com/API/v3/responseexports/"
    qualREheaders = {
      "content-type": "application/json",
      "x-api-token": apiToken,
      }
    #Creating Data Export
    downloadRequestUrl = baseUrl
    downloadRequestPayload = '{"format":"' + fileFormat + '","surveyId":"' + surveyID + '"}'
    downloadRequestResponse = requests.post(downloadRequestUrl, data=downloadRequestPayload, headers=qualREheaders)
    print downloadRequestResponse
    progressId = downloadRequestResponse.json()["result"]["id"]
    print "Progress"
    print progressId
    print downloadRequestResponse.text
    print
    print

    #Checking on Data Export Progress and waiting until export is ready
    while requestCheckProgress < 100:
        requestCheckUrl = baseUrl + progressId
        requestCheckResponse = requests.get(requestCheckUrl, headers=qualREheaders)
        requestCheckProgress = requestCheckResponse.json()["result"]["percentComplete"]
        print "Download is " + str(requestCheckProgress) + " complete"

    #Downloading and unzipping file
    requestDownloadUrl = baseUrl + progressId + '/file'
    requestDownload = requests.get(requestDownloadUrl, headers=qualREheaders, stream=True)
    print requestDownload.json

    with open(RequestFile, "wb") as f:
        for chunk in requestDownload.iter_content(chunk_size=1024):
            f.write(chunk)
        f.close()

    zipfile.ZipFile(RequestFile).extractall(ExtractLocation)


def SharedDrive_on():
    try:
        os.listdir(SharedDriveTestLocation)
        return True
    except WindowsError:
        return False

def internet_on():
    try:
        urllib2.urlopen('https://www.google.com', timeout=15)
        return True
    except urllib2.URLError as err: 
        return False

token = #canvas token here
canHeaders = {'Authorization': 'Bearer {}'.format(token)}

def getAllCourseInfo():

    allCourses = {}


    progRefCSV = #reference csv file with programs and dates

    today = datetime.datetime.today()
    twoWeeks = datetime.timedelta(14)
    threeMnths = datetime.timedelta(90)
    with open(progRefCSV) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            startDateRef = datetime.datetime.strptime(row['Program Session - Program Session Start Date'], "%d-%b-%y")
            endDateRef = datetime.datetime.strptime(row['Program Session - Program Session End Date'], "%d-%b-%y")
            if startDateRef > today - twoWeeks and endDateRef < today + threeMnths:
                urlfull = row['Program Session - Program Session Information URL']
                urlSnip = urlfull[-3:]
                concatCode = row['Program Session - Portal Acronym'] + row['Program Session - Program Session Subactivity Code']
                allCourses.update({urlSnip : concatCode})

    for key, value in allCourses.iteritems():

        courseInfoRaw = requests.get('https://harvard-catalog-courses.instructure.com/api/v1/courses/' + str(key) +'/users?per_page=500,', headers=canHeaders)
        courseInfo = courseInfoRaw.json()
        enrollmentInfoAll = []
        
        for c in courseInfo:
            userID = c['id']
            enrollmentInfoRaw = requests.get('https://harvard-catalog-courses.instructure.com/api/v1/users/' + str(userID) +'/profile?per_page=500', headers=canHeaders)
            enrollmentInfo = enrollmentInfoRaw.json()
            enrollmentInfoAll.append(enrollmentInfo)  
        
        with open(CanvasAutoExportPath + str(value) + ".json", "w") as outfile:
            outfile.write("var canRosterData = ")
            outfile.write(json.dumps(enrollmentInfoAll, sort_keys=False, indent=4))


def alertMePos():
    pymsgbox.alert("Success! Photo Roster Data from Canvas has been UPDATED for today!")
    response = pymsgbox.password('Please enter password to confirm')
    print response
    if response == "None":
        alertMePos()
    if not response:
        alertMePos()

def alertMeNegInt():
    pymsgbox.alert("Process Failed! No Internet Connection. Please Try Again.")
    response = pymsgbox.password('Please enter password to confirm')
    print response
    if response == "None":
        alertMeNegInt()
    if not response:
        alertMeNegInt()

def alertMeNegK():
    pymsgbox.alert("Process Failed! Web and net is up, but there is no secure K drive Connection. Please Try Again.")
    response = pymsgbox.password('Please enter password to confirm')
    print response
    if response == "None":
        alertMeNegK()
    if not response:
        alertMeNegK()


if internet_on() == True:
    if SharedDrive_on() == True:
        getSurveys()
        for t in allSurvs:
            print t
            gatherResponses(t)
        getAllCourseInfo()
        alertMePos()
        secsDur = time.time()-start
        minsDur = secsDur / 60    
        print 'It took', minsDur, 'mins.'
    elif SharedDrive_on() == False:
        alterMeNegK()

elif internet_on() == False:
    alertMeNegInt()
