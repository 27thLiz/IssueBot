#!/usr/bin/python3
import re
import requests

import socket

ircsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server = "chat.freenode.net" # Server
channels = ["#godotengine-devel"] # Channels
botnick = "IssueBot" # Your bots nick
ignore_nicks = ["Gobot"] # don't talk with bots
adminname = "Hinsbart" #Your IRC nickname.
exitcode = "!IssueBot-quit"
helpcmd = "!IssueBot-help"
repos = {"godot":"godot", "demos":"godot-demo-projects", "docs":"godot-docs", "assetlib":"asset-library", "escoria":"escoria", "collada":"collada-exporter"}

ircsock.connect((server, 6667)) # Here we connect to the server using the port 6667
ircsock.send(bytes("USER "+ botnick +" "+ botnick +" "+ botnick + " " + botnick + "\n", "UTF-8")) #We are basically filling out a form with this line and saying to set all the fields to the bot nickname.
ircsock.send(bytes("NICK "+ botnick +"\n", "UTF-8")) # assign the nick to the bot


def joinchan(chan): # join channel(s).
    ircsock.send(bytes("JOIN "+ chan +"\n", "UTF-8"))
    ircmsg = ""
    while ircmsg.find("End of /NAMES list.") == -1:
        ircmsg = ircsock.recv(2048).decode("UTF-8")
        ircmsg = ircmsg.strip('\n\r')
        print(ircmsg)

def ping(): # respond to server Pings.
    ircsock.send(bytes("PONG :pingis\n", "UTF-8"))

def sendmsg(msg, target=channels[0]): # sends messages to the target.
    ircsock.send(bytes("PRIVMSG "+ target +" :"+ msg +"\n", "UTF-8"))

def send_help_msg(channel):
    sendmsg("Usage: [repo]/#[issue_num]", channel)
    sendmsg("possible values for [repo]: godot (default), demos, docs, assetlib, escoria, collada", channel)

def parse_msg(name, msg, channel):
    if len(name) > 16:
        return
    words = msg.split(" ")
    for word in words:
        if word.find("#") != -1:
            repo = "godot"
            split = word.split('#', 1)
            try_repo = split[0]
            issue = re.sub('[^0-9]','', split[1])

            if try_repo in repos:
                repo = try_repo
            elif word.find("/") != -1:
                repo = word.split("/", 1)[0]

            if repo in repos:
                generate_answer(repo, issue, channel)

def generate_answer(repo, issue, channel):
    repo_name = repos[repo]
    r = requests.get("https://api.github.com/repos/godotengine/" + repo_name + "/issues/" + issue)
    print("res code: " + str(r.status_code))
    if r.status_code == 200:
        response = r.json()
        title = response["title"]
        long_url = response["html_url"]
        header = {'user-agent': 'IssueBot/0.0.1', "content-type": "application/x-www-form-urlencoded"}
        body = {"url": long_url}
        r = requests.post("https://git.io/", headers=header, data=body)
        if r.status_code == 201:
            send_answer(repo, issue, title, r.headers["Location"], channel)

def send_answer(repo, issue, title, url, channel):
    if repo == "godot":
        repo = "#";
    else:
        repo = repo + "/#"
    message = repo + issue + ": " + title + " | " + url
    sendmsg(message, channel)


def main():
    for channel in channels:
        joinchan(channel)
    while 1:
        ircmsg = ircsock.recv(2048).decode("UTF-8")
        ircmsg = ircmsg.strip('\n\r')
        print(ircmsg)

        if ircmsg.find("PRIVMSG") != -1:
            name = ircmsg.split('!',1)[0][1:]
            privmsg = ircmsg.split('PRIVMSG',1)[1]
            channel = privmsg.split(':',1)[0].strip()
            message = privmsg.split(':',1)[1]
            print(channel)
            if name in ignore_nicks:
                continue
            parse_msg(name, message, channel)
            if message.rstrip() == exitcode:
                #sendmsg("bye!")
                if name.lower() == adminname.lower():
                    ircsock.send(bytes("QUIT \n", "UTF-8"))
                    return
                else:
                    sendmsg(name + ": check your privileges", channel)
            if message.rstrip() == helpcmd:
                send_help_msg(channel)
        else:
            if ircmsg.find("PING :") != -1:
                ping()

main()

