import re

def slugify(text):
    """Convert heading text to a markdown anchor link."""
    text = text.strip().lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    return text

def parse_bibtex(bibfile):
    """Parse a simple BibTeX file into a dict."""
    with open(bibfile, encoding="utf-8") as f:
        content = f.read()
    entries = re.findall(r'@(\w+)\{([^,]+),([\s\S]*?)\n\}', content)
    bib = {}
    for entry_type, key, fields in entries:
        field_dict = {}
        for field in re.findall(r'(\w+)\s*=\s*[{"]([^}"]+)[}"]', fields):
            field_dict[field[0].lower()] = field[1]
        bib[key.strip()] = field_dict
    return bib

def format_reference(key, entry):
    """Format a reference entry for Markdown, with a link if available and an anchor."""
    author = entry.get("author", "Unknown Author")
    title = entry.get("title", "No Title")
    journal = entry.get("journal", "")
    year = entry.get("year", "")
    url = entry.get("url", "")
    if url:
        title_md = f"[{title}]({url})"
    else:
        title_md = title
    return f'<a id="ref-{key}"></a>\n- **{author}**. *{title_md}*. {journal} ({year}).'

def extract_citations(md_text):
    """Extract all citation keys from the markdown text."""
    return set(re.findall(r'\[@([^\]]+)\]', md_text))

def replace_citations(md_text, cited_keys):
    """Replace [@key] with a markdown link to the reference anchor."""
    def replacer(match):
        key = match.group(1)
        if key in cited_keys:
            return f"[{key}](#ref-{key})"
        else:
            return f"[{key}](#ref-missing)"
    return re.sub(r'\[@([^\]]+)\]', replacer, md_text)

def generate_toc(md_text, toc_heading="# Table of Contents"):
    """Generate a markdown ToC for # and ## headings after the ToC heading."""
    lines = md_text.splitlines()
    toc_start = None
    for i, line in enumerate(lines):
        if line.strip().lower() == toc_heading.lower():
            toc_start = i
            break
    if toc_start is None:

        for i, line in enumerate(lines):
            if re.match(r'^# ', line):
                toc_start = i
                break
    toc_lines = []
    for line in lines[toc_start+1:]:
        match = re.match(r'^(#{1,2})\s+(.+)', line)
        if match:
            title = match.group(2).strip()
            if title.lower() == toc_heading[2:].strip().lower():
                continue 
            level = len(match.group(1))
            anchor = slugify(title)
            indent = '  ' * (level - 1)
            toc_lines.append(f"{indent}- [{title}](#{anchor})")
    return f"{toc_heading}\n\n" + "\n".join(toc_lines) + "\n"

def insert_or_update_toc(md_text, toc_heading="# Table of Contents"):
    """Insert or update the ToC section in the markdown text."""
    toc_pattern = re.compile(
        rf'{re.escape(toc_heading)}[\s\S]*?(?=\n# |\Z)', re.IGNORECASE
    )
    toc = generate_toc(md_text, toc_heading)
    if toc_heading.lower() in md_text.lower():
        md_text = toc_pattern.sub(toc, md_text, count=1)
    else:
        md_text = re.sub(
            r'(^# .+\n)', r'\1\n' + toc + '\n', md_text, count=1
        )
    return md_text

def insert_or_update_references(md_text, references_md):
    """Insert or update the References section in the markdown text."""
    if "# References" in md_text:
        md_text = re.sub(r'# References[\s\S]*', references_md, md_text)
    else:
        md_text += "\n\n" + references_md
    return md_text

def main(md_file, bib_file, output_file):
    with open(md_file, encoding="utf-8") as f:
        md_text = f.read()
    bib = parse_bibtex(bib_file)
    cited_keys = extract_citations(md_text)

    md_text = replace_citations(md_text, cited_keys)

    md_text = insert_or_update_toc(md_text)

    references = []
    for key in cited_keys:
        if key in bib:
            references.append(format_reference(key, bib[key]))
        else:
            references.append(f'<a id="ref-{key}"></a>\n- **{key}**: Not found in bibliography.')
    references_md = "# References\n\n" + "\n".join(references)

    md_text = insert_or_update_references(md_text, references_md)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(md_text)

if __name__ == "__main__":
    main("main.md", "references.bib", "compleatedpaper.md")
