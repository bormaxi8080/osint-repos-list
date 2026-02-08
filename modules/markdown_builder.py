"""Markdown generation helpers for OSINT repositories list."""

from datetime import datetime


def _separate(document, line_separator):
    """Append markdown line separators to the document."""
    return document + f"{line_separator}{line_separator}"


def build_repos_markdown(
    repos,
    repos_count,
    document_date,
    owners_names,
    config
):
    """Build the markdown document for starred repositories."""
    line_separator = config["line_separator"]
    group_separator = config["group_separator"]

    md_document = (
        "# " + config["header"] + line_separator + line_separator
        + config["description_text"] + line_separator + line_separator
        + config["generation_text"] + line_separator + line_separator
        + config["copyright_text"] + line_separator + line_separator
        + config["warning_text"] + line_separator + line_separator
        + document_date + line_separator + line_separator
        + f"**Starred repositories count:** {repos_count}"
        + line_separator + line_separator
        + config["section_repos_title"] + line_separator + line_separator + line_separator
    )

    for repo in repos:
        owner_login = str(repo["owner"]["login"])
        if owners_names is not None and owner_login not in owners_names:
            owners_names.append(owner_login)

        md_document += f"### [{repo['name']}]({repo['html_url']})"
        md_document = _separate(md_document, line_separator)
        md_document += f"Repository Url: {repo['html_url']}"
        md_document = _separate(md_document, line_separator)
        md_document += (
            f"Repository Owner: "
            f"[{repo['owner']['login']}]({repo['owner']['html_url']})"
        )
        md_document = _separate(md_document, line_separator)

        if repo["description"] is None:
            md_document += "Description: No project description"
        else:
            md_document += f"Description: {repo['description']}"
        md_document = _separate(md_document, line_separator)

        md_document += f"**Stars:** {repo['stargazers_count']}"
        created_on = datetime.strptime(
            str(repo["created_at"]), "%Y-%m-%dT%H:%M:%SZ"
        ).strftime("%Y-%m-%d")
        updated_on = datetime.strptime(
            str(repo["updated_at"]), "%Y-%m-%dT%H:%M:%SZ"
        ).strftime("%Y-%m-%d")
        md_document += f" / **Created at:** {created_on}"
        md_document += f" / **Last commit:** {updated_on}"
        md_document = _separate(md_document, line_separator)

        if repo["topics"]:
            if len(repo["topics"]) > 0:
                topics_ = ["#" + item for item in repo["topics"]]
                str_topics = " ".join(topics_)
                md_document += f"**Topics:** {str_topics}"
                md_document = _separate(md_document, line_separator)

        md_document += group_separator
        md_document = _separate(md_document, line_separator)

    return md_document


def build_contributors_markdown(contributors, document_date, config):
    """Build the markdown document for starred contributors."""
    line_separator = config["line_separator"]
    group_separator = config["group_separator"]

    md_document = (
        "# " + config["header"] + line_separator + line_separator
        + config["description_text"] + line_separator + line_separator
        + config["generation_text"] + line_separator + line_separator
        + config["copyright_text"] + line_separator + line_separator
        + document_date + line_separator + line_separator
        + config["section_contributors_title"] + line_separator + line_separator
    )

    for contributor_data in contributors:
        if "login" in contributor_data and "html_url" in contributor_data:
            if (
                contributor_data["login"] is not None
                and contributor_data["html_url"] is not None
            ):
                md_document += (
                    f"### [{contributor_data['login']}]({contributor_data['html_url']})"
                )
        if "name" in contributor_data and contributor_data["name"] is not None:
            md_document += f" ({contributor_data['name']})"
        if "location" in contributor_data and contributor_data["location"] is not None:
            md_document += f", {contributor_data['location']}"
        md_document = _separate(md_document, line_separator)

        if "bio" in contributor_data and contributor_data["bio"] is not None:
            md_document += str(contributor_data["bio"])
            md_document = _separate(md_document, line_separator)
        if (
            "blog" in contributor_data
            and contributor_data["blog"] is not None
            and str(contributor_data["blog"]) != ""
        ):
            md_document += f"Site/Blog: {contributor_data['blog']}"
            md_document = _separate(md_document, line_separator)

        if (
            "public_repos" in contributor_data
            and contributor_data["public_repos"] is not None
            and "html_url" in contributor_data
            and contributor_data["html_url"] is not None
            and "followers" in contributor_data
            and contributor_data["followers"] is not None
            and "followers_url" in contributor_data
            and contributor_data["followers_url"] is not None
        ):
            md_document += (
                f"Public repos: [{contributor_data['public_repos']}]"
                f"({contributor_data['html_url']}?tab=repositories) "
                f"/ Followers: [{contributor_data['followers']}]"
                f"({contributor_data['followers_url']})"
            )
            md_document = _separate(md_document, line_separator)

        has_contact = False
        if "twitter_username" in contributor_data \
                and contributor_data["twitter_username"] is not None:
            has_contact = True
            twitter_username = contributor_data["twitter_username"]
            md_document += (
                f"Twitter: [@{twitter_username}](https://twitter.com/{twitter_username})"
            )
            if "email" in contributor_data and contributor_data["email"] is not None:
                md_document += " / "
        if "email" in contributor_data and contributor_data["email"] is not None:
            has_contact = True
            contributor_email = contributor_data["email"]
            md_document += f"Email: [{contributor_email}](mailto:{contributor_email})"
        if has_contact:
            md_document = _separate(md_document, line_separator)

        md_document += group_separator
        md_document = _separate(md_document, line_separator)

    return md_document
