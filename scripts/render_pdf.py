"""
render_pdf.py — render the '## Tailored Resume' section of a job file into an
ATS-safe PDF (single column, no tables/columns, plain extractable text).

Playwright is OPTIONAL. If it is not installed, the script degrades gracefully:
it prints where the tailored-resume markdown already lives and exits 0, so the
tailoring workflow never hard-fails just because PDF rendering is unavailable.

Paths are resolved through workspace.py. If no output path is given, the PDF is
written into the workspace pdf dir using the job file's name.

Usage:
    python scripts/render_pdf.py data/jobs/acme-senior-pm-2026-04-07.md
    python scripts/render_pdf.py <job_file.md> <output.pdf>
"""
import sys
from pathlib import Path

import jobfile
import workspace

TEMPLATE_PATH = Path(__file__).resolve().parent / "resume_template.html"


def extract_tailored_resume(job_file: str) -> str:
    resume = jobfile.tailored_resume(jobfile.read(job_file))
    if not resume:
        raise ValueError(
            f"No tailored resume found in {job_file}.\n"
            "Run the tailoring skill on this job file first."
        )
    return resume


def md_to_html(md: str) -> str:
    """Convert a subset of Markdown to ATS-safe HTML."""
    lines = md.split("\n")
    html = []
    in_ul = False

    def close_ul():
        nonlocal in_ul
        if in_ul:
            html.append("</ul>")
            in_ul = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            close_ul()
            html.append(f"<h1>{stripped[2:].strip()}</h1>")
        elif stripped.startswith("## "):
            close_ul()
            html.append(f"<h2>{stripped[3:].strip()}</h2>")
        elif stripped.startswith("### "):
            close_ul()
            html.append(f"<h3>{stripped[4:].strip()}</h3>")
        elif stripped.startswith("- "):
            if not in_ul:
                html.append("<ul>")
                in_ul = True
            html.append(f"<li>{stripped[2:].strip()}</li>")
        elif stripped == "---":
            close_ul()  # skip horizontal rules
        elif stripped == "":
            close_ul()
            html.append("")
        else:
            close_ul()
            if stripped.startswith("**ATS Keywords") or stripped.startswith("**Top 5 Missing"):
                pass  # metadata, not part of resume output
            elif "@" in stripped and "|" in stripped:
                html.append(f'<p class="contact">{stripped}</p>')
            elif "|" in stripped and "@" not in stripped:
                html.append(f'<p class="job-meta">{stripped}</p>')
            else:
                html.append(f"<p>{stripped}</p>")

    close_ul()
    return "\n".join(html)


def build_html(resume_md: str) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    return template.replace("{{RESUME_CONTENT}}", md_to_html(resume_md))


def render(html: str, output_path: str) -> None:
    import asyncio

    from playwright.async_api import async_playwright

    async def _go():
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_content(html, wait_until="domcontentloaded")
            await page.pdf(
                path=output_path,
                format="Letter",
                margin={"top": "0.65in", "right": "0.75in",
                        "bottom": "0.65in", "left": "0.75in"},
                print_background=True,
            )
            await browser.close()

    asyncio.run(_go())


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    job_file = sys.argv[1]
    if not Path(job_file).exists():
        print(f"Error: job file not found: {job_file}", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) >= 3:
        output_pdf = sys.argv[2]
    else:
        pdf_dir = Path(workspace.paths()["pdf_dir"])
        output_pdf = str(pdf_dir / (Path(job_file).stem + ".pdf"))

    print(f"Extracting tailored resume from {job_file}...")
    resume_md = extract_tailored_resume(job_file)

    try:
        import playwright  # noqa: F401
    except ImportError:
        print(
            "\nPlaywright is not installed — skipping PDF render (this is OK).\n"
            f"Your tailored resume markdown is ready in: {job_file}\n"
            "To enable PDFs: pip install playwright && playwright install chromium",
        )
        sys.exit(0)

    Path(output_pdf).parent.mkdir(parents=True, exist_ok=True)
    print("Building ATS-safe HTML...")
    html = build_html(resume_md)
    print(f"Rendering PDF to {output_pdf}...")
    render(html, output_pdf)
    size_kb = Path(output_pdf).stat().st_size // 1024
    print(f"Done. PDF size: {size_kb} KB → {output_pdf}")


if __name__ == "__main__":
    main()
