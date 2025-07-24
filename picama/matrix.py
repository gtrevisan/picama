#!/usr/bin/env python3

"""
parse the Pica website and extract all institutions
"""

# global
import json
import sys

# third-party
import requests
import bs4


# main function
def main():
    """
    main function
    """

    url = "https://pica.cineca.it"

    # request
    print(url, file=sys.stderr, end="\t")
    result = requests.get(url, timeout=9)
    print(result.status_code, file=sys.stderr)

    # parser
    soup = bs4.BeautifulSoup(result.content, "html.parser")
    items = soup.find_all("div", class_="card-container")
    insts = {}

    # for each job
    for item in items:
        href = item.find("a").get("href").replace("/", "")
        name = item.find("h5", class_="card-title").get_text()
        logo = item.find("img", class_="card-img-top").get("src").split("?")[0]
        insts[href] = name, logo

    with open("insts.json", "w", encoding="utf-8") as fio:
        json.dump(insts, fio)

    print(f"matrix={list(insts)}")


# command-line entry point
if __name__ == "__main__":
    main()
