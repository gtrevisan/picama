#!/usr/bin/env python3

"""
parse the extracted institutions and update README
"""

# global
import json

REPO = "https://github.com/gtrevisan/picama"


def image(src, alt="", height=None):
    """
    build an image string
    :param src: image src
    :param alt: image alt
    :param height: image height
    :return: string
    """

    if height:
        return f"<img src='{src}' alt='{alt}' height={height} />"

    return f"![{alt}]({src})"


def link(href, text):
    """
    build a hyperlink
    :param href: link href
    :param text: link text
    :return: string
    """

    return f"[{text}]({href})"


def badge(name):
    """
    build a badge
    :param name: workflow name
    :return: badge alt, src, href
    """

    workflow = REPO + f"/actions/workflows/{name}.yml"
    return (
        name,
        workflow + "/badge.svg",
        workflow,
    )


def main():
    """
    main function
    """

    url = "https://pica.cineca.it"

    badges = [badge(name) for name in ["build", "lint"]]
    badges += [
        (
            "Feed: validated",
            "https://badgen.net/badge/rss/validated/green?icon=rss",
            f"https://validator.w3.org/feed/check.cgi?url={REPO}/raw/cineca/rss.xml",
        ),
        (
            "Code style: black",
            "https://img.shields.io/badge/code%20style-black-000000.svg",
            "https://github.com/psf/black",
        ),
        (
            "Linting: pylint",
            "https://img.shields.io/badge/linting-pylint-yellowgreen",
            "https://github.com/PyCQA/pylint",
        ),
    ]

    # logo
    print()
    print(image(alt="logo", src="images/logo.png"))
    print()

    # title and subtitle
    print("# PicaMA 🪄")
    print("### Piattaforma Integrata Concorsi Atenei Magicamente Automatizzata")

    # badges
    print()
    for alt, src, href in badges:
        print(link(href=href, text=image(alt=alt, src=src)))

    # description
    print()
    print("🇮🇹  ")
    print(
        "PicaMA espone quotidianamente in formato RSS le opportunità lavorative",
        "presenti presso gli istituti partecipanti alla rete Pica del Cineca.  ",
    )
    print("Questo progetto non è in alcun modo affiliato con Pica od il Cineca.  ")
    print()
    print("🇬🇧  ")
    print(
        "PicaMA offers a daily RSS feed containing the job opportunities available",
        "at the institutions participating in the Pica network by Cineca.  ",
    )
    print("This project is not associated in any way with Pica or Cineca.  ")

    # content
    print()
    print("## List of Institutions")
    print()

    # parse institutions
    with open("insts.json", "r", encoding="utf-8") as fio:
        insts = json.load(fio)

    # table headers
    headers = ["logo", "institution", "url", "git", "rss"]
    fillers = ["---"] * len(headers)
    print("|" + "|".join(headers) + "|")
    print("|" + "|".join(fillers) + "|")

    # for each institute
    for href, inst in insts.items():
        pica = "/".join([url, href, ""])
        branch = REPO + f"/tree/{href}"
        feed = REPO + f"/raw/{href}/rss.xml"
        row = [
            image(alt=f"logo: {href}", src=url + inst[1], height=64),
            inst[0],
            link(
                href=pica,
                text=image(
                    alt=f"url: {href}",
                    src="images/pica.png",
                    height=32,
                ),
            ),
            link(
                href=branch,
                text=image(
                    alt=f"branch: {href}",
                    src="images/git.png",
                    height=28,
                ),
            ),
            link(
                href=feed,
                text=image(
                    alt=f"feed: {href}",
                    src="images/feed.svg",
                    height=24,
                ),
            ),
        ]
        print("|" + "|".join(row) + "|")


# command-line entry point
if __name__ == "__main__":
    main()
