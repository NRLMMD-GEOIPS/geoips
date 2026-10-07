#!/usr/bin/env python
"""Render the interface rename map artifact page to a shareable PDF.

The HTML page beside this script is the single source: it is what gets published as the
artifact and what this script renders. Do not maintain a separate PDF layout.

    conda run -n docs-pdf python build_map_pdf.py [input.html] [output.pdf]
"""
import re
import sys
from pathlib import Path

from weasyprint import CSS, HTML

HERE = Path(__file__).resolve().parent
DEFAULT_IN = HERE / "TEMP_interface_rename_map.html"

# The page links IBM Plex from Google Fonts, which is unavailable offline and slow to fetch
# during a build. Map each role onto a face that is installed locally.
FONT_SUBS = {
    '"IBM Plex Sans"': '"Nimbus Sans"',
    '"IBM Plex Mono"': '"Source Code Pro"',
    '"IBM Plex Serif"': '"Nimbus Roman"',
}

PRINT_CSS = """
@page {
  size: 17in 11in;
  margin: 0.55in 0.6in 0.5in;
  @bottom-left {
    content: "GeoIPS v2.0.0 Specification \\00b7 working draft \\00b7 branch spec-devel";
    font-family: "Nimbus Sans", sans-serif; font-size: 7pt; color: #7b8a90;
  }
  @bottom-center {
    content: "docs/dev/spec_plans/TEMP_interface_rename_map.html";
    font-family: "Source Code Pro", monospace; font-size: 7pt; color: #7b8a90;
  }
  @bottom-right {
    content: counter(page) " / " counter(pages);
    font-family: "Nimbus Sans", sans-serif; font-size: 7pt; color: #7b8a90;
  }
}

/* These overrides compete with the page's own rules at equal specificity, and WeasyPrint
   does not reliably order an injected stylesheet after the document's <style>. Hence the
   !important throughout -- it is cascade ordering, not emphasis. */

html, body { background: #ffffff !important; }

/* The wrap is sized for a browser column; the @page box is the margin here, and the table
   needs the full sheet or its right-hand columns are clipped. */
.wrap {
  max-width: none !important;
  padding-inline: 0 !important;
  padding-block: 0 !important;
}

/* The horizontal scroller exists for narrow screens and clips on paper. */
.table-scroll { overflow: visible !important; box-shadow: none !important; }
table { min-width: 0 !important; width: 100% !important; }
.scroll-hint { display: none !important; }

/* Repeat the column headings on every page; never split a row or orphan a group heading. */
thead { display: table-header-group !important; }
tr { break-inside: avoid !important; }
tr.group { break-after: avoid !important; }

/* repeat(auto-fit, minmax(...)) is not honoured, so the two definitions stack. */
.defs { display: flex !important; }
.def { flex: 1 1 0 !important; }

.defs, .rule-line, .kind-note, .note { break-inside: avoid !important; }
h2 { break-after: avoid !important; }

/* Compress the masthead so the table starts on page one rather than owning a sheet alone,
   and widen the prose measures, which are set for a 1020px column. */
.masthead { padding-bottom: 14px !important; margin-bottom: 18px !important; }
h1 { font-size: 30px !important; margin-bottom: 10px !important; }
.standfirst { font-size: 14px !important; max-width: 108ch !important; }
.def { padding: 12px 16px !important; }
.defs { margin-bottom: 16px !important; }
.rule-line { font-size: 13.5px !important; max-width: 118ch !important; margin-bottom: 18px !important; }
.kind-note { padding: 12px 16px !important; margin-bottom: 18px !important; }
.kind-note p { max-width: 80ch !important; }
.legend { margin-bottom: 10px !important; }
section + section { margin-top: 26px !important; }

/* Tighten the rows; the screen padding is generous for a 24-row table. */
tbody td { padding: 7px 12px !important; }
thead th { padding: 9px 12px !important; }
td.notes { min-width: 0 !important; }

/* Rows carrying two chips overflow a nowrap status cell and collide with the notes
   column, so let the chips stack instead. */
td.status { white-space: normal !important; }
td.status .chip { margin-bottom: 2px !important; }

/* The HTML footer is replaced by the @page margin boxes above. */
footer { display: none !important; }

/* WeasyPrint makes hrefs clickable; keep them visibly distinct in the notes column. */
td.notes a { color: #0b6360 !important; text-decoration: underline !important; }
"""


def build(src: Path, out: Path) -> None:
    html = src.read_text()

    # Drop the Google Fonts links so the build never reaches the network.
    html = re.sub(r'\s*<link rel="(?:preconnect|stylesheet)"[^>]*>', "", html)
    for plex, local in FONT_SUBS.items():
        html = html.replace(plex, local)

    # The artifact page is a fragment that the platform wraps at publish time. Split it at
    # the end of its stylesheet so the head and body land where a real document expects.
    head, _, body = html.partition("</style>")
    doc = (
        '<!DOCTYPE html>\n<html lang="en" data-theme="light">\n<head>\n'
        '<meta charset="utf-8">\n' + head + "</style>\n</head>\n<body>\n" + body +
        "\n</body>\n</html>"
    )

    HTML(string=doc, base_url=str(src)).write_pdf(out, stylesheets=[CSS(string=PRINT_CSS)])
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} KB) from {src.name}")


if __name__ == "__main__":
    source = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_IN
    target = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else source.with_suffix(".pdf")
    build(source, target)
