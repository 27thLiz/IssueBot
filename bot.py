#!/usr/bin/python3
from __future__ import print_function

# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log
import re
import requests
import sys

class MessageHandler:
    def __init__(self, bot, org, repos):
        self.bot   = bot
        self.org   = org
        self.repos = repos
        self.help_commands = ["!IssueBot-help", "!help", "!usage"]

    def parse_msg(self, name, msg, channel):
        if (msg in self.help_commands):
            self.print_usage(channel)
            return

        words = msg.split(" ")
        for word in words:
            if word.find("#") != -1:
                repo = ""
                split = word.split('#', 1)
                try_repo = split[0]

                res = re.match(r"[0-9]+", split[1])
                if not res: return

                issue = res.group(0)
                if word.find("/") != -1:
                    repo = word.split("/", 1)[0]
                elif try_repo != "":
                    repo = try_repo
                else:
                    repo = "godot"

                if repo in self.repos:
                    self.generate_answer(repo, issue, channel)
                else:
                    self.print_wrong_usage(channel, repo)


    def print_usage(self, channel):
        message = "Usage: [repo]/#[issue_number]\n" + self.get_available_repos()
        self.bot.msg(channel, message)

    def print_wrong_usage(self, channel, repo):
        message = "Unknown repository \"" + repo + "\"\n" + self.get_available_repos()
        self.bot.msg(channel, message)

    def get_available_repos(self):
        return "Available repositories: godot, demos, docs, assetlib, escoria, collada"

    def generate_answer(self, repo, issue, channel):
        repo_name = self.repos[repo]
        r = requests.get("https://api.github.com/repos/godotengine/" + repo_name + "/issues/" + issue)
        if r.status_code == 200:
            response = r.json()
            title = response["title"]
            long_url = response["html_url"]
            header = {'user-agent': 'IssueBot/0.0.1', "content-type": "application/x-www-form-urlencoded"}
            body = {"url": long_url}
            r = requests.post("https://git.io/", headers=header, data=body)
            if r.status_code == 201:
                #send_answer(repo, issue, title, r.headers["Location"], channel)
                if repo == "godot":
                    repo = "#"
                else:
                    repo = repo + "/#"
                message = repo + issue + ": " + title + " | " + r.headers["Location"]
                #sendmsg(message, channel)
                self.bot.msg(channel, message)

class IssueBot(irc.IRCClient):
    """Simple irc bot that resolves Github issues to links"""

    nickname = "IssueBot"
    ignore = ["goBot", "[-einbot2-]", "http", "https"]
    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.msgHandler = MessageHandler(self, "godotengine", {"godot":"godot", "demos":"godot-demo-projects", "docs":"godot-docs", "assetlib":"asset-library", "escoria":"escoria", "collada":"collada-exporter"})

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

    def ignore_message(self, user, message):
        if user in self.ignore:
            return True
        for ignore_str in self.ignore:
            if ignore_str in message:
                return True
        return False

    def signedOn(self):
        for channel in self.factory.channels:
            self.join(channel)

    def privmsg(self, user, channel, msg):
        user = user.split('!', 1)[0]
        if not self.ignore_message(user, msg):
            self.msgHandler.parse_msg(user,msg,channel)


class IssueBotFactory(protocol.ClientFactory):
    """A factory for IssueBots.

    A new protocol instance will be created each time we connect to the server.
    """
    protocol = IssueBot
    def __init__(self, channels):
        self.channels = channels

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print("connection failed:", reason)
        reactor.stop()

if __name__ == '__main__':
    # initialize logging
    log.startLogging(sys.stdout)

    # create factory protocol and application
    f = IssueBotFactory(["#godotengine", "#godotengine-devel", "#godotengine-docs", "godotengine-atelier"])

    # connect factory to this host and port
    reactor.connectTCP("irc.freenode.net", 6667, f)

    # run bot
    reactor.run()
