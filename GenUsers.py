import json

def writeUser(username, roblosecurity):
    with open('users.json', 'a+') as f:
        a = f.read()
    with open('users.json', 'w') as f:
        if len(a) == 0:
            f.write(json.dumps({username:roblosecurity}))
        else:
            try:
                b = json.loads(a)
                b[username] = roblosecurity
                f.write(json.dumps(b))
            except:
                print "Error reading json file, erasing and starting from scratch"
                f.write(json.dumps({username:roblosecurity}))

while True:
    username = raw_input("Username: ")
    roblosecurity = raw_input(".ROBLOSECURITY: ")
    writeUser(username, roblosecurity)
    print "Added", username
