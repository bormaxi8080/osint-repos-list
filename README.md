# OSINT Repos List (Limited Access Version)

This repository encapsulates a list of repositories from the GitHub, marked with an asterisk relating to the subject of OSINT, Cybersecurity, DevOps / System Administration and specific development.

The list of 100 random starred repositories is here: [https://github.com/bormaxi8080/osint-repos-list/blob/main/starred_repos_random.md](https://github.com/bormaxi8080/osint-repos-list/blob/main/starred_repos_random.md)

----

**The full version of the list includes more than 3,000 repositories.**

**The list of repositories is updated weekly.**

----

## How to access full repositories list?

- Buy Me A Coffee:

[![Buy Me a Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/bormaxi8080)

or Subscribe Me on Substack: [@OSINTech](https://substack.com/@osintech)

- Connect Me on Substack: [@OSINTech](https://substack.com/@osintech) or Request Access in a [Google Form](https://docs.google.com/forms/d/e/1FAIpQLSdO6Kh2oG5wCe1sNXNJm6H1JOLStJmBIVMi4srR5J39FH1-pw/viewform?usp=publish-editor) by providing your email address and a link to your GitHub account

- I will grant you access to the full version list repositories posted on GitHub or send it on email.

- All Substack subscribers have access to the full list of repositories, as well as a premium version of the list in the form of bookmarks/a board for the [start.me](https://start.me) service

----

## How to build your own repos List?

Python script for build all your starred GitHub repositories information in JSON and Markdown documents named as builder.py.

To build repos list run:

```python3 builder.py```

This Python script helps for generate Markdown description document contains all your GitHub starred repositories.

This is typically needed in a situation when you have many starred repositories to view, such as collection of various utilities.

This script does simple things:

> Gets list of your starred GitHub repositories.
>
> Generate JSON and Markdown documents with your GitHub starred repos statistics

That's all.

*It works on GitHub only! (not in GitLab or BitBucket)

----

### WARNING

All tools, programs and techniques published in this repository are used for informational, educational purposes or for information security purposes. The authors are not responsible for the activities that users of these tools and techniques may carry out, and urge them not to use them to carry out harmful or destructive activities directed against other users or groups on the Internet.

----

### Important

If you have a lot of starred GitHub repositories, operations may take a long time to complete.

----

## Usage

- Clone this repository
- Create environment variable GITHUB_API_TOKEN with your GitHub API token
- Run 'python3 builder.py' and wait

![alt text](./img/shell1.png "Terminal")

![alt text](./img/shell2.png "Terminal")

- Bingo!!!

----

Results

![alt text](./img/starred_repos.json.png "JSON")

### NOTE: Simplification of the output: image badges have been removed, since with a large number of repositories, a document is generated that is too large and the page freezes

![alt text](./img/starred_repos.md.2.png "Markdown")

You can see full repos list in Markdown and JSON files.

----

### SEARCH EXAMPLE

You can search repos by keyword. For example, search repos by "SMS" keyword. Type "Ctrl+F" ("Cmd+F") and search:

![alt text](./img/starred_repos.search.1.png "Markdown")

![alt text](./img/starred_repos.search.2.png "Markdown")

----

## Related projects

I use [github-starred-repos-loader](https://github.com/bormaxi8080/github-starred-repos-loader) and [git-repos-updater](https://github.com/bormaxi8080/git-repos-updater) shell scripts to pull and update my starred GitHub collected repos locally.

----

## Notes

### How to get your GitHub personal API access token for API

[https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

----

### More about GitHub stars

[https://stars.github.com/](https://stars.github.com/)

### More about GitHub API

[https://docs.github.com/en/rest](https://docs.github.com/en/rest)

### More about GitHub Starred API

[https://docs.github.com/en/rest/activity/starring](https://docs.github.com/en/rest/activity/starring)

### More About GitHub API Pagination Requests

[https://docs.github.com/en/rest/guides/traversing-with-pagination](https://docs.github.com/en/rest/guides/traversing-with-pagination)

----

### Donates

[![Buy Me a Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/bormaxi8080)
