import requests
from html.parser import HTMLParser
import sys
import json
import re
import datetime
from urllib3.exceptions import InsecureRequestWarning
import selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
now = datetime.datetime.now()

proxies = {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}
headers = {
    "Host":"portal.tedankara.k12.tr",
    "User-Agent":"Mozilla/5.0 (X11; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0",
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language":"en-US,en;q=0.5",
    "Accept-Encoding":"gzip, deflate",
    "Content-Type":"application/x-www-form-urlencoded",
    "Origin":"https://portal.tedankara.k12.tr",
    "Connection":"close",
    "Referer":"https://portal.tedankara.k12.tr/login",
    "DNT":"1"
}

class JDParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        self.attributes = {}
        for attr in attrs:
            self.attributes[attr[0]] = attr[1]


def get_meetings(uname, passwd):
    url = "https://portal.tedankara.k12.tr/login"
    r = requests.get(url,verify=False)

    cookies = r.cookies
    content = r.content

    lines = content.splitlines()
    line  = list(filter(lambda x: b'_token' in x, lines))[0].decode("utf-8")

    parser = JDParser()
    parser.feed(line)

    parser.feed(line)
    parser.close()
    _token = parser.attributes["content"]

    data = "_token={}&kimlikno={}&sifre={}".format(_token,uname,passwd)
    r = requests.post(url,data=data,cookies=cookies,headers=headers,verify=False)
    cookies = r.cookies
    r = requests.get("https://portal.tedankara.k12.tr/veli/zoom",cookies=cookies,verify=False, headers=headers)
    content = r.json()
    data = {"current_day": content["current_day"],
            "current_class": content["current_class"],
            "current_student": content["current_student"]}

    headers2 = {"Host":"portal.tedankara.k12.tr",
                "User-Agent":"Mozilla/5.0 (X11; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0",
                "Accept":"application/json, text/plain, */*",
                "Accept-Language":"en-US,en;q=0.5",
                "Accept-Encoding":"gzip, deflate",
                "X-Requested-With":"XMLHttpRequest",
                "Content-Type":"application/json;charset=utf-8",
                "Origin":"https://portal.tedankara.k12.tr",
                "Connection":"close",
                "Referer":"https://portal.tedankara.k12.tr/",
                "DNT":"1"}
    headers2["X-XSRF-TOKEN"] = r.cookies["XSRF-TOKEN"]
    headers2["X-CSRF-TOKEN"] = _token

    r = requests.post("https://portal.tedankara.k12.tr/veli/zoom",cookies=r.cookies,verify=False, json=data, headers=headers2)
    classes = r.json()
    meetings = []
    for i in classes["meetings"]:
        data = "_token={}&student={}&id={}".format(_token, content["students"][0],i["meeting_id"])
        r = requests.post("https://portal.tedankara.k12.tr/veli/yoklama",allow_redirects=False, cookies=cookies,verify=False, data=data, headers=headers)
        data = r.content.decode()
        if "Location" not in data:
            continue
        for j in data.split("\n"):
            items = j.split(" ")
            if items[0] == "Location:":
                invitation = items[-1]
        try:
            m = re.compile("https:\/\/zoom\.us\/j\/([0-9]*)\?.*pwd=([^#]*)")
            g = m.search(invitation)
            meeting_url = f"zoommtg://zoom.us/join?confno={g.group(1)}&zc=0&browser=chrome&pwd={g.group(2)}"
            http_url = f"https://zoom.us/j/{g.group(1)}?pwd={g.group(2)}"
            meetings.append({"meeting_url": meeting_url,
                             "class": i["topic"],
                             "time":i["meeting_time"],
                             "http_url":http_url})
        except Exception as e:
            print(e)

    return meetings


