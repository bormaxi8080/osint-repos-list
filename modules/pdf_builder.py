"""PDF generation helpers for OSINT repositories list."""

from colorama import Fore

from .pdf_estimate import (
    _estimate_contributor_block_height,
    _estimate_repo_block_height
)
from .pdf_fonts import OSINTPDF, _configure_pdf_fonts, _set_pdf_font
from .pdf_fpdf import FPDF
from .pdf_header import _write_header_section
from .pdf_render import (
    _pdf_draw_separator,
    _pdf_write_bold_label_value,
    _pdf_write_bold_label_with_link,
    _pdf_write_icon_bold_label_links,
    _pdf_write_icon_bold_label_value,
    _pdf_write_icon_bold_label_with_link,
    _pdf_write_label_with_link,
    _pdf_write_starred_bold_label_value,
    _pdf_write_wrapped_text
)
from .pdf_utils import _format_github_date


def _write_repo_entry(pdf, repo, max_width):
    """Write a single repository entry in the standard layout."""
    repo_name = str(repo.get("name", ""))
    repo_url = str(repo.get("html_url", ""))
    owner = repo.get("owner") or {}
    owner_login = str(owner.get("login", ""))
    owner_url = str(owner.get("html_url", ""))

    _set_pdf_font(pdf, bold=True, size=12)
    _pdf_write_label_with_link(
        pdf,
        "Repository: ",
        repo_name,
        repo_url,
        max_width,
        line_height=6
    )
    pdf.ln(5)
    if repo_url:
        _pdf_write_icon_bold_label_with_link(
            pdf,
            "link",
            "Repository Url: ",
            repo_url,
            repo_url,
            max_width
        )
    _set_pdf_font(pdf, bold=False, size=11)
    _pdf_write_icon_bold_label_with_link(
        pdf,
        "person",
        "Repository Owner: ",
        owner_login,
        owner_url,
        max_width
    )

    description = repo.get("description")
    if description is None:
        description = "No project description"
    _pdf_write_icon_bold_label_value(
        pdf,
        "book",
        "Description: ",
        str(description),
        max_width,
        spacing=1
    )

    stars = repo.get("stargazers_count")
    created_on = _format_github_date(repo.get("created_at"))
    updated_on = _format_github_date(repo.get("updated_at"))
    _pdf_write_starred_bold_label_value(
        pdf,
        "Stars: ",
        str(stars),
        max_width,
        spacing=1
    )
    _pdf_write_icon_bold_label_value(
        pdf,
        "clock",
        "Created at: ",
        created_on,
        max_width,
        spacing=1
    )
    _pdf_write_icon_bold_label_value(
        pdf,
        "clock",
        "Last commit: ",
        updated_on,
        max_width,
        spacing=1
    )

    topics = repo.get("topics") or []
    if len(topics) > 0:
        _pdf_write_icon_bold_label_links(
            pdf,
            "info",
            "Topics: ",
            [str(item) for item in topics],
            "https://github.com/topics/",
            max_width,
            spacing=1
        )

    _pdf_draw_separator(pdf)


def _write_repositories_section(
    pdf,
    title,
    repos,
    max_width,
    empty_message="No repositories found."
):
    """Write a full repositories section using the standard entry layout."""
    _set_pdf_font(pdf, bold=True, size=16)
    _pdf_write_wrapped_text(
        pdf,
        title,
        max_width,
        line_height=7,
        spacing=3
    )

    if not isinstance(repos, list):
        repos = []
    sorted_repos = sorted(repos, key=lambda x: str(x.get("name", "")).lower())
    if len(sorted_repos) == 0:
        _set_pdf_font(pdf, bold=False, size=11)
        _pdf_write_wrapped_text(
            pdf,
            empty_message,
            max_width,
            line_height=5,
            spacing=2
        )
        return

    for repo in sorted_repos:
        repo_block_height = _estimate_repo_block_height(pdf, repo, max_width)
        if pdf.get_y() + repo_block_height > pdf.page_break_trigger:
            pdf.add_page()
        _write_repo_entry(pdf, repo, max_width)


def save_pdf_from_data(
    path,
    repos,
    contributors,
    document_date,
    config,
    new_since=None,
    new_repos=None
):
    """Generate and save the PDF from repository and contributor data."""
    if FPDF is None:
        print(
            Fore.RED
            + "Missing dependency: fpdf2. Install it with 'pip install -r requirements.txt'."
        )
        return False

    pdf = OSINTPDF()
    _configure_pdf_fonts(pdf)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.footer_text = config.get("footer_text", "")
    pdf.footer_show_page_number = config.get("footer_show_page_number", True)
    pdf.add_page()
    max_width = pdf.w - pdf.l_margin - pdf.r_margin

    link_repos = pdf.add_link()
    link_contributors = pdf.add_link()

    _write_header_section(
        pdf,
        config["repos_header"],
        document_date,
        max_width,
        include_warning=True,
        include_count=len(repos),
        include_new_since=new_since
    )

    _set_pdf_font(pdf, bold=False, size=11)
    _pdf_write_label_with_link(
        pdf,
        "",
        "Starred Repositories",
        link_repos,
        max_width,
        line_height=6
    )
    _pdf_write_label_with_link(
        pdf,
        "",
        "Starred Contributors",
        link_contributors,
        max_width,
        line_height=6
    )
    pdf.ln(2)

    if new_repos is not None:
        pdf.add_page()
        _write_repositories_section(
            pdf,
            config["section_new_repos_title"],
            new_repos,
            max_width,
            empty_message="No newly added repositories found."
        )

    pdf.add_page()
    pdf.set_link(link_repos, page=pdf.page_no(), y=pdf.t_margin)
    _write_repositories_section(
        pdf,
        config["section_repos_title"],
        repos,
        max_width,
        empty_message="No repositories found."
    )

    pdf.add_page()
    pdf.set_link(link_contributors, page=pdf.page_no(), y=pdf.t_margin)

    _set_pdf_font(pdf, bold=True, size=16)
    _pdf_write_wrapped_text(
        pdf,
        config["section_contributors_title"],
        max_width,
        line_height=7,
        spacing=3
    )

    sorted_contributors = sorted(
        contributors,
        key=lambda x: str(x.get("login", "")).lower()
    )
    for contributor_data in sorted_contributors:
        contributor_block_height = _estimate_contributor_block_height(
            pdf,
            contributor_data,
            max_width
        )
        if pdf.get_y() + contributor_block_height > pdf.page_break_trigger:
            pdf.add_page()
        login = str(contributor_data.get("login", ""))
        html_url = str(contributor_data.get("html_url", ""))
        name = contributor_data.get("name")
        location = contributor_data.get("location")

        _set_pdf_font(pdf, bold=True, size=12)
        _pdf_write_label_with_link(
            pdf,
            "Contributor: ",
            login,
            html_url,
            max_width,
            line_height=6
        )

        line_height = 5
        spacing = 1
        _set_pdf_font(pdf, bold=False, size=11)
        if name is not None:
            _pdf_write_bold_label_value(
                pdf,
                "Name: ",
                str(name),
                max_width,
                line_height=line_height,
                spacing=spacing
            )
        if location is not None:
            _pdf_write_bold_label_value(
                pdf,
                "Location: ",
                str(location),
                max_width,
                line_height=line_height,
                spacing=spacing
            )

        bio = contributor_data.get("bio")
        if bio is not None:
            _pdf_write_wrapped_text(
                pdf,
                str(bio),
                max_width,
                line_height=line_height,
                spacing=spacing
            )

        blog = contributor_data.get("blog")
        if blog is not None and str(blog) != "":
            _pdf_write_bold_label_with_link(
                pdf,
                "Site/Blog: ",
                str(blog),
                str(blog),
                max_width,
                line_height=line_height
            )
            pdf.ln(spacing)

        public_repos = contributor_data.get("public_repos")
        if public_repos is not None and html_url:
            repos_url = f"{html_url}?tab=repositories"
            _pdf_write_bold_label_with_link(
                pdf,
                "Public Repos: ",
                str(public_repos),
                repos_url,
                max_width,
                line_height=line_height
            )
            pdf.ln(spacing)

        followers = contributor_data.get("followers")
        followers_url = contributor_data.get("followers_url")
        if followers is not None and followers_url:
            _pdf_write_bold_label_with_link(
                pdf,
                "Followers: ",
                str(followers),
                str(followers_url),
                max_width,
                line_height=line_height
            )
            pdf.ln(spacing)

        twitter_username = contributor_data.get("twitter_username")
        if twitter_username is not None:
            twitter_handle = f"@{twitter_username}"
            twitter_url = f"https://twitter.com/{twitter_username}"
            _pdf_write_bold_label_with_link(
                pdf,
                "Twitter: ",
                twitter_handle,
                twitter_url,
                max_width,
                line_height=line_height
            )
            pdf.ln(spacing)

        contributor_email = contributor_data.get("email")
        if contributor_email is not None:
            mailto = f"mailto:{contributor_email}"
            _pdf_write_label_with_link(
                pdf,
                "Email: ",
                str(contributor_email),
                mailto,
                max_width,
                line_height=line_height
            )
            pdf.ln(spacing)

        _pdf_draw_separator(pdf)

    pdf.output(path)
    print(Fore.GREEN + f"Document saved: {path}")
    return True
