#!/usr/bin/env python3

"""
parse the webpage of a single institution
"""

# global
import datetime
import os
import re
import sys

# third-party
import bs4
import requests

URL = "https://pica.cineca.it"


def tag(name, content):

    """
    print content enclosed in named tag
    :param name: tag name
    :param content: tag content
    :return: string
    """

    return f"<{name}>{content}</{name}>"


def parse_old():

    """
    parse old feed
    :return: dictionary
    """

    old_feed = "old.xml"

    # check cache
    if not os.path.exists(old_feed):
        return {}

    # open cache
    with open(old_feed, "r", encoding="utf-8") as fio:
        soup = bs4.BeautifulSoup(fio, "xml")

    # parse cache
    feed = {}
    for job in soup.find_all("item"):
        code = job.find("guid").get_text()
        feed[code] = job

    return feed


def parse_job(job):

    """
    parse a single job
    """

    # parse
    code = job.find("span", class_="search_cod").get_text()
    href = job.find("a", class_="card").get("href")
    title = job.find("h1", class_="search_title").get_text()
    text = job.find("small", class_="default_call-desc")
    cdata = job.find("div", class_="default_call-data").find_all("span")
    data = [val.get_text().strip(" ") for val in cdata]

    # parse date
    if len(data) == 1:
        begin = until = None
        categ = data[0]
    elif len(data) == 2:
        begin, until = data
        categ = None
    else:
        begin, until, categ = data

    # fetch details
    link = URL + href
    print(link, file=sys.stderr, end="\t")
    result = requests.get(link, timeout=9)
    print(result.status_code, file=sys.stderr)

    # parse details
    further = bs4.BeautifulSoup(result.content, "html.parser")
    details = further.find("div", class_="default_call-testo")

    # build description
    descr = ""
    if text:
        descr += "<i>" + text.get_text() + "</i>\n"
    if begin:
        descr += "\n"
        descr += "<b>From:</b> " + begin + "\n"
        descr += "<b>To:</b> " + until + "\n"
    if categ:
        descr += "<b>Category:</b> " + categ + "\n"
    if details:
        descr += str(details)

    descr = descr.replace("\n", "<br/>").replace("<", "&lt;").replace(">", "&gt;")

    # build feed job
    print("<item>", end="")
    print(tag("guid", code), end="")
    print(tag("link", link), end="")
    print(tag("pubDate", begin), end="")
    print(tag("title", title), end="")
    print(tag("description", descr), end="")
    print("</item>")


def fetch(url, headers={}):

    """
    fetch a remote url, log in if necessary
    :param url: full remote url
    :param headers: header dictionary
    :return: requests result
    """

    print(url, file=sys.stderr, end="\t")
    result = requests.get(url=url, headers=headers, allow_redirects=False, timeout=9)
    print(result.status_code, file=sys.stderr)

    if result.status_code == 302 and not headers:
        return fetch(url=url, headers={"Cookie": os.environ.get("SESS")})

    return result


def main():

    """
    main function
    """

    repo = "https://github.com/gtrevisan/picama"
    inst = os.environ["INST"]
    new_html = inst + ".htm"

    # old feed
    feed = parse_old()

    # check cache
    if os.path.exists(new_html):

        # read
        with open(new_html, "rb") as fio:
            html = fio.read()

    else:

        # fetch
        url = URL + "/" + inst + "/"
        result = fetch(url=url)

        # read and cache
        html = result.content
        with open(new_html, "wb") as fio:
            fio.write(html)

    # parse html
    soup = bs4.BeautifulSoup(html, "html.parser")
    calls = soup.find("div", id="myCalls")

    # sanity check
    if calls:
        jobs = calls.find_all("div", class_="col-xs-12")
        errmsg = None
    elif URL + "/login" in str(html):
        jobs = []
        errmsg = "Login required"
    elif soup.find("h1").get_text() == "Non ci sono bandi":
        jobs = []
        errmsg = "No open positions"

    # start building feed
    print('<rss version="2.0"><channel>')
    print("<title>" + re.sub(r"\s+", " ", soup.title.get_text()).strip() + "</title>")
    print(
        "<lastBuildDate>" + datetime.datetime.now().strftime("%c") + "</lastBuildDate>"
    )

    # no jobs
    if not jobs:
        print("<item>", end="")
        print(tag("guid", "error"))
        print(tag("title", errmsg), end="")
        print(tag("link", repo + "/issues/new"), end="")
        print("</item>")

    # for each job
    for job in jobs:

        code = job.find("span", class_="search_cod").get_text()

        # keep cache if present
        if code in feed:
            print(feed[code])
            continue

        # parse job
        parse_job(job=job)

    print("</channel></rss>")


# command-line entry point
if __name__ == "__main__":

    main()
