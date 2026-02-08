"""Build starred repos/contributors markdown and JSON from GitHub API."""

import argparse
import json
import os
import random
import sys
import time
from datetime import datetime

import requests
from colorama import Fore, init
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from modules.json_builder import save_json
from modules.markdown_builder import build_repos_markdown, build_contributors_markdown
from modules.pdf_builder import save_pdf_from_data

# Initialize Colorama
init(autoreset=True)

GITHUB_API_HEADER_ACCEPT = "Accept: application/vnd.github+json"
GITHUB_API_URL = "https://api.github.com"
GITHUB_API_STARRED = "/user/starred"
GITHUB_API_CONTRIBUTORS = "/users/"
GITHUB_REPO_URL = "https://github.com/bormaxi8080/osint-repos-list"

MD_DOCUMENT_HEADER = "List of GitHub Starred Repositories and Contributors"
MD_DOCUMENT_GENERATION = (
    f"This document generated automatically, see [{GITHUB_REPO_URL}]({GITHUB_REPO_URL}) for details"
)
MD_DOCUMENT_LINE_SEPARATOR = "\r\n"
MD_DOCUMENT_GROUP_SEPARATOR = "----"

MD_DOCUMENT_WARNING = (
    "**Legal and ethical note.** All tools, programs and techniques published in this repository "
    "are used for informational, educational purposes or for information security purposes. "
    "The authors are not responsible for the activities that users of these tools "
    "and techniques may carry out, and urge them not to use them to carry out "
    "harmful or destructive activities directed against other users or groups "
    "on the Internet."
)
DESCRIPTION_TEXT = (
    "This list catalogs your GitHub starred repositories and their owners, "
    "including descriptions, topics, stars, and update dates."
)
CURRENT_YEAR = datetime.now().year
COPYRIGHT_TEXT = f"(c) OSINTech, {CURRENT_YEAR}, All rights reserved"
REPOS_SUMMARY_PATH = "repos_summary.json"
PDF_NAME_PREFIX = "OSINT_Repositories_"
PDF_OUTPUT_DIR = "pdf"


def _parse_pdf_date_from_name(filename):
    """Parse PDF date from name like OSINT_Repositories_YYYY.MM.DD.pdf."""
    if not filename.startswith(PDF_NAME_PREFIX) or not filename.endswith(".pdf"):
        return None
    date_part = filename[len(PDF_NAME_PREFIX):-4]
    try:
        return datetime.strptime(date_part, "%Y.%m.%d").date()
    except ValueError:
        return None


def _normalize_repos_summary(raw_data):
    """Normalize summary data into a list of entries with parsed dates."""
    entries = []
    if isinstance(raw_data, dict):
        for name, count in raw_data.items():
            if not isinstance(name, str):
                continue
            date_value = _parse_pdf_date_from_name(name)
            if date_value is None:
                continue
            try:
                count_value = int(count)
            except (TypeError, ValueError):
                continue
            entries.append(
                {
                    "pdf": name,
                    "repos_count": count_value,
                    "date": date_value
                }
            )
        return entries

    if isinstance(raw_data, list):
        for item in raw_data:
            if not isinstance(item, dict):
                continue
            name = item.get("pdf") or item.get("file")
            if not isinstance(name, str):
                continue
            try:
                count_value = int(item.get("repos_count"))
            except (TypeError, ValueError):
                continue
            date_value = item.get("date")
            if isinstance(date_value, str):
                try:
                    date_value = datetime.strptime(date_value, "%Y-%m-%d").date()
                except ValueError:
                    date_value = None
            if date_value is None:
                date_value = _parse_pdf_date_from_name(name)
            if date_value is None:
                continue
            entries.append(
                {
                    "pdf": name,
                    "repos_count": count_value,
                    "date": date_value
                }
            )
    return entries


def _load_repos_summary(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw_data = json.load(handle)
        return _normalize_repos_summary(raw_data)
    except (OSError, json.JSONDecodeError):
        return []


def _write_repos_summary(path, entries):
    payload = [
        {
            "pdf": entry["pdf"],
            "repos_count": entry["repos_count"],
            "date": entry["date"].isoformat()
        }
        for entry in sorted(
            entries,
            key=lambda item: (item["date"], item["pdf"])
        )
    ]
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def _get_previous_repos_count(entries, current_date):
    previous_entries = [entry for entry in entries if entry["date"] < current_date]
    if not previous_entries:
        return None
    previous_entry = max(previous_entries, key=lambda item: item["date"])
    return previous_entry["repos_count"]


def create_session_with_retries():
    """Создает сессию с автоматическими повторными попытками"""
    session = requests.Session()

    # Настройка стратегии повторных попыток
    retry_strategy = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


# Создаем глобальную сессию с retry механизмом
SESSION = create_session_with_retries()


def _get_github_headers():
    """Build GitHub API headers from environment token."""
    token = os.environ.get("GITHUB_API_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_API_TOKEN environment variable is not set.")
    return {
        "Accept": GITHUB_API_HEADER_ACCEPT,
        "Authorization": f"token {token}"
    }


def fetch_contributor(contributor_login, headers, max_retries=3):
    """Fetch GitHub contributor data with retry handling."""
    not_found = (
        "{'message': 'Not Found', "
        "'documentation_url': 'https://docs.github.com/rest/users/users#get-a-user'}"
    )

    for attempt in range(max_retries):
        try:
            time.sleep(0.5)

            res = SESSION.get(
                url=f"{GITHUB_API_URL}{GITHUB_API_CONTRIBUTORS}{contributor_login}",
                headers=headers,
                timeout=(10, 30)
            )

            result = res.json()
            if str(result) == not_found:
                return None
            else:
                return result

        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.ChunkedEncodingError) as e:
            print(
                Fore.RED
                + f"Ошибка при запросе контрибьютора {contributor_login}: {e}"
            )
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(
                    Fore.YELLOW
                    + f"Повторная попытка через {wait_time} секунд... "
                    f"({attempt + 1}/{max_retries})"
                )
                time.sleep(wait_time)
            else:
                print(
                    Fore.RED
                    + (
                        f"Не удалось получить данные контрибьютора "
                        f"{contributor_login} после {max_retries} попыток"
                    )
                )
                return None

        except requests.exceptions.RequestException as e:
            print(
                Fore.RED
                + f"Ошибка при запросе контрибьютора {contributor_login}: {e}"
            )
            return None

        except ValueError as e:
            print(
                Fore.RED
                + f"Ошибка разбора ответа контрибьютора {contributor_login}: {e}"
            )
            return None

    return None


def fetch_starred_repos(page="", headers=None, max_retries=3):
    """Fetch starred repositories for the authenticated user."""
    if headers is None:
        headers = _get_github_headers()
    params = None
    if page != '':
        params = {"page": page}

    for attempt in range(max_retries):
        try:
            time.sleep(0.5)

            res = SESSION.get(
                url=f"{GITHUB_API_URL}{GITHUB_API_STARRED}",
                params=params,
                headers=headers,
                timeout=(10, 30)
            )

            res.raise_for_status()

            last_page = True
            if 'rel="next"' in res.headers.get("Link", ""):
                last_page = False

            return {
                "last_page": last_page,
                "repos": res.json()
            }

        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.ChunkedEncodingError) as e:
            print(Fore.RED + f"Ошибка при запросе репозиториев (страница {page}): {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(
                    Fore.YELLOW
                    + f"Повторная попытка через {wait_time} секунд... "
                    f"({attempt + 1}/{max_retries})"
                )
                time.sleep(wait_time)
            else:
                print(Fore.RED + f"Не удалось получить репозитории после {max_retries} попыток")
                return {"last_page": True, "repos": []}

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                wait_time = 60
                print(Fore.YELLOW + f"Rate limit превышен. Ожидание {wait_time} секунд...")
                time.sleep(wait_time)
                if attempt < max_retries - 1:
                    continue
            print(Fore.RED + f"HTTP ошибка: {e}")
            return {"last_page": True, "repos": []}

        except requests.exceptions.RequestException as e:
            print(Fore.RED + f"Ошибка при запросе репозиториев (страница {page}): {e}")
            return {"last_page": True, "repos": []}

        except ValueError as e:
            print(Fore.RED + f"Ошибка разбора ответа репозиториев (страница {page}): {e}")
            return {"last_page": True, "repos": []}

    return {"last_page": True, "repos": []}


def _save_document(path, document_data):
    """Write a UTF-8 text document to disk."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(document_data)
    print(Fore.GREEN + f"Document saved: {path}")
    return


def _save_json_document(path, json_data):
    """Write JSON data to disk and log success."""
    save_json(path, json_data)
    print(Fore.GREEN + f"Document saved: {path}")
    return


def _load_json_document(path):
    """Load JSON content from disk."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _resolve_contributors_json_path(path):
    """Resolve contributors JSON filename variations to an existing path."""
    if os.path.exists(path):
        return path
    base = os.path.basename(path)
    directory = os.path.dirname(path)
    if base == "starred_contributors.json":
        alt = os.path.join(directory, "starred_contributor.json")
    elif base == "starred_contributor.json":
        alt = os.path.join(directory, "starred_contributors.json")
    else:
        alt = None
    if alt and os.path.exists(alt):
        return alt
    return path


def generate_markdown_documents(
    repos_json_path="starred_repos.json",
    contributors_json_path="starred_contributors.json"
):
    """Generate markdown (and random) files from existing JSON data."""
    if not os.path.exists(repos_json_path):
        print(Fore.RED + f"Missing file: {repos_json_path}")
        return False
    contributors_json_path = _resolve_contributors_json_path(contributors_json_path)
    if not os.path.exists(contributors_json_path):
        print(Fore.RED + f"Missing file: {contributors_json_path}")
        return False

    print(Fore.GREEN + "Welcome to GitHub starred repos builder!")
    print(Fore.CYAN + f"See {GITHUB_REPO_URL} for details")

    repos = _load_json_document(repos_json_path)
    contributors = _load_json_document(contributors_json_path)

    print(Fore.CYAN + f"Repos loaded: {len(repos)}")
    print(Fore.CYAN + f"Contributors loaded: {len(contributors)}")

    # Sort array by repository name
    sorted_repos = sorted(repos, key=lambda x: x['name'])

    print(Fore.YELLOW + "Generating repos data...")

    document_date = f"Generated at: {datetime.now().date().strftime('%Y-%m-%d')}"

    markdown_config = {
        "header": MD_DOCUMENT_HEADER,
        "generation_text": MD_DOCUMENT_GENERATION,
        "description_text": DESCRIPTION_TEXT,
        "line_separator": MD_DOCUMENT_LINE_SEPARATOR,
        "group_separator": MD_DOCUMENT_GROUP_SEPARATOR,
        "warning_text": MD_DOCUMENT_WARNING,
        "copyright_text": (
            f"**{COPYRIGHT_TEXT}** "
            "[Substack: https://substack.com/@osintech](https://substack.com/@osintech)"
        ),
        "section_repos_title": "## Starred Repositories",
        "section_contributors_title": "## Starred Contributors"
    }

    md_document = build_repos_markdown(
        repos=sorted_repos,
        repos_count=len(repos),
        document_date=document_date,
        owners_names=None,
        config=markdown_config
    )

    print(Fore.YELLOW + "Saving document data...")
    _save_document("starred_repos.md", md_document)
    print(Fore.GREEN + "Done")

    print(Fore.YELLOW + "Generating random repos data...")
    random_sample_size = min(100, len(repos))
    random_indices = sorted(
        random.sample(range(len(repos)), k=random_sample_size)
    )
    random_repos = [repos[idx] for idx in random_indices]
    random_sorted_repos = sorted(random_repos, key=lambda x: x['name'])
    md_document_random = build_repos_markdown(
        repos=random_sorted_repos,
        repos_count=len(random_repos),
        document_date=document_date,
        owners_names=None,
        config=markdown_config
    )

    print(Fore.YELLOW + "Saving random document data...")
    _save_json_document("starred_repos_random.json", random_repos)
    _save_document("starred_repos_random.md", md_document_random)
    print(Fore.GREEN + "Done")

    print(Fore.YELLOW + "Generating contributors data...")

    md_document_contributors = build_contributors_markdown(
        contributors=contributors,
        document_date=document_date,
        config=markdown_config
    )

    print(Fore.YELLOW + "Saving document data...")
    _save_document("starred_contributors.md", md_document_contributors)
    print(Fore.GREEN + "Done")
    return True


def generate_json_documents():
    """Fetch GitHub data and generate JSON files."""
    print(Fore.GREEN + "Welcome to GitHub starred repos builder!")
    print(Fore.CYAN + f"See {GITHUB_REPO_URL} for details")

    headers = _get_github_headers()

    starred_repos = []
    fetched_page = 1
    starred_owners_names = []
    starred_owners = []

    print(Fore.YELLOW + "Fetching GitHub starred repos...")

    # Fetch first page
    print(Fore.BLUE + f"Pages fetched: {fetched_page}")
    fetched_result = fetch_starred_repos(headers=headers)
    starred_repos.extend(fetched_result["repos"])

    # Fetch other pages in loop if exists
    if not fetched_result["last_page"]:
        while not fetched_result["last_page"]:
            fetched_page += 1
            print(Fore.BLUE + f"Pages fetched: {fetched_page}")
            fetched_result = fetch_starred_repos(page=f"{fetched_page}", headers=headers)
            starred_repos.extend(fetched_result["repos"])

    print(Fore.CYAN + f"Repos fetched: {len(starred_repos)}")

    print(Fore.YELLOW + "Saving repos JSON data...")
    _save_json_document("starred_repos.json", starred_repos)
    print(Fore.GREEN + "Done")

    starred_repos_sorted = sorted(starred_repos, key=lambda x: x['name'])
    for repo in starred_repos_sorted:
        owner_login = str(repo["owner"]["login"])
        if owner_login not in starred_owners_names:
            starred_owners_names.append(owner_login)

    starred_owners_names.sort()

    print(Fore.YELLOW + "Generating contributors data...")
    print(Fore.CYAN + f"Fetching {len(starred_owners_names)} contributors data...")
    for idx, owner_login in enumerate(starred_owners_names, 1):
        print(
            Fore.BLUE
            + f"Fetching contributor {idx}/{len(starred_owners_names)}: {owner_login}"
        )
        owner_data = fetch_contributor(owner_login, headers=headers)
        if owner_data is not None:
            starred_owners.append(owner_data)

    _save_json_document("starred_contributors.json", starred_owners)
    print(Fore.GREEN + "Done")


def generate_topics_json(
    repos_json_path="starred_repos.json",
    output_path="starred_topics.json"
):
    """Build starred_topics.json from starred repos data."""
    if not os.path.exists(repos_json_path):
        print(Fore.RED + f"Missing file: {repos_json_path}")
        return False

    print(Fore.YELLOW + "Generating topics data...")

    repos = _load_json_document(repos_json_path)
    topics_map = {}
    for repo in repos:
        topics = repo.get("topics") or []
        if not isinstance(topics, list):
            continue
        full_name = repo.get("full_name")
        html_url = repo.get("html_url")
        if not isinstance(full_name, str) or not isinstance(html_url, str):
            continue
        repo_entry = {"full_name": full_name, "html_url": html_url}
        for topic in topics:
            if not isinstance(topic, str):
                continue
            topic = topic.strip()
            if not topic:
                continue
            topics_map.setdefault(topic, []).append(repo_entry)

    topics_payload = []
    for topic in sorted(topics_map, key=lambda value: value.lower()):
        repos_list = topics_map[topic]
        seen = set()
        unique_repos = []
        for item in repos_list:
            key = (item["full_name"], item["html_url"])
            if key in seen:
                continue
            seen.add(key)
            unique_repos.append(item)
        unique_repos.sort(key=lambda item: item["full_name"].lower())
        topics_payload.append({"topic": topic, "repositories": unique_repos})

    _save_json_document(output_path, topics_payload)
    print(Fore.GREEN + "Done")
    return True


def generate_startme_html(
    topics_json_path="starred_topics.json",
    output_path="starred_repos.html",
    columns=4
):
    """Build start.me-compatible HTML bookmarks from topics JSON."""
    if not os.path.exists(topics_json_path):
        print(Fore.RED + f"Missing file: {topics_json_path}")
        return False

    print(Fore.YELLOW + "Generating start.me bookmarks...")

    topics = _load_json_document(topics_json_path)
    if not isinstance(topics, list):
        print(Fore.RED + f"Invalid topics data in {topics_json_path}")
        return False

    filtered_topics = []
    for item in topics:
        if not isinstance(item, dict):
            continue
        topic_name = item.get("topic")
        repositories = item.get("repositories")
        if not isinstance(topic_name, str) or not isinstance(repositories, list):
            continue
        if len(repositories) <= 20:
            continue
        filtered_topics.append(
            {
                "topic": topic_name,
                "repositories": repositories
            }
        )

    filtered_topics.sort(key=lambda entry: entry["topic"].lower())
    for entry in filtered_topics:
        entry["repositories"] = sorted(
            entry["repositories"],
            key=lambda repo: str(repo.get("full_name", "")).lower()
        )

    timestamp = str(int(time.time()))

    def _escape(value):
        return (
            str(value)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    lines = [
        "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
        "<!-- This is an automatically generated file.",
        "     It will be read and overwritten.",
        "     DO NOT EDIT! -->",
        '<META CONTENT="text/html; charset=UTF-8" HTTP-EQUIV="Content-Type">',
        "<TITLE>Bookmarks</TITLE>",
        "<H1>Bookmarks</H1>",
        "<DL><p>",
        (
            f'<DT><H3 FOLDED="true" PAGE="true" ADD_DATE="{timestamp}" '
            f'LAST_MODIFIED="{timestamp}">Starred Repositories</H3>'
        ),
        "<DL><p>"
    ]

    for entry in filtered_topics:
        topic_name = _escape(entry["topic"])
        lines.append(
            (
                f'<DT><H3 FOLDED="true" BOOKMARKS="true" FEEDS="false" '
                f'ADD_DATE="{timestamp}" LAST_MODIFIED="{timestamp}">'
                f'{topic_name}</H3>'
            )
        )
        lines.append("<DL><p>")
        for repo in entry["repositories"]:
            full_name = repo.get("full_name")
            html_url = repo.get("html_url")
            if not isinstance(full_name, str) or not isinstance(html_url, str):
                continue
            lines.append(
                (
                    f'<DT><A HREF="{_escape(html_url)}" '
                    f'ADD_DATE="{timestamp}" LAST_MODIFIED="{timestamp}">'
                    f"{_escape(full_name)}</A>"
                )
            )
        lines.append("</DL><p>")

    lines.append("</DL><p>")
    lines.append("</DL><p>")

    _save_document(output_path, "\n".join(lines))
    print(Fore.GREEN + "Done")
    return True


def generate_pdf_from_json(
    repos_json_path="starred_repos.json",
    contributors_json_path="starred_contributors.json",
    output_path=None
):
    """Generate the PDF from existing JSON files."""
    if not os.path.exists(repos_json_path):
        print(Fore.RED + f"Missing file: {repos_json_path}")
        return False
    contributors_json_path = _resolve_contributors_json_path(contributors_json_path)
    if not os.path.exists(contributors_json_path):
        print(Fore.RED + f"Missing file: {contributors_json_path}")
        return False

    repos = _load_json_document(repos_json_path)
    contributors = _load_json_document(contributors_json_path)
    document_date = f"Generated at: {datetime.now().date().strftime('%Y-%m-%d')}"
    if output_path is None:
        date_stamp = datetime.now().strftime("%Y.%m.%d")
        output_path = os.path.join(
            PDF_OUTPUT_DIR,
            f"{PDF_NAME_PREFIX}{date_stamp}.pdf"
        )
    else:
        output_dir = os.path.dirname(output_path)
        if output_dir == "":
            output_path = os.path.join(PDF_OUTPUT_DIR, output_path)

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    pdf_name = os.path.basename(output_path)
    current_date = _parse_pdf_date_from_name(pdf_name) or datetime.now().date()
    current_count = len(repos)
    summary_entries = _load_repos_summary(REPOS_SUMMARY_PATH)
    previous_count = _get_previous_repos_count(summary_entries, current_date)
    if previous_count is None:
        newly_added = current_count
    else:
        newly_added = current_count - previous_count
        if newly_added < 0:
            newly_added = 0

    print(Fore.YELLOW + "Generating PDF document...")
    pdf_config = {
        "repos_header": {
            "header": MD_DOCUMENT_HEADER,
            "description_text": DESCRIPTION_TEXT,
            "generation_text": (
                "This document generated automatically. "
                "See project repository for details:"
            ),
            "repo_url": GITHUB_REPO_URL,
            "copyright_text": COPYRIGHT_TEXT,
            "copyright_bold": True,
            "copyright_link_prefix": "Substack: ",
            "copyright_link_text": "https://substack.com/@osintech",
            "copyright_link_url": "https://substack.com/@osintech",
            "warning_text": MD_DOCUMENT_WARNING
        },
        "contributors_header": {
            "header": MD_DOCUMENT_HEADER,
            "description_text": DESCRIPTION_TEXT,
            "generation_text": "This document generated automatically. See:",
            "repo_url": GITHUB_REPO_URL,
            "copyright_text": f"(c) @OSINTech, {CURRENT_YEAR}",
            "warning_text": MD_DOCUMENT_WARNING
        },
        "section_repos_title": "Starred Repositories",
        "section_contributors_title": "Starred Contributors",
        "footer_text": COPYRIGHT_TEXT,
        "footer_show_page_number": True
    }
    success = save_pdf_from_data(
        output_path,
        repos,
        contributors,
        document_date,
        pdf_config,
        newly_added
    )
    if success:
        summary_entries = [
            entry
            for entry in summary_entries
            if entry["pdf"] != pdf_name
        ]
        summary_entries.append(
            {
                "pdf": pdf_name,
                "repos_count": current_count,
                "date": current_date
            }
        )
        _write_repos_summary(REPOS_SUMMARY_PATH, summary_entries)
    return success


def _parse_args(argv):
    """Parse CLI arguments and normalize the mode option."""
    parser = argparse.ArgumentParser(
        description="Build starred repos/contributors markdown and PDF documents."
    )
    parser.add_argument(
        "--mode",
        "-m",
        choices=["json", "markdown", "pdf", "topics", "startme", "full"],
        default="full",
        help=(
            "json: generate json only; markdown: generate md only; pdf: generate pdf only; "
            "topics: generate topics only; startme: generate start.me bookmarks only; "
            "full: json then topics then markdown then pdf then startme."
        )
    )
    if not argv:
        args, unknown = parser.parse_known_args([])
        args.mode = "full"
        return args

    args, unknown = parser.parse_known_args(argv)

    for arg in unknown:
        if arg.startswith("mode="):
            mode_value = arg.split("=", 1)[1].strip().lower()
            if mode_value not in {"json", "markdown", "pdf", "topics", "startme", "full"}:
                print(Fore.RED + f"Unknown mode: {mode_value}")
                sys.exit(2)
            args.mode = mode_value
            break

    return args


def main():
    """Run the builder based on CLI mode."""
    args = _parse_args(sys.argv[1:])

    if args.mode == "json":
        generate_json_documents()
        return

    if args.mode == "markdown":
        success = generate_markdown_documents()
        if not success:
            sys.exit(1)
        return

    if args.mode == "pdf":
        success = generate_pdf_from_json()
        if not success:
            sys.exit(1)
        return

    if args.mode == "topics":
        success = generate_topics_json()
        if not success:
            sys.exit(1)
        return

    if args.mode == "startme":
        success = generate_startme_html()
        if not success:
            sys.exit(1)
        return

    if args.mode == "full":
        generate_json_documents()
        success = generate_topics_json()
        if not success:
            sys.exit(1)
        success = generate_markdown_documents()
        if not success:
            sys.exit(1)
        success = generate_pdf_from_json()
        if not success:
            sys.exit(1)
        success = generate_startme_html()
        if not success:
            sys.exit(1)
        return

    print(Fore.RED + f"Unsupported mode: {args.mode}")
    sys.exit(2)


if __name__ == '__main__':
    main()
