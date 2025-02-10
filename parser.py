import os
import shutil
import datetime
import yaml
from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader

# -------------------------------------------------------------------
# Configuration: Exclude these top-level folder names from navigation and processing.
EXCLUDED_SECTIONS = {"_drafts"}
# -------------------------------------------------------------------

# Set up Jinja2 to load templates from the "templates" directory.
env = Environment(loader=FileSystemLoader("templates"))
template = env.get_template("base.html")

def parse_markdown_file(file_path: Path) -> (dict, str):
    """
    Parse a Markdown file to extract YAML front matter (if present)
    and the Markdown content.
    
    Expected format:
    ---
    title: My Title
    date: YYYY-MM-DD
    tags: [tag1, tag2]
    ---
    Markdown content...
    
    :param file_path: Path to the Markdown file.
    :return: Tuple (metadata_dict, markdown_content)
    """
    content = file_path.read_text(encoding="utf-8")
    metadata = {}
    md_content = content

    if content.startswith("---"):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            front_matter = parts[1]
            md_content = parts[2]
            try:
                metadata = yaml.safe_load(front_matter) or {}
            except yaml.YAMLError as e:
                print(f"YAML parsing error in {file_path}: {e}")
    return metadata, md_content.strip()

def convert_md_to_html(md_text: str, title: str, listing: list = None, nav_links: list = None) -> str:
    """
    Convert Markdown text to HTML and render it with the Jinja2 template.
    
    :param md_text: Markdown content.
    :param title: Page title.
    :param listing: Optional list of child pages (for section index pages).
    :param nav_links: Site-wide navigation links.
    :return: Rendered HTML as a string.
    """
    html_body = markdown.markdown(md_text, extensions=["extra", "codehilite"])
    rendered = template.render(
        title=title,
        content=html_body,
        year=datetime.datetime.now().year,
        listing=listing,
        nav_links=nav_links
    )
    return rendered

def normalize_date(date_val):
    """
    Convert a date value to a datetime.date object.
    
    If date_val is a string (in "YYYY-MM-DD" format), parse it.
    Otherwise, return a minimal date so that sorting works.
    """
    if isinstance(date_val, datetime.date):
        if isinstance(date_val, datetime.datetime):
            return date_val.date()
        return date_val
    elif isinstance(date_val, str) and date_val:
        try:
            return datetime.datetime.strptime(date_val, "%Y-%m-%d").date()
        except Exception:
            return datetime.date.min
    return datetime.date.min

def generate_listing(src_dir: Path, base_relative: Path) -> list:
    """
    Scan src_dir for Markdown files (excluding index.md) and for subdirectories
    (that are not excluded) with an index.md. Use their YAML metadata (title and date)
    to build a list.
    
    :param src_dir: Current directory being scanned.
    :param base_relative: The path of src_dir relative to the content root.
    :return: List of dictionaries with keys 'title', 'date', and 'url'.
    """
    listing = []
    # Process Markdown files (excluding index.md)
    for item in src_dir.iterdir():
        if item.is_file() and item.suffix.lower() == ".md" and item.name.lower() != "index.md":
            meta, _ = parse_markdown_file(item)
            page_title = meta.get("title", item.stem)
            page_date = meta.get("date", "")
            if str(base_relative) == ".":
                url = f"/{item.stem}/"
            else:
                url = f"/{base_relative.as_posix()}/{item.stem}/"
            listing.append({"title": page_title, "date": page_date, "url": url})
    # Process subdirectories with index.md (that are not excluded)
    for subdir in src_dir.iterdir():
        if subdir.is_dir() and subdir.name not in EXCLUDED_SECTIONS and (subdir / "index.md").exists():
            meta, _ = parse_markdown_file(subdir / "index.md")
            page_title = meta.get("title", subdir.name)
            page_date = meta.get("date", "")
            if str(base_relative) == ".":
                url = f"/{subdir.name}/"
            else:
                url = f"/{base_relative.as_posix()}/{subdir.name}/"
            listing.append({"title": page_title, "date": page_date, "url": url})
    listing.sort(key=lambda x: normalize_date(x.get("date", "")), reverse=True)
    return listing

def generate_nav_links(content_root: Path) -> list:
    """
    Build the navigation menu by scanning the top-level of content_root.
    
    Adds:
      - A Home link.
      - For each top-level folder with an index.md (and not in EXCLUDED_SECTIONS),
        add a link using its index.md title.
      - For each top-level standalone Markdown file (except index.md), add a link.
    
    :param content_root: The root of the content folder.
    :return: List of dictionaries with keys 'title' and 'url'.
    """
    nav = []
    # Always add Home.
    nav.append({"title": "Home", "url": "/"})
    for item in content_root.iterdir():
        if item.name in EXCLUDED_SECTIONS:
            continue
        if item.is_dir() and (item / "index.md").exists():
            meta, _ = parse_markdown_file(item / "index.md")
            nav_title = meta.get("title", item.name.capitalize())
            nav.append({"title": nav_title, "url": f"/{item.name}/"})
        elif item.is_file() and item.suffix.lower() == ".md" and item.name.lower() != "index.md":
            meta, _ = parse_markdown_file(item)
            nav_title = meta.get("title", item.stem.capitalize())
            nav.append({"title": nav_title, "url": f"/{item.stem}/"})
    return nav

def process_directory(src_dir: Path, dest_dir: Path, nav_links: list):
    """
    Walk through src_dir and process each Markdown file.
    
    - Files named index.md are treated as section index pages and get an auto‑generated
      listing of child pages.
    - Other Markdown files are treated as standalone pages.
    
    The output is written to dest_dir with "pretty URLs" (each page in its own folder
    with an index.html file).
    """
    for root, dirs, files in os.walk(src_dir):
        # Exclude folders in EXCLUDED_SECTIONS.
        dirs[:] = [d for d in dirs if d not in EXCLUDED_SECTIONS]
        for file in files:
            if file.endswith(".md"):
                md_path = Path(root) / file
                relative_path = md_path.relative_to(src_dir)
                metadata, md_content = parse_markdown_file(md_path)
                page_title = metadata.get("title", md_path.stem)

                if file.lower() == "index.md":
                    # Section index page.
                    current_dir = Path(root)
                    base_relative = current_dir.relative_to(src_dir)
                    listing = generate_listing(current_dir, base_relative)
                    html_output = convert_md_to_html(md_content, page_title, listing, nav_links)
                    output_folder = dest_dir / relative_path.parent
                else:
                    # Standalone page.
                    html_output = convert_md_to_html(md_content, page_title, None, nav_links)
                    output_folder = dest_dir / relative_path.parent / md_path.stem

                os.makedirs(output_folder, exist_ok=True)
                output_file = output_folder / "index.html"
                output_file.write_text(html_output, encoding="utf-8")
                print(f"Converted {md_path} -> {output_file}")

def copy_static(static_dir: Path, dest_dir: Path):
    """
    Copy static assets (such as CSS and images) from static_dir to the build output.
    """
    dest_static = dest_dir / "static"
    if dest_static.exists():
        shutil.rmtree(dest_static)
    shutil.copytree(static_dir, dest_static)
    print(f"Copied static assets from {static_dir} to {dest_static}")

def main():
    src_dir = Path("content")
    dest_dir = Path("build")
    static_dir = Path("static")

    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    os.makedirs(dest_dir, exist_ok=True)

    nav_links = generate_nav_links(src_dir)
    process_directory(src_dir, dest_dir, nav_links)
    copy_static(static_dir, dest_dir)
    print("Site build complete!")

if __name__ == "__main__":
    main()
