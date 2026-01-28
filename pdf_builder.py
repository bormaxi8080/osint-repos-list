"""PDF generation helpers for OSINT repositories list."""

from colorama import Fore

from pdf_estimate import _estimate_repo_block_height
from pdf_fonts import OSINTPDF, _configure_pdf_fonts, _set_pdf_font
from pdf_fpdf import FPDF
from pdf_header import _write_header_section
from pdf_render import (
    _pdf_draw_separator,
    _pdf_write_icon_bold_label_links,
    _pdf_write_icon_bold_label_value,
    _pdf_write_icon_bold_label_with_link,
    _pdf_write_label_with_link,
    _pdf_write_starred_bold_label_value,
    _pdf_write_wrapped_text
)
from pdf_utils import _format_github_date


def save_pdf_from_data(path, repos, users, document_date, config, new_since=None):
    """Generate and save the PDF from repository and user data."""
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

    _write_header_section(
        pdf,
        config["repos_header"],
        document_date,
        max_width,
        include_warning=True,
        include_count=len(repos),
        include_new_since=new_since
    )

    _set_pdf_font(pdf, bold=True, size=16)
    _pdf_write_wrapped_text(
        pdf,
        config["section_repos_title"],
        max_width,
        line_height=7,
        spacing=3
    )

    sorted_repos = sorted(repos, key=lambda x: str(x.get("name", "")).lower())
    for repo in sorted_repos:
        repo_block_height = _estimate_repo_block_height(pdf, repo, max_width)
        if pdf.get_y() + repo_block_height > pdf.page_break_trigger:
            pdf.add_page()
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

    pdf.add_page()

    _write_header_section(
        pdf,
        config["users_header"],
        document_date,
        max_width
    )

    _set_pdf_font(pdf, bold=True, size=13)
    _pdf_write_wrapped_text(
        pdf,
        config["section_users_title"],
        max_width,
        line_height=6,
        spacing=3
    )

    sorted_users = sorted(users, key=lambda x: str(x.get("login", "")).lower())
    for owner_data in sorted_users:
        login = str(owner_data.get("login", ""))
        html_url = str(owner_data.get("html_url", ""))
        name = owner_data.get("name")
        location = owner_data.get("location")

        _set_pdf_font(pdf, bold=True, size=12)
        _pdf_write_label_with_link(
            pdf,
            "User: ",
            login,
            html_url,
            max_width,
            line_height=6
        )

        _set_pdf_font(pdf, bold=False, size=11)
        if name is not None:
            _pdf_write_wrapped_text(pdf, f"Name: {name}", max_width, spacing=1)
        if location is not None:
            _pdf_write_wrapped_text(pdf, f"Location: {location}", max_width, spacing=1)

        bio = owner_data.get("bio")
        if bio is not None:
            _pdf_write_wrapped_text(pdf, str(bio), max_width, spacing=1)

        blog = owner_data.get("blog")
        if blog is not None and str(blog) != "":
            _pdf_write_label_with_link(
                pdf,
                "Site/Blog: ",
                str(blog),
                str(blog),
                max_width
            )

        public_repos = owner_data.get("public_repos")
        if public_repos is not None and html_url:
            repos_url = f"{html_url}?tab=repositories"
            _pdf_write_label_with_link(
                pdf,
                "Public repos: ",
                str(public_repos),
                repos_url,
                max_width
            )

        followers = owner_data.get("followers")
        followers_url = owner_data.get("followers_url")
        if followers is not None and followers_url:
            _pdf_write_label_with_link(
                pdf,
                "Followers: ",
                str(followers),
                str(followers_url),
                max_width
            )

        twitter_username = owner_data.get("twitter_username")
        if twitter_username is not None:
            twitter_handle = f"@{twitter_username}"
            twitter_url = f"https://twitter.com/{twitter_username}"
            _pdf_write_label_with_link(
                pdf,
                "Twitter: ",
                twitter_handle,
                twitter_url,
                max_width
            )

        owner_email = owner_data.get("email")
        if owner_email is not None:
            mailto = f"mailto:{owner_email}"
            _pdf_write_label_with_link(
                pdf,
                "Email: ",
                str(owner_email),
                mailto,
                max_width
            )

        _pdf_draw_separator(pdf)

    pdf.output(path)
    print(Fore.GREEN + f"Document saved: {path}")
    return True
