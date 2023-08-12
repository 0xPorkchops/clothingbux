import requests
from bs4 import BeautifulSoup
import time
import sys
from random import randint
import json
import pickle
import os

os.chdir(sys.path[0]) #Allows relative directories on linux

AssetsLoc = '/home/Robux/Assets'
user = ''
ROBLOSECURITY = ''
pause = 3
gid = ''

with open('/home/Robux/blacklist.json') as f:
    blacklistFile = json.load(f)

with open('/home/Robux/proxies.json') as f:
    proxyFile = json.load(f)

proxies = {
    'http': proxyFile[user],
    'https': proxyFile[user]
}

class RobloxBot:
        """A simple Roblox bot class"""
        def __init__(self, group_id):
                # creates a session
                self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
                session_status = self.login()
                if session_status == False:
                        sys.exit('Login failed, exiting...')
                # sets group id
                self.group_id = group_id


        def save_cookies(self, session, filename):
                with open('./' + filename + '.cookie', 'w') as f:
                        f.truncate()
                        pickle.dump(session.cookies._cookies, f)

        def load_cookies(self, session, filename):
                try:
                        with open('./' + filename + '.cookie', 'r') as f:
                                cookies = pickle.load(f)
                                if cookies:
                                        jar = requests.cookies.RequestsCookieJar()
                                        jar._cookies = cookies
                                        session.cookies = jar
                                else:
                                        return False
                except:
                        return False

        def logged_in(self, session):
                balance = session.get('http://api.roblox.com/currency/balance').text
                if 'Forbidden' in balance:
                        return False
                elif 'robux' in balance:
                        return True
                else:
                        return 'Error'

        def login(self):
                self.session = requests.Session()
                self.session.headers.update(self.headers)
                self.session.proxies = proxies
                print self.session.get('https://api.ipify.org/?format=json').text
                self.load_cookies(self.session, user)
                login_status = self.logged_in(self.session)
                if login_status == False:
                        print "Logging in via saved cookies failed, logging in using .ROBLOSECURITY"
                        self.session = requests.Session()
                        self.session.headers.update(self.headers)
                        self.session.proxies = proxies
                        self.session.cookies.set('.ROBLOSECURITY', ROBLOSECURITY)
                        #payload = {'username':user, 'password':pw} #make sure no passwords have apostrophes
                        #r = self.session.post('https://api.roblox.com/v2/login', data=payload)
                        login_status = self.logged_in(self.session)
                        if login_status == True:
                                print "Logging in via .ROBLOSECURITY succeded"
                                self.save_cookies(self.session, user)
                                return True
                        elif login_status == False:
                                print "Logging in via .ROBLOSECURITY failed"
                                return False
                elif login_status == True:
                                print "Logging in via saved cookies succeeded"
                                return True

        def http(self, op, url, params, files, data):
                r = None
                if op == 'get':
                        r = self.session.get(url, params=params, files=files, data=data)
                elif op == 'post':
                        r = self.session.post(url, params=params, files=files, data=data)
                if 'https://www.roblox.com/Membership/NotApproved.aspx?ID=' in r.url:
                        print 'Not clear'
                        soup =  BeautifulSoup(r.content, 'lxml')
                        if soup.findAll('input', {'name':'ctl00$cphRoblox$ButtonAgree'}) == []:
                                print user, 'Banned, skipping...'
                                sys.exit('Account currently banned')
                        else:
                                print user, 'Suspended, reactivating...'
                                userId = self.session.get('http://api.roblox.com/users/get-by-username?username=' + user).json()['Id']
                                postData = {
                                        '__EVENTTARGET':'',#soup.find('input', {'name':'__EVENTTARGET'}).get('value'),
                                        '__EVENTARGUMENT':'',#soup.find('input', {'name':'__EVENTARGUMENT'}).get('value'),
                                        '__VIEWSTATE':soup.find('input', {'name':'__VIEWSTATE'}).get('value'),
                                        '__VIEWSTATEGENERATOR':soup.find('input', {'name':'__VIEWSTATEGENERATOR'}).get('value'),
                                        '__EVENTVALIDATION':soup.find('input', {'name':'__EVENTVALIDATION'}).get('value'),
                                        'ctl00$cphRoblox$ButtonAgree':'Reactivate My Account'#soup.find('input', {'name':'ctl00$cphRoblox$ButtonAgree'}).get('value')
                                        }
                                r = self.session.post('https://www.roblox.com/Membership/NotApproved.aspx?ID='+str(userId), data=postData) #post to MemberNotApproved.aspx?id=8888?
                                if op == 'get':
                                        return self.session.get(url, params=params, files=files, data=data)
                                elif op == 'post':
                                        return self.session.post(url, params=params, files=files, data=data)
                else:
                        return r
        def xcsrf(self):
                r = self.session.post('https://api.roblox.com/sign-out/v1')
                xcsrfToken = r.headers['x-csrf-token']
                return xcsrfToken

        def bypass_captcha(self):
            r = self.http('get', 'https://www.roblox.com/develop/groups/' + gid + '?View=11', None, None, None)
            soup = BeautifulSoup(r.text, 'lxml')
            clientKey = 'ANTI-CAPTCHA_CLIENT_KEY_HERE'
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
                print 'Checking for captcha result'
                getTaskResponse = requests.post('https://api.anti-captcha.com/getTaskResult', json=getTaskPayload).json()
                if getTaskResponse['status'] == 'ready':
                    print 'Got captcha result, submitting...'
                    solution = str(getTaskResponse['solution']['gRecaptchaResponse'])
                    print 'solution', solution
                    solved = True
            formParams = {
                'g-Recaptcha-Response':solution,
                'isInvisible':'true'
            }
            formHeaders = {
                    'X-CSRF-TOKEN':self.xcsrf(),
                    'Referer':'https://www.roblox.com/develop/groups/'+gid+'?view=11'
            }
            print formHeaders
            print self.session.headers
            prime0 = self.session.post('https://www.roblox.com/build/upload/captcha', headers=formHeaders)
            print 'Prime0', prime0.status_code, prime0.request.headers
            prime1 = self.session.options('https://assetgame.roblox.com/game/report-event?name=ClothingUploadCaptcha_Displayed', headers=formHeaders, params={'name':'ClothingUploadCaptcha_Displayed'})
            print 'Prime1', prime1.status_code, prime1.request.headers
            prime2 = self.session.post('https://assetgame.roblox.com/game/report-event?name=ClothingUploadCaptcha_Displayed', headers=formHeaders, params={'name':'ClothingUploadCaptcha_Displayed'})
            print 'Prime2', prime2.status_code, prime2.request.headers
            prime3 = self.session.options('https://assetgame.roblox.com/game/report-event?name=ClothingUploadCaptcha_User_Solved_InSeconds_4_To_10', headers=formHeaders, params={'name':'ClothingUploadCaptcha_User_Solved_InSeconds_4_To_10'})
            print 'Prime3', prime3.status_code, prime3.request.headers
            prime4 = self.session.options('https://api.roblox.com/captcha/validate/user', headers=formHeaders)
            print 'Prime4', prime4.status_code, prime4.request.headers
            prime5 = self.session.post('https://assetgame.roblox.com/game/report-event?name=ClothingUploadCaptcha_User_Solved_InSeconds_4_To_10', headers=formHeaders, params={'name':'ClothingUploadCaptcha_User_Solved_InSeconds_4_To_10'})
            print 'Prime5', prime5.status_code, prime5.request.headers
            submitRequest = self.session.post('https://api.roblox.com/captcha/validate/user', headers=formHeaders, params=formParams)
            print 'Submit request', submitRequest.status_code, submitRequest.request.headers
            prime6 = self.session.options('https://assetgame.roblox.com/game/report-event?name=ClothingUploadCaptcha_Success', headers=formHeaders, params={'name':'ClothingUploadCaptcha_Success'})
            print 'Prime6', prime6.status_code, prime6.request.headers
            prime7 = self.session.post('https://assetgame.roblox.com/game/report-event?name=ClothingUploadCaptcha_Success', headers=formHeaders, params={'name':'ClothingUploadCaptcha_Success'})
            print 'Prime7', prime7.status_code, prime7.request.headers
            print 'submitted captcha solve'

        def get_shirts(self, page_num, category, wait):
                while page_num < 25:
                        # gets asset ids of shirts
                        params = {'Subcategory': category, 'SortAggregation': '5', 'LegendExpanded': 'true', 'Category': '3', 'PageNumber': page_num} #{'CatalogContext':'66'}
                        try:
                                while True:
                                        r = self.http('get', 'https://www.roblox.com/catalog/json', params, None, None)
                                        if r.text != '[]':
                                                break
                                        time.sleep(5)
                                r.raise_for_status()
                        except requests.exceptions.HTTPError:
                                print('Status Error: {}'.format(r.status_code))
                                time.sleep(30)
                                continue
                        print('Got items from page: {}'.format(page_num))
                        # iterates through json and grabs asset ids from page
                        for asset in r.json():
                                # calls download with the asset id
                                while True:
                                        try:
                                                self.__download(asset['AssetId'])
                                                break
                                        except Exception as e:
                                                print 'Retrying, Error on line {}'.format(sys.exc_info()[-1].tb_lineno), e
                                                continue
                                time.sleep(wait)
                        if page_num == 24:
                                page_num = 1
                        else:
                                page_num +=1

        def __cache(self, assetId, fileType):
                if fileType == 'json':
                        try:
                                f = open(AssetsLoc + '/json/' + str(assetId) + '.json', 'r')
                                asset = f.read()
                                f.close()
                                print "Returning local json"
                                return asset
                        except:
                                try:
                                        asset = self.http('get', 'https://api.roblox.com/Marketplace/ProductInfo', {'assetId': assetId}, None, None)
                                        asset.raise_for_status()
                                except (requests.exceptions.HTTPError, ValueError):
                                        print ('Could not find template? for: {}'.format(assetId)) #fix this shitty error catching ... why does it say template? its product info
                                        return
                                f = open(AssetsLoc + '/json/' + str(assetId) + '.json', 'w')
                                f.write(asset.content)
                                f.close()
                                print "Returning online json"
                                return asset.content

                elif fileType == 'image':
                        try:
                                f = open(AssetsLoc + '/image/' + str(assetId) + '.png', 'rb')
                                asset = f.read() #fix close, maybe do with open
                                f.close()
                                print "Used cached image"
                                return asset
                        except:
                                asset = self.http('get', 'https://www.roblox.com/asset/', {'id': assetId}, None, None)
                                f = open(AssetsLoc + '/image/' + str(assetId) + '.png', 'wb')
                                f.write(asset.content)
                                f.close()
                                print "Used online image"
                                return asset.content

        def __download(self, assetId):
                # gets name, description, price and file

                data = json.loads(self.__cache(assetId, 'json'))#works fine

                name, description, price, asset_type = data['Name'], data['Description'], data['PriceInRobux'], data['AssetTypeId']

                if any(badword in name.lower() for badword in blacklistFile):
                    print name.encode('ascii', 'ignore'), "; Item name contains blacklisted word, skipping"
                else:
                    print name.encode('ascii', 'ignore'), "; Item name doesn't contain blacklisted word, continuing"
                    # gets templates asset id
                    count = 0
                    while count < 10:
                            assetId -= 1
                            #print "Trying cache 1"
                            r = self.__cache(assetId, 'json')
                            #print "Cache 2"
                            count += 1
                            if json.loads(r)['Name'] == name:
                                    print('Got template id for: {}'.format(assetId))
                                    break
                    else:
                            print('Could not find template for: {}'.format(assetId))
                            return
                    # downloads file to memory for later upload
                    Upfile = self.__cache(assetId, 'image')
                    print('Downloaded Template.')
                    self.__upload(name, description, price, Upfile, asset_type, assetId)

        def __upload(self, name, description, price, Upfile, asset_type, assetId):
                # gets verification token
                r = self.http('get', 'https://www.roblox.com/build/upload', None, None, None)
                token = r.text.split('name=__RequestVerificationToken type=hidden value=')[-1].split('>')[0]
                print('Got Request Verification Token.')
                # uploads file to Roblox
                data = {'file': ('template.png', Upfile, 'image/png')}
                payload = {'__RequestVerificationToken': token, 'assetTypeId': asset_type, 'groupId': self.group_id, 'onVerificationPage': False, 'isOggUploadEnabled': True, 'isTgaUploadEnabled': True, 'name': name}
                r = self.http('post', 'https://www.roblox.com/build/upload', None, data, payload)
                if 'errorType=1' in r.url:
                    print 'Captcha present'
                        #self.bypass_captcha()
                # gets asset id so the shirt can be published
                asset_id = r.text.split('uploadedId=')[-1].split('" />')[0]
                assets = {'id': asset_id}
                # gets required fields for post request
                r = self.http('get', 'https://www.roblox.com/my/item.aspx', assets, None, None)
                view_state = r.text.split('id="__VIEWSTATE" value="')[-1].split('" />')[0]
                view_gen = r.text.split('id="__VIEWSTATEGENERATOR" value="')[-1].split('" />')[0]
                validation = r.text.split('id="__EVENTVALIDATION" value="')[-1].split('" />')[0]
                # creates payload for shirt editing/publishing
                tags = 'TAGS - Costume Doctor Nurse Cop Prisoner Sailor Army CIA Swat FBI Pride Boy Girl Racer NASCAR Zombie Vampire Halloween Peach Strawberry Cherry Blueberry Chocolate Vanilla Milk Anime Tokyo Ghoul Demon Jojo Naruto One Piece MHA DBZ Japan Japanese God Goddess Roman Greek Egyptian Watermelon Shark Animal Squirrel Fox Wolf Bunny Dog Cat Frog Scrunchie Bracelet Skater Cute Kawaii Assassin Wizard Witch Devil Angel Memes Love Heart Tiger Panda Cheetah Lion Korean Chinese RP Role Play Ice Cream Sandwich Cake Muffin Cupcake Backpack Bag Guardian Galaxy Supreme LV Louis Vuitton Gucci Versace Champion Vans Skater Checkered Hoodie Overalls Cartoons Sprinkles Sad Happy Mad Cheetos Doritos King Queen Princess Prince Jester Nerd Geek Soul Reaper Cookie Chef Superhero Villain DC Marvel Majestic Magical Magic Cape Cloud Vest Onesie Pajamas Pjs Food Noob OOF Headstack Stars Space Necklace Diamond Gold Ruby Dora Rose Spongebob Muscles Abs Sports Tik Tok Ninja Samurai Miku WWE'
                payload = {'__EVENTTARGET': 'ctl00$cphRoblox$SubmitButtonBottom', '__EVENTARGUMENT': '', '__VIEWSTATE': view_state, '__VIEWSTATEGENERATOR': view_gen, '__EVENTVALIDATION': validation, 'ctl00$cphRoblox$NameTextBox': name, 'ctl00$cphRoblox$DescriptionTextBox': tags, 'ctl00$cphRoblox$SellThisItemCheckBox': 'on', 'ctl00$cphRoblox$SellForRobux': 'on', 'ctl00$cphRoblox$RobuxPrice': price, 'ctl00$cphRoblox$EnableCommentsCheckBox': 'on', 'GenreButtons2': '1', 'ctl00$cphRoblox$actualGenreSelection': '1'}#description, 'ctl00$cphRoblox$SellThisItemCheckBox': 'on', 'ctl00$cphRoblox$SellForRobux': 'on', 'ctl00$cphRoblox$RobuxPrice': price, 'ctl00$cphRoblox$EnableCommentsCheckBox': 'on', 'GenreButtons2': '1', 'ctl00$cphRoblox$actualGenreSelection': '1'}
                q = self.http('post', 'https://www.roblox.com/my/item.aspx', assets, None, payload)
                #if 'sorry about this rather cryptic error message' in q.content:
                #        print('Upload Error: {}'.format(assetId) + ', Uploading too much, perhaps?')
                #else:
                #        print('Successfully uploaded: {}'.format(assetId))

if __name__ == '__main__':
        # instantiates RobloxBot
        bot = RobloxBot(group_id=gid)
        # starts collecting shirts on page one with a wait time of 10 seconds
        bot.get_shirts(page_num=randint(1, 24), category='14', wait=pause)
