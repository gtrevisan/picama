#!/usr/bin/env python3

"""
parse the webpage of a single institution
"""

# global
import os
import re
import sys
from datetime import datetime
from email.utils import formatdate

# third-party
import bs4
import requests

URL = "https://pica.cineca.it"
REPO = "https://github.com/gtrevisan/picama"


def tag(name, content, attrs=None):
    """
    print content enclosed in named tag
    :param name: tag name
    :param content: tag content
    :param attrs: attributes
    :return: string
    """

    attr_str = ""
    if attrs:
        attr_str = "".join([f' {key}="{val}"' for key, val in attrs.items()])

    return f"<{name}{attr_str}>{content}</{name}>"


def replace(string):
    """
    replace some special characters
    :return: string
    """
    for old, new in [
        ("\n", "<br/>"),
        ("<", "&lt;"),
        (">", "&gt;"),
        (" & ", " &amp; "),
        ("–", "-"),
    ]:
        string = string.replace(old, new)
    return string


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
        lines = fio.readlines()

    # parse cache
    feed = {}
    for line in lines:
        code = re.search(r">([^<>]*)</guid>", line)
        if code:
            feed[code.group(1)] = line.strip("\n")

    return feed


def parse_job(div):
    """
    parse a single job
    :param div: job div
    :return: feed line
    """

    # parse
    code = div.find("span", class_="search_cod").get_text()
    href = div.find("a", class_="card").get("href")
    title = div.find("h1", class_="search_title").get_text()
    text = div.find("small", class_="default_call-desc")
    cdata = div.find("div", class_="default_call-data").find_all("span")
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
    print(URL + href, file=sys.stderr, end="\t")
    result = requests.get(URL + href, timeout=9)
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
        date = formatdate(datetime.strptime(begin, "%d-%m-%Y %H:%M").timestamp())
    else:
        date = formatdate()
    if categ:
        descr += "<b>Category:</b> " + categ + "\n"
    if details:
        descr += re.sub('href="./', f'href="{URL}{href}', str(details))
    descr = re.sub(r'href=".?/', f'href="{URL}/', descr)

    # build line
    return (
        "<item>"
        + tag("guid", code, attrs={"isPermaLink": "false"})
        + tag("link", URL + href)
        + tag("pubDate", date)
        + tag("title", replace(title))
        + tag("description", replace(descr))
        + "</item>"
    )


def fetch(url, headers=None):
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

    inst = os.environ["INST"]
    html = inst + ".htm"

    # old feed
    old_feed = parse_old()

    # check cache
    if os.path.exists(html):
        # read
        with open(html, "rb") as fio:
            content = fio.read()

    else:
        # fetch
        url = URL + "/" + inst + "/"
        result = fetch(url=url)

        # read and cache
        content = result.content
        with open(html, "wb") as fio:
            fio.write(content)

    # parse html
    soup = bs4.BeautifulSoup(content, "html.parser")
    calls = soup.find("div", id="myCalls")

    # sanity checks
    if URL + "/login" in str(content):
        divs = []
        errmsg = "Login required"
    elif soup.find("h1").get_text() == "Non ci sono bandi":
        divs = []
        errmsg = "No open positions"
    elif calls:
        divs = calls.find_all("div", class_="col-xs-12")
        errmsg = None
    else:
        divs = []
        errmsg = None

    # new feed
    new_feed = {}

    # no jobs
    if not divs and errmsg:
        new_feed["error"] = "<item>"
        new_feed["error"] += tag("guid", "error")
        new_feed["error"] += tag("title", errmsg)
        new_feed["error"] += tag("link", REPO + "/issues/new")
        new_feed["error"] += "</item>"

    # for each job
    for div in divs:
        code = div.find("span", class_="search_cod").get_text()

        if code in old_feed:
            new_feed[code] = old_feed[code]
            print(code, file=sys.stderr)
        else:
            new_feed[code] = parse_job(div=div)

    # build and print feed
    title = re.sub(r"\s+", " ", soup.title.get_text()).strip()
    print('<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">')
    print("<channel>")
    print(tag("title", title))
    print(tag("link", f"{REPO}/tree/{inst}"))
    print(tag("description", title))
    print(tag("lastBuildDate", formatdate()))
    print("\n".join([new_feed[code] for code in sorted(new_feed)]))
    print("</channel></rss>")


# command-line entry point
if __name__ == "__main__":
    main()
