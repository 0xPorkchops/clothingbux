import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from bs4 import BeautifulSoup
import time
import math
import pickle
import json
import os
import sys

os.chdir(sys.path[0]) #Allows relative directories on linux

row = int(math.floor(time.time()/60/60/24-0.1666666666666667))-17909

header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}#str(UserAgent().chrome)}

accounts = {
    'USERNAME_HERE':'.ROBLOSECURITY_COOKIE_HERE'
    }

with open('/home/Robux/proxies.json') as f:
    proxyFile = json.load(f)

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('/home/Robux/Robux Stats-0d2ae993d8d2.json', scope)
client = gspread.authorize(creds)

spreadsheet = client.open('Robux Stats')

stockSheet = spreadsheet.worksheet('Stock')
stockGroups = stockSheet.row_values(1)

salesSheet = spreadsheet.worksheet('Robux Sales')

pendingSalesSheet = spreadsheet.worksheet('Robux Pending Sales')

payoutSheet = spreadsheet.worksheet('Group Payouts')

def save_cookies(session, filename):
    with open('./' + filename + '.cookie', 'w') as f:
        f.truncate()
        pickle.dump(session.cookies._cookies, f)

def load_cookies(session, filename):
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

def logged_in(session):
    balance = session.get('http://api.roblox.com/currency/balance').text
    if 'Forbidden' in balance:
        return False
    elif 'robux' in balance:
        return True
    else:
        return 'Error'

def login(username):
    s = requests.Session()
    s.headers.update(header)
    proxies = {
        'http': proxyFile[username],
        'https': proxyFile[username]
    }
    s.proxies = proxies
    load_cookies(s, username)
    login_status = logged_in(s)
    if login_status == False:
        print "Logging in via saved cookies failed, logging in .ROBLOSECURITY"
        s = requests.Session()
        s.headers.update(header)
        s.proxies = proxies
        s.cookies.set('.ROBLOSECURITY', accounts[username])
        login_status = logged_in(s)
        if login_status == True:
            print "Logging in via .ROBLOSECURITY succeded"
            save_cookies(s, username)
            return s
        elif login_status == False:
            print "Logging in via .ROBLOSECURITY failed, skipping"
            return "Failure"
    elif login_status == True:
        print "Logging in via saved cookies succeeded"
        return s

def http(s, op, url, params, files, data):
        r = None
        if op == 'get':
                r = s.get(url, params=params, files=files, data=data)
        elif op == 'post':
                r = s.post(url, params=params, files=files, data=data)
        if 'https://www.roblox.com/Membership/NotApproved.aspx?ID=' in r.url:
                print 'Not clear'
                soup =  BeautifulSoup(r.content, 'lxml')
                if soup.findAll('input', {'name':'ctl00$cphRoblox$ButtonAgree'}) == []:
                        print user, 'Banned, skipping...'
                        return "Banned"
                else:
                        print user, 'Suspended, reactivating...'
                        userId = s.get('http://api.roblox.com/users/get-by-username?username=' + user).json()['Id']
                        postData = {
                                '__EVENTTARGET':'',#soup.find('input', {'name':'__EVENTTARGET'}).get('value'),
                                '__EVENTARGUMENT':'',#soup.find('input', {'name':'__EVENTARGUMENT'}).get('value'),
                                '__VIEWSTATE':soup.find('input', {'name':'__VIEWSTATE'}).get('value'),
                                '__VIEWSTATEGENERATOR':soup.find('input', {'name':'__VIEWSTATEGENERATOR'}).get('value'),
                                '__EVENTVALIDATION':soup.find('input', {'name':'__EVENTVALIDATION'}).get('value'),
                                'ctl00$cphRoblox$ButtonAgree':'Reactivate My Account'#soup.find('input', {'name':'ctl00$cphRoblox$ButtonAgree'}).get('value')
                                }
                        r = s.post('https://www.roblox.com/Membership/NotApproved.aspx?ID='+str(userId), data=postData) #post to MemberNotApproved.aspx?id=8888?
                        if op == 'get':
                                return s.get(url, params=params, files=files, data=data)
                        elif op == 'post':
                                return s.post(url, params=params, files=files, data=data)
        else:
                return r

def collectStats(s, userGroups):
    stats = {}
    for index, item in enumerate(userGroups):
        r = http(s, 'get', 'https://www.roblox.com/my/groupadmin.aspx?gid=' + str(item['Id']) + '#nav-revenue', None, None, None)
        soup = BeautifulSoup(r.text, 'lxml')
        try:
            stock = int(soup.find('span', class_='robux').contents[0])
            summaryId = soup.find('div', 'summary')['data-get-url'].replace('/currency/summary/','')
            r = http(s, 'get', 'https://www.roblox.com/currency/summary/' + summaryId, None, None, None).text
            soup = BeautifulSoup(r, 'lxml')
            groupStats = soup.findAll('td', 'credit')
            sales = groupStats[0].string
            pendingSales = groupStats[1].string
            groupPayout = groupStats[2].string
            if sales is None:
                sales = 0
            else:
                sales = int(sales)
            if pendingSales is None:
                pendingSales = 0
            else:
                pendingSales = int(pendingSales)
            if groupPayout is None:
                groupPayout = 0
            else:
                groupPayout = int(groupPayout.replace("(", "").replace(")", ""))
        except Exception as e:
            print e
            print 'Couldnt get the sales for', item['id']
        stats[item['Id']] = [stock, sales, pendingSales, groupPayout]
        time.sleep(3)
    return stats

def colNumString(n):
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string

def updateRange(stats, sheet):
    dataPoint = None
    if sheet == stockSheet:
        dataPoint = 0
    elif sheet == salesSheet:
        dataPoint = 1
    elif sheet == pendingSalesSheet:
        dataPoint = 2
    elif sheet == payoutSheet:
        dataPoint = 3
    cellValues = []
    for index, item in enumerate(stockGroups):
        cellValues.append(stats[int(item)][dataPoint])
    range = sheet.range('A'+str(row)+':'+colNumString(len(stockGroups))+str(row))
    for index, item in enumerate(cellValues):
        range[index].value = item
    sheet.update_cells(range)

for index, item in enumerate(accounts):
    s = login(item)
    if s != "Failure":
        access = http(s, 'get', "https://www.roblox.com/", None, None, None)
        if access != "Banned":
            userId = http(s, 'get', 'http://api.roblox.com/users/get-by-username?username=' + item, None, None, None).json()['Id']
            userGroups = http(s, 'get', 'http://api.roblox.com/users/' + str(userId) + '/groups', None, None, None).json()
            stats = collectStats(s, userGroups)
            updateRange(stats, stockSheet)
            updateRange(stats, salesSheet)
            updateRange(stats, pendingSalesSheet)
            updateRange(stats, payoutSheet)
            print stats
        else:
            print item, "Account banned, skipping"
    else:
        print item, "Error with this account, skipping"
