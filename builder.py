import os
import requests
import json

from datetime import datetime

GITHUB_API_TOKEN = os.environ['GITHUB_API_TOKEN']

# GITHUB_API_HEADER_ACCEPT = "Accept: application/vnd.github.v3+json"
GITHUB_API_HEADER_ACCEPT = "Accept: application/vnd.github+json"

GITHUB_API_URL = "https://api.github.com"
GITHUB_API_REST = "/user/starred"

GITHUB_REPO_URL = "https://github.com/bormaxi8080/github-starred-repos-builder"

HEADERS = {
    "Accept": GITHUB_API_HEADER_ACCEPT,
    "Authorization": "token {0}".format(GITHUB_API_TOKEN)
}

MD_DOCUMENT_HEADER = "## List of GitHub starred repositories"
MD_DOCUMENT_GENERATION = "This document generated automatically, see {0} for details".format(GITHUB_REPO_URL)
MD_DOCUMENT_LINE_SEPARATOR = "\r\n"
MD_DOCUMENT_GROUP_SEPARATOR = "----"


def fetch_starred_repos(page=""):
    params = None
    if page != '':
        params = {"page": page}

    res = requests.get(url="{0}{1}".format(GITHUB_API_URL, GITHUB_API_REST),
                       params=params,
                       headers=HEADERS)

    last_page = True
    if 'rel="next"' in res.headers["Link"]:
        last_page = False

    return {
        "last_page": last_page,
        "repos": res.json()
    }


def _separate(document):
    return document + "{0}{1}".format(MD_DOCUMENT_LINE_SEPARATOR, MD_DOCUMENT_LINE_SEPARATOR)


def _save_document(path, document_data):
    with open(path, "w") as f:
        f.write(document_data)
    print("Document saved: {0}".format(path))
    return


def _save_json(path, json_data):
    with open(path, "w") as f:
        json.dump(json_data, f, indent=2)
    print("Document saved: {0}".format(path))
    return


if __name__ == '__main__':
    print("Welcome to GitHub starred repos builder!")
    print("See {0} for details".format(GITHUB_REPO_URL))

    STARRED_REPOS = []
    fetched_page = 1

    print("Fetching GitHub starred repos...")

    # Fetch first page
    print("Pages fetched: {0}".format(fetched_page))
    fetched_result = fetch_starred_repos()
    STARRED_REPOS.extend(fetched_result["repos"])

    # Fetch other pages in loop if exists
    if not fetched_result["last_page"]:
        while not fetched_result["last_page"]:
            fetched_page = fetched_page + 1
            print("Pages fetched: {0}".format(fetched_page))
            fetched_result = fetch_starred_repos(page="{0}".format(fetched_page))
            STARRED_REPOS.extend(fetched_result["repos"])

    print("Repos fetched: {0}".format(len(STARRED_REPOS)))

    # Sort array by repository name
    SORTED_REPOS = sorted(STARRED_REPOS, key=lambda x: x['name'])

    DOCUMENT_DATE = "Created at: {0}".format(datetime.now().date().strftime("%Y-%m-%d"))

    # Generate Markdown document
    MD_DOCUMENT = MD_DOCUMENT_HEADER + MD_DOCUMENT_LINE_SEPARATOR + MD_DOCUMENT_LINE_SEPARATOR + \
        MD_DOCUMENT_GENERATION + MD_DOCUMENT_LINE_SEPARATOR + MD_DOCUMENT_LINE_SEPARATOR + \
        "(c) @bormaxi8080, 2023" + MD_DOCUMENT_LINE_SEPARATOR + MD_DOCUMENT_LINE_SEPARATOR + \
        DOCUMENT_DATE + MD_DOCUMENT_LINE_SEPARATOR + MD_DOCUMENT_LINE_SEPARATOR + \
        "Starred repositories count: {0}".format(len(STARRED_REPOS)) + \
        MD_DOCUMENT_LINE_SEPARATOR + MD_DOCUMENT_LINE_SEPARATOR + \
        MD_DOCUMENT_GROUP_SEPARATOR + MD_DOCUMENT_LINE_SEPARATOR + MD_DOCUMENT_LINE_SEPARATOR

    # Save repos to document structure
    print("Generating Markdown document...")
    for repo in SORTED_REPOS:
        # NOTE: Simplification of the output: image badges have been removed, since with a large number of repositories,
        # a document is generated that is too large and the page freezes.

        # Repository link
        MD_DOCUMENT += "### [{0}]({1}) from [{2}]({3})".format(
            str(repo["name"]), str(repo["html_url"]),
            str(repo["owner"]["login"]), str(repo["owner"]["html_url"])
        )
        MD_DOCUMENT = _separate(MD_DOCUMENT)
        # Author
        # MD_DOCUMENT += "[![GitHub](https://img.shields.io/badge/GitHub-Profile-brightgreen?logo=github)](https://github.com/{0})".format(
        #    str(repo["owner"]["login"]))

        # Description
        if repo["description"] is None:
            MD_DOCUMENT += "No project description"
        else:
            MD_DOCUMENT += str(repo["description"])
        MD_DOCUMENT = _separate(MD_DOCUMENT)

        # Stars
        MD_DOCUMENT += "**Stars:** {0}".format(str(repo["stargazers_count"]))
        # MD_DOCUMENT += " [![GitHub stars](https://img.shields.io/github/stars/{0}/{1}.svg?style=social&label=Stars)]({2})".format(
        #    str(repo["owner"]["login"]), str(repo["name"]), str(repo["html_url"])
        # )

        # First commit (created_at)
        # MD_DOCUMENT += " [![GitHub creation date](https://img.shields.io/badge/Created%20on-{0}-brightgreen.svg)]({1})".format(
        #    datetime.strptime(str(repo["created_at"]), '%Y-%m-%dT%H:%M:%SZ').strftime("%Y--%m--%d"),
        #    str(repo["html_url"])
        # )
        MD_DOCUMENT += " / **Created on:** {0}".format(
            datetime.strptime(str(repo["created_at"]), '%Y-%m-%dT%H:%M:%SZ').strftime("%Y-%m-%d"))

        # Last commit
        # MD_DOCUMENT += " [![GitHub last commit](https://img.shields.io/github/last-commit/{0}/{1}.svg?color=blue)]({2})".format(
        #    str(repo["owner"]["login"]), str(repo["name"]), str(repo["html_url"])
        # )
        MD_DOCUMENT += " / **Last commit:** {0}".format(
            datetime.strptime(str(repo["updated_at"]), '%Y-%m-%dT%H:%M:%SZ').strftime("%Y-%m-%d"))

        # Tag
        # MD_DOCUMENT += " [![GitHub tags](https://img.shields.io/github/v/tag/{0}/{1}.svg)]({2})".format(
        #    str(repo["owner"]["login"]), str(repo["name"]), str(repo["html_url"])
        # )

        MD_DOCUMENT = _separate(MD_DOCUMENT)

        # Topics
        if not repo["topics"] is None:
            topics = repo["topics"]
            if len(topics) > 0:
                topics_ = ["#" + item for item in topics]
                str_topics = " ".join(topics_)
                # str_topics = "%2C%20".join(topics_).replace("-", "\u2013")
                # MD_DOCUMENT += "[![GitHub topics](https://img.shields.io/badge/Topics-{0}-brightgreen.svg)]({1})".format(
                #    str_topics,
                #    str(repo["html_url"])
                # )
                MD_DOCUMENT += "**Topics:** {0}".format(str_topics)
                MD_DOCUMENT = _separate(MD_DOCUMENT)

        # Repository Url
        MD_DOCUMENT += "**Repository Url:** {0}".format(str(repo["html_url"]))
        MD_DOCUMENT = _separate(MD_DOCUMENT)

        # Clone
        # MD_DOCUMENT += "[![GitHub clone](https://img.shields.io/badge/GitHub-Clone-green?logo=github)]({0})".format(str(repo["clone_url"]))
        MD_DOCUMENT += "**Clone Url:** {0}".format(str(repo["clone_url"]))
        MD_DOCUMENT = _separate(MD_DOCUMENT)

        MD_DOCUMENT += MD_DOCUMENT_GROUP_SEPARATOR
        MD_DOCUMENT = _separate(MD_DOCUMENT)

    print("Saving document data...")
    # Save Markdown document to file
    _save_document("starred_repos.md", MD_DOCUMENT)
    # Save json backup to file
    _save_json("starred_repos.json", STARRED_REPOS)

    print("Done")
