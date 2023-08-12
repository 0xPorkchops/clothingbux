from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import requests
import json
import time
import os
import random
import traceback
import logging
from multiprocessing import Process

DIRECTORY = r'C:\Users\User\Desktop\ClothingBot\Assets' #Add validation that these folders exist with some assets in them

class DownloadClothing:
    def __init__(self):
        print("Starting class DownloadClothing")
        with open("settings.json", "r") as f: #Read settings and save that data into class
            settings = json.load(f)
            self.users, self.blacklist, self.proxies, self.keywordsNew, self.keywordsOld = settings["users"], settings["blacklist"], settings["proxies"], settings["keywordsNew"], settings["keywordsOld"]

    def Run(self):
        #Search each keyword and download all of the assets possible up until the maximum page_num is reached
        for keyword in self.keywordsNew:
            cursor = None
            for x in range(3): #Number of pages to download per keyword, I think limit is 25?
                params = {"keyword": keyword, "Category": "3", "Subcategory": 12, "Limit": 30, "IncludeNotForSale": False, "MinPrice": 1, "Cursor": cursor}
                r = requests.get("https://catalog.roblox.com/v1/search/items/details", params=params)
                for assetInfo in r.json()["data"]: #This sometimes returns None, so make it retry if r.json() == None
                    if self.Validate(assetInfo["name"]):
                        self.Download(assetInfo["id"], str(assetInfo["assetType"]))
                        time.sleep(0.25)
                cursor = r.json()["nextPageCursor"]
            print("Finished keyword:", keyword)
            self.keywordsNew.remove(keyword)
            self.keywordsOld.append(keyword)
            if len(self.keywordsNew) == 0:
                self.keywordsNew = self.keywordsOld
                self.keywordsOld = []
            self.SaveSettings() #Save the keywordsNew and keywordsOld changes to settings file

    def Validate(self, assetName):
        #something about check if CD, blacklist, ####, etc.
        if "##" in assetName or "Content Deleted" in assetName:
            return False
        else:
            return True

    def Download(self, assetId, assetType):
        jsonFile = os.path.join(os.path.join(DIRECTORY, 'json'), str(assetId) + '.json') #File path for assetId
        if not os.path.isfile(jsonFile): #If this file doesn't already exist, let's make it exist
            r = self.ProductInfo(assetId)
            with open(jsonFile, 'wb') as f: #We write json file before image file so that if we run DownloadClothing and UploadClothing at the same time, there is no chance of a json file not existing when we select a random image in UploadClothing
                f.write(r.content)
            for x in range(30): #Number of tries to find the file ID
                r2 = self.ProductInfo(assetId - x)
                if r2.json()["Name"] == r.json()["Name"]: #If we found a match between asset ID and file ID
                    r3 = requests.get("https://assetdelivery.roblox.com/v1/asset/", params={"id": assetId - x})
                    if len(r3.content) > 1000: #If the asset file returns a 403 json, then its Content Deleted and the length should be 77, but we test for 1000 just in case. Image files should be like 500K+ length
                        imageFile = os.path.join(os.path.join(DIRECTORY, assetType), str(assetId) + '.png') #File path for asset file
                        with open(imageFile, 'wb') as f:
                            f.write(r3.content)

    def ProductInfo(self, assetId):
        r = requests.get("https://api.roblox.com/Marketplace/ProductInfo", params={"assetId": assetId})
        while r.status_code != 200: #Sometimes it returns 503, service unavailable, so we have to retry
            print("ProductInfo API returned 503")
            r = requests.get("https://api.roblox.com/Marketplace/ProductInfo", params={"assetId": assetId})
            time.sleep(0.5)
        return r

    def SaveSettings(self):
        with open("settings.json", "r+") as f:
            settings = json.load(f)
            settings["keywordsNew"], settings["keywordsOld"] = self.keywordsNew, self.keywordsOld
            f.seek(0) #Open file stream at beginning of file, because for some reason it starts at the end when using json.dump()
            json.dump(settings, f)
            f.truncate() #If there's any excess characters after what we wrote, it'll delete it. truncate(x) default argument is current file stream position x

class UploadClothing:
    def __init__(self):
        print("Starting class UploadClothing")

        with open('settings.json', 'r') as f: #Read settings and save that data into class
            settings = json.loads(f.read())
            self.users, self.blacklist, self.proxies, self.description = settings["users"], settings["blacklist"], settings["proxies"], settings["description"]

        self.assets = {'11' : os.listdir(os.path.join(DIRECTORY, '11')), '12' : os.listdir(os.path.join(DIRECTORY, '12'))} #Creates list of shirts and list of pants from folders, ripe for randomly picking from

        self.tabData = {} #Dictionary to store the most recent JSON ID's being uploaded per group tab, plus timeout timestamp. Key = int self.currentTab, Value = {'assetId': str assetId, 'timeout': float timeout}
        self.currentTab = 0

        self.options = webdriver.ChromeOptions() #Put the saved Chrome profile into the class (has anti-captcha and adblock extensions)
        self.options.add_argument(r'user-data-dir=C:\Users\User\Desktop\ClothingBot\ChromeProfile')
        self.options.add_experimental_option("detach", True) #'keep alive' function so that the driver/browser doesn't close automatically when its variable goes out of scope/gets garbaged

    def Run(self):
        #Starts the upload bot
        try:
            assetType = '11'
            for user in self.users: #Start new browser window for each user
                driver = self.UserDriver(user, assetType) #11 means upload shirts
                self.GroupTabs(user, driver, assetType)
                while True:
                    #print(self.tabData)
                    if self.tabData[self.currentTab]['timeout'] < time.time(): #Skip tabs that are currently in timeout
                        status = self.UploadStatus(driver)
                        print("STATUS", status)
                        if status == 2: #last upload successful, configure it and upload next shirt
                            if not self.CheckContentDeleted(self.tabData[self.currentTab]['assetId'], assetType): #Only configure the asset if its not content-deleted. If it is content deleted, leave it not for sale and delete the image file from local storage
                                self.ConfigureAsset(driver)
                        elif status == 3: #uploading too fast, wait a while
                            print("Upload limit reached, will try again in 6 hours...")
                            driver.refresh()
                            self.DeleteMyCreationsTab(driver)
                            self.tabData[self.currentTab]['timeout'] = time.time() + 21601 #7200 for 2 hours, 86400 for 24 hours
                        elif status == 5 or status == 7 or status == 8: #captcha or upload timeout, refresh page
                            driver.refresh()
                            self.DeleteMyCreationsTab(driver)
                        if status != 4 and status != 3: #captcha not yet solved or upload cooldown, go to next tab
                            self.UploadAsset(driver, assetType)
                            time.sleep(4) #let captcha and anti-captcha extension load?
                    else:
                        time.sleep(4) #To lower the amount of times it checks the timeout. Maybe add a smart way of pausing altogether if all tabs are timeout? or closing and reopening tabs after timeout completion?
                    self.NextTab(driver)
        except Exception as e:
            logging.error(traceback.format_exc())
            if 'Message: no such element: Unable to locate element: {"method":"css selector","selector":"[id="upload-button"]"}' in str(e):
                print("################## HAVE YOU SET UP THE ANTI-CAPTCHA EXTENSION? ##################") #We use the text generated by the anti-captcha extension to check the status of the current upload. If its not set up, the bot tries to upload while the captcha is still present

    def UserDriver(self, user, assetType):
        #New driver/browser window. Will contain all tabs for each group a user is in

        driver = webdriver.Chrome(executable_path=r'C:\Users\User\Desktop\ClothingBot\chromedriver.exe', options=self.options) #New browser window

        driver.get("https://www.roblox.com/") #Load some regular roblox.com cookies into this session
        driver.add_cookie({'name':'.ROBLOSECURITY', 'value':self.users[user], 'domain':'.roblox.com'}) #Inject previous session cookie to log in

        return driver

    def GroupTabs(self, user, driver, assetType):
        #Open all the tabs for each group upload page
        groups = requests.get("http://api.roblox.com/users/" + str(user) + "/groups").json() #Gets user's groups #Maybe check rank/privs in group - for if I ever release this to the public
        for group in groups:
            driver.get("https://www.roblox.com/develop/groups/" + str(group["Id"]) + "?view=" + assetType) #assetType = 11 for shirts or 12 for pants
            self.tabData[self.currentTab] = {'timeout':0} #Set up the group ID's in tabData. Within each table will be current assetId and current timeout
            self.DeleteMyCreationsTab(driver) #The webpage is weird, we have to delete the personal asset uploading tab so we only deal with the group asset uploading tab
            driver.execute_script("window.open('');") #Open new tab for next group
            self.currentTab += 1
            driver.switch_to.window(driver.window_handles[self.currentTab]) #Even if we open a new tab using javascript, we also need to tell selenium that there's a new active tab

        driver.close() #Close the last tab that's empty
        self.currentTab -= 1
        driver.switch_to.window(driver.window_handles[self.currentTab])

        self.NextTab(driver) #Not necessary, but start on first tab

    def UploadAsset(self, driver, assetType):
        #Submit upload for random shirt/pant in folder on the current page
        assetFile = random.choice(self.assets[assetType]) #Select random asset image
        assetId = assetFile.split('.',1)[0] #Associated json file should be the same assetId
        self.tabData[self.currentTab]['assetId'] = assetId #Store assetId in self.tabData so we have the data to configure this asset once its done uploading using assetId.json

        time.sleep(3) #wait for upload iframe to load if it hasn't. not best practice but whatever
        self.Iframe(driver) #Switch bot's focus to the iframe within the webpage for uploading
        driver.find_element_by_id("file").send_keys(os.path.join(os.path.join(DIRECTORY, assetType), assetFile)) #Selects the file in the upload webform
        time.sleep(0.1) #Give time for the name field populate with the file name
        driver.find_element_by_id("name").clear() #Delete the file name so we can replace it with "Clothing" to prevent 'The name or description contains inappropriate text.'
        driver.find_element_by_id("name").send_keys("Clothing") #Generic placeholder name
        driver.find_element_by_id("upload-button").click() #Clicks the upload button
        self.Iframe(driver, False) #Get out of the scope of the upload iframe, ie 'zoom out'

    def NextTab(self, driver): #does this work if I'm only in one group? (ie one tab)
        #Switch to the next tab while the captcha solver extension is (possibly) running
        if self.currentTab + 1 == len(self.tabData):
            self.currentTab = 0
        else:
            self.currentTab += 1
        driver.switch_to.window(driver.window_handles[self.currentTab])

    def UploadStatus(self, driver):
        time.sleep(3) #Wait period between uploads. Acts as a timeout in case upload gets hung up or iframe doesn't load yet
        page = driver.page_source
        self.Iframe(driver)
        page += driver.page_source #Append the contents of the upload iframe
        self.Iframe(driver, False)

        if '<div id="upload-result" class="status-confirm btn-level-element">' in page: #Another option is to string match element().text instead of iframe().page_source?
            return 2 #2 - Upload successful, go configure it and upload more
        elif "uploading too much" in page:
            return 3 #3 - Too many uploads, stop for a while
        elif page.count("Loading..") == 1 or "Solving is in process" in page: #the anti-captcha extension also has initial text on the bottom before solving is in process. what's the text? add it to this elif or. ALSO sometimes it takes too long, so add a timeout timestamp to self.tabData (maybe rename?)
            return 4 #4 - Still solving captcha or shirt was successfully created and there's captcha remnants on page (which doesn't matter with the first if statement), go to next tab
        elif page.count("Loading..") == 2 or "Captcha could not be solved" in page:
            return 5 #5 - Captcha took too long or didn't solve correctly, refresh page
        elif "Upload failed. Did you use the template?" in page:
            return 6 #6 - Upload failed, shirt template wasn't compatible? upload more
        elif "Please fill out the Captcha" in page:
            return 7 #7 - Not sure how this one came up once, but it breaks the upload form so refresh page
        elif '<span id="loading-container" style="display: inline;">' in page:
            return 8 #8 - The asset upload got hung up and is still loading beyond timeout period, so refresh the page. Need to figure out how to make timeout independent of upload wait period!
        else:
            return 1 #1 - No status, new page, start uploading

    def ConfigureAsset(self, driver):
        #Set name, description, price
        assetId = self.tabData[self.currentTab]['assetId'] #Get assetId from self.tabData[int self.currentTab]['assetId'] for finding json file
        self.Iframe(driver)
        uploadedId = driver.page_source.split('uploadedId=',1)[1].split('">',1)[0] #this is in an iframe, so does it search correctly??
        self.Iframe(driver, False)
        with open(os.path.join(os.path.join(DIRECTORY, 'json'), assetId + '.json'), 'rb') as f:
            metadata = json.load(f)
            groupId = driver.current_url.split("groups/")[1].split("?view")[0]
            name, description = metadata["Name"], self.description.format(groupId, "6142507395")
        self.Request(driver, 'PATCH', 'https://develop.roblox.com/v1/assets/' + uploadedId, data={"name":name,"description":description,"enableComments":True,"genres":["All"],"isCopyingAllowed":False}, headers={'x-csrf-token':self.GetToken(driver)})
        self.Request(driver, 'POST', 'https://itemconfiguration.roblox.com/v1/assets/' + uploadedId + '/release', json={"priceConfiguration":{"priceInRobux":5},"saleStatus":"OnSale"}, headers={'x-csrf-token':self.GetToken(driver)})
        #print(s.post('https://itemconfiguration.roblox.com/v1/assets/6026516587/update-price', data={"priceConfiguration":{"priceInRobux":6}}, headers={'x-csrf-token':(s.post('https://auth.roblox.com/v2/logout').headers['x-csrf-token'])}).text)

    def CheckContentDeleted(self, assetId, assetType):
        assetThumbnail = requests.get("https://www.roblox.com/asset-thumbnail/image?assetId=" + assetId + "&width=420&height=420&format=png")
        while assetThumbnail.url == "https://t2.rbxcdn.com/ffc3cf81492f26555592d46357f0658e": #If the asset thumbnail is the blank loading thumbnail, wait and retry until its either the correct thumbnail or content-deleted thumbnail
            print("Uploaded asset is still loading, retrying checking content-deleted status...")
            time.sleep(0.5)
            assetThumbnail = requests.get("https://www.roblox.com/asset-thumbnail/image?assetId=" + assetId + "&width=420&height=420&format=png")
        if assetThumbnail.url == "https://t6.rbxcdn.com/70608418c648be7ac4e323e3294bb059": #If asset has content-deleted thumbnail, delete the image file from storage, but keep json file so we don't redownload image file
            print("Uploaded asset is content-deleted, deleting from local storage...")
            assetFile = os.path.join(os.path.join(DIRECTORY, assetType), str(assetId) + ".png")
            if os.path.exists(assetFile):
                os.remove(assetFile)
            return True
        else:
            return False

    def DeleteMyCreationsTab(self, driver):
        myCreations = driver.find_element_by_id("MyCreationsTab") #We only want to work with group tab, not personl tab
        driver.execute_script("var myCreations = arguments[0];myCreations.parentNode.removeChild(myCreations);", myCreations) #Javascript to delete personal asset uploading tab

    def Iframe(self, driver, action=True): #Switch driver scope to upload-iframe so we can search it, or exit iframe if False
        if action:
            driver.switch_to.frame(driver.find_element_by_id("upload-iframe"))
        else:
            driver.switch_to.default_content()

    def GetToken(self, driver):
        return self.Request(driver, 'POST', 'https://auth.roblox.com/v2/logout').headers['x-csrf-token'] #X-CSRF-TOKEN is an ever-changing token that is necessary to make certain requests that require elevated security. This is a backwards way of getting the token, it doesn't actually log out.

    def Request(self, driver, method, url, params=None, data=None, json=None, headers=None):
        s = requests.Session() #This 'proxy' function lets us sync the driver/web browser cookies with requests' cookies
        seleniumCookies = driver.get_cookies()
        for cookie in seleniumCookies:
            s.cookies.set(cookie['name'], cookie['value'])
        if method.upper() == 'GET':
            r = s.get(url=url, params=params, headers=headers)
        elif method.upper() == 'POST':
            r = s.post(url=url, params=params, data=data, json=json, headers=headers)
        elif method.upper() == 'PATCH':
            r = s.patch(url=url, params=params, data=data, json=json, headers=headers)
        else:
            r = False #There are other methods and data types that could go through requests, but this function is limited to what is necessary
        requestsCookies = s.cookies.get_dict()
        for cookie in requestsCookies:
            driver.add_cookie({'name':cookie, 'value':requestsCookies[cookie], 'domain':'.roblox.com'}) #Update driver/web browser cookies with any changes made with requests
        return r

def main():
    selection = input("Enter 1 for download, 2 for upload, or 3 for both: ")
    if selection == "1":
        Download = Process(target=DownloadClothing().Run)
        Download.start()
        Download.join()
    elif selection == "2":
        Upload = Process(target=UploadClothing().Run)
        Upload.start()
        Upload.join()
    elif selection == "3":
        Download = Process(target=DownloadClothing().Run)
        Upload = Process(target=UploadClothing().Run)
        Download.start()
        Upload.start()
        Download.join()
        Upload.join()
    print("Process finished.")

if __name__ == '__main__':
    main()


#Get users, for each user...
#Get user groups
#Open the clothing upload tab for each group
#Select random image file from folder containing all downloaded templates and upload
#Wait x seconds just in case captcha is present, or somehow check if image is done uploading
#Configure with json file that has the same asset ID (get asset data from roblox if json doesnt exist, and placeholder data if that asset no longer exists)
#repeat last 3 steps

#check status.roblox.com for outages
#check if asset is Content Deleted, and don't store it if it is
#use PIL to add custom watermark to asset, maybe even custom per group?
#test different prices, maybe run each group with different pricing model?
#add blacklist, proxy, and search functionality
#if uploaded asset gets CD'd, then delete it from local storage
#check for ##### in title/description, delete or adjust accordingly?
#add a global try except so if there's any errors, the bot can restart itself from scratch
#add real api login functionality?
#is there a way to implicitly pass the current driver into functions? through self? how do I organize that?
#add default description tags / price to settings.json?
#I check for blacklist when downloading, but should I check for ### or CD'd after uploading?
