import requests, os, errno, json

def MakeDir(directory):
    print directory
    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    return directory

with open('users.json', 'r') as f:
    userDirectory = json.loads(f.read())

for user in userDirectory:
    username = user
    ROBLOSECURITY = userDirectory[user]

    userDir = MakeDir("./" + username + '/')

    userId = requests.get("http://api.roblox.com/users/get-by-username?username=" + username).json()["Id"]
    groups = requests.get("http://api.roblox.com/users/" + str(userId) + "/groups").json()
    #print groups

    Shirt = open("./Shirt.py", "r").read()
    Pant = open("./Pant.py", "r").read()

    for group in groups:
        groupFolder = group["Name"].encode("ascii", "ignore").replace(" ", "").replace("-", "").replace(".", "").replace("&", "").replace("'", "")
        if groupFolder == '':
            try:
                groupFolder = raw_input("Please manually enter the name for group " + group["Name"] + " : ")
            except Exception as e:
                #print "Tried printing group name: ", e
                groupFolder = raw_input("Please manually enter the name for group " + str(group["Id"]) + " : ")
        groupDir = MakeDir(userDir + groupFolder)
        with open(groupDir + "/Shirt.py", "w+") as groupShirt:
            groupShirt.write(Shirt.replace("gid = ''", "gid = '" + str(group["Id"]) + "'").replace("user = ''", "user = '" + username + "'").replace("ROBLOSECURITY = ''", "ROBLOSECURITY = '" + ROBLOSECURITY + "'"))
        with open(groupDir + "/Pant.py", "w+") as groupPant:
            groupPant.write(Pant.replace("gid = ''", "gid = '" + str(group["Id"]) + "'").replace("user = ''", "user = '" + username + "'").replace("ROBLOSECURITY = ''", "ROBLOSECURITY = '" + ROBLOSECURITY + "'"))
finished = raw_input("Press enter to exit")
