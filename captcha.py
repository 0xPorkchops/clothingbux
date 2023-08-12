import requests
from bs4 import BeautifulSoup
import time

session = requests.Session()

ROBLOSECURITY = 'YOUR_.ROBLOSECURITY_COOKIE_HERE'

def login():
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'})
    session.cookies.set('.ROBLOSECURITY', ROBLOSECURITY) #logs in to the account
    session.get('https://www.roblox.com/home') #adds a bunch of other normal cookies to the session

def xcsrf():
        r = session.post('https://api.roblox.com/sign-out/v1') #no worries, this does not actually sign out the account
        xcsrfToken = r.headers['x-csrf-token'] #this x-csrf-token is used for many roblox.com API's
        return xcsrfToken

def bypass_captcha():
    r = session.get('https://www.roblox.com/develop/?View=11')
    soup = BeautifulSoup(r.text, 'html.parser')
    clientKey = 'YOUR_ANTI-CAPTCHA_CLIENT_API_KEY' #my anti-captcha.com client key
    url = r.url
    siteKey = r.text.split('captcha.setSiteKey("')[-1].split('"')[0]
    createTaskPayload = {
        'clientKey':clientKey,
        'task':{
            'type':'NoCaptchaTaskProxyless',
            'websiteURL':url,
            'websiteKey':siteKey
        }
    }
    createTaskResponse = requests.post('https://api.anti-captcha.com/createTask', json=createTaskPayload).json()
    errorId = createTaskResponse['errorId']
    taskId = createTaskResponse['taskId']
    getTaskPayload = {
        'clientKey':clientKey,
        'taskId':taskId
    }
    solved = False
    while solved == False:
        time.sleep(15)
        print 'Checking for captcha result...'
        getTaskResponse = requests.post('https://api.anti-captcha.com/getTaskResult', json=getTaskPayload).json()
        if getTaskResponse['status'] == 'ready':
            solution = str(getTaskResponse['solution']['gRecaptchaResponse'])
            print 'Got Captcha Solution: ', solution
            solved = True

    formParams = {
        'g-Recaptcha-Response':solution,
        'isInvisible':'true'
    }
    formHeaders = {
            'Sec-Fetch-Mode':'cors',
            'Sec-Fetch-Site':'same-origin',
            'Origin':'https://www.roblox.com',
            'Accept-Encoding':'gzip, deflate, br',
            'X-CSRF-TOKEN':xcsrf(),
            'Host':'www.roblox.com',
            'Accept-Language':'en-US,en;q=0.9',
            'Accept':'*/*',
            'Referer':'https://www.roblox.com/develop?View=11',
            'Connection':'keep-alive',
            'Content-Length':'0'
    }
    optionsHeaders = {'Sec-Fetch-Mode':'cors', 'Access-Control-Request-Method':'POST', 'Origin':'https://www.roblox.com/', 'Referer':'https://www.roblox.com/develop?View=11', 'Access-Control-Request-Headers':'x-csrf-token'}

    #Look at the network request log I provided. I tried to replicate the network requests, but submitRequest still returns 403

    prime0 = session.post('https://www.roblox.com/build/upload/captcha', headers=formHeaders)
    print 'Prime0', prime0.status_code
    prime1 = session.options('https://assetgame.roblox.com/game/report-event?name=ClothingUploadCaptcha_Displayed', headers=optionsHeaders, params={'name':'ClothingUploadCaptcha_Displayed'})
    print 'Prime1', prime1.status_code
    prime2 = session.post('https://assetgame.roblox.com/game/report-event?name=ClothingUploadCaptcha_Displayed', headers=formHeaders, params={'name':'ClothingUploadCaptcha_Displayed'})
    print 'Prime2', prime2.status_code
    prime3 = session.options('https://assetgame.roblox.com/game/report-event?name=ClothingUploadCaptcha_User_Solved_InSeconds_4_To_10', headers=optionsHeaders, params={'name':'ClothingUploadCaptcha_User_Solved_InSeconds_4_To_10'})
    print 'Prime3', prime3.status_code
    prime4 = session.options('https://api.roblox.com/captcha/validate/user', headers=optionsHeaders)
    print 'Prime4', prime4.status_code
    prime5 = session.post('https://assetgame.roblox.com/game/report-event?name=ClothingUploadCaptcha_User_Solved_InSeconds_4_To_10', headers=formHeaders, params={'name':'ClothingUploadCaptcha_User_Solved_InSeconds_4_To_10'})
    print 'Prime5', prime5.status_code
    submitRequest = session.post('https://api.roblox.com/captcha/validate/user', headers=formHeaders, params=formParams)
    print 'Submit request', submitRequest.status_code
    prime6 = session.options('https://assetgame.roblox.com/game/report-event?name=ClothingUploadCaptcha_Success', headers=optionsHeaders, params={'name':'ClothingUploadCaptcha_Success'})
    print 'Prime6', prime6.status_code
    prime7 = session.post('https://assetgame.roblox.com/game/report-event?name=ClothingUploadCaptcha_Success', headers=formHeaders, params={'name':'ClothingUploadCaptcha_Success'})
    print 'Prime7', prime7.status_code
    print 'submitted captcha solve'

login()
bypass_captcha()
