#!/usr/bin/env python3
"""Check internal consistency across the specification planning documents.

Run after any structural edit:

    python3 docs/dev/spec_plans/check_consistency.py
    python3 docs/dev/spec_plans/check_consistency.py --relink   # repair stale anchors

Exits non-zero if any check fails. Each check targets a way these documents can
drift apart as they are edited incrementally. The checks are deliberately
mechanical -- anything needing judgment is reported as a prompt rather than a
failure, so the script stays trustworthy and does not cry wolf.
"""

import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
PLAN = HERE / "class_based_plugins.md"
RECON = HERE / "datatree_spec_reconciliation.md"
REVIEW_MAP = HERE / "TEMP_review_map.md"

problems: list[str] = []
prompts: list[str] = []


def fail(msg: str) -> None:
    problems.append(msg)


def ask(msg: str) -> None:
    prompts.append(msg)


def headings(text: str):
    """Yield (level, number, title, anchor) for every numbered heading."""
    fence = None
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            tok = stripped[:3]
            fence = None if fence == tok else (fence or tok)
            continue
        if fence:
            continue
        m = re.match(r"^(#{2,4}) (\d+(?:\.\d+)*)\. (.+)$", line.rstrip())
        if m:
            slug = f"{m.group(2)}. {m.group(3)}".lower()
            slug = re.sub(r"[`*]", "", slug)  # GitHub keeps "_" in anchors
            slug = re.sub(r"[^a-z0-9 _-]", "", slug).strip().replace(" ", "-")
            yield len(m.group(1)), m.group(2), m.group(3), slug


def section_of(text: str):
    """Map each line index to the number of the section containing it."""
    out, cur = [], ""
    for line in text.split("\n"):
        m = re.match(r"^#{2,4} (\d+(?:\.\d+)*)\. ", line)
        if m:
            cur = m.group(1)
        out.append(cur)
    return out


plan = PLAN.read_text()
recon = RECON.read_text() if RECON.exists() else ""
plan_lines = plan.split("\n")
plan_sec = section_of(plan)

plan_anchors = {h[3] for h in headings(plan)}
recon_anchors = {h[3] for h in headings(recon)}
plan_titles = {h[1]: h[2] for h in headings(plan)}


# 1. Numbering is sequential and properly nested ---------------------------
def check_numbering(text: str, name: str) -> None:
    counters = [0, 0, 0]
    for level, number, title, _ in headings(text):
        idx = level - 2
        counters[idx] += 1
        for j in range(idx + 1, 3):
            counters[j] = 0
        expected = ".".join(str(counters[k]) for k in range(idx + 1))
        if number != expected:
            fail(f"{name}: heading '{title}' numbered {number}, expected {expected}")


check_numbering(plan, "plan")
check_numbering(recon, "recon")


# 2. Links and anchors resolve ---------------------------------------------
# An anchor carries its section number, so renumbering silently breaks every link
# pointing at a moved heading -- inserting 5.4 turned every #19x link stale. The
# title half of an anchor survives renumbering, so a broken link whose title half
# still matches a heading can be repaired mechanically: run with --relink.
#
# Underscores are legal in an anchor (`depends_on`); omitting them from this
# character class does not fail those links, it skips them silently.
ANCHOR = r"[a-z0-9_-]+"


def title_key(anchor: str) -> str:
    """The anchor with its leading section number removed."""
    return re.sub(r"^\d+-", "", anchor)


plan_by_title = {title_key(a): a for a in plan_anchors}
recon_by_title = {title_key(a): a for a in recon_anchors}
repairs: list[tuple[str, str]] = []


def check_anchor(anchor: str, known: set, by_title: dict, prefix: str, label: str) -> None:
    if anchor in known:
        return
    fixed = by_title.get(title_key(anchor))
    if fixed is None:
        fail(f"plan: {label}#{anchor} does not resolve")
        return
    repairs.append((f"]({prefix}#{anchor})", f"]({prefix}#{fixed})"))
    fail(f"plan: {label}#{anchor} does not resolve; #{fixed} matches by title (--relink)")


for anchor in re.findall(rf"\]\(#({ANCHOR})\)", plan):
    check_anchor(anchor, plan_anchors, plan_by_title, "", "link to ")

for target, anchor in re.findall(rf"\]\(([a-z_]+\.md)#({ANCHOR})\)", plan):
    same = target == RECON.name
    check_anchor(anchor, recon_anchors if same else plan_anchors,
                 recon_by_title if same else plan_by_title,
                 target, f"cross-file link {target}")



# 2b. The review map addresses the plan by section number ------------------
# TEMP_review_map.md carries the section number twice per reference: in the link
# text (§12) and in the anchor (#12-...). Renumbering the plan invalidates both,
# and the stale label is the worse half -- a wrong number reads as correct, while
# a wrong anchor at least fails to jump. Repair the pair together.
map_repairs: list[tuple[str, str]] = []


def loose(key: str) -> str:
    """Title key without underscores, to match anchors written before the slug
    function stopped stripping them."""
    return key.replace("_", "")


if REVIEW_MAP.exists():
    rmap = REVIEW_MAP.read_text()
    anchor_number = {h[3]: h[1] for h in headings(plan)}
    loose_by_title = {loose(title_key(a)): a for a in plan_anchors}
    for label, anchor in re.findall(rf"\[§([\d.]+)\]\({PLAN.name}#({ANCHOR})\)", rmap):
        if anchor in plan_anchors and anchor_number.get(anchor) == label:
            continue
        fixed = (plan_by_title.get(title_key(anchor))
                 or loose_by_title.get(loose(title_key(anchor))))
        if fixed is None:
            fail(f"review map: link to #{anchor} does not resolve")
            continue
        old = f"[§{label}]({PLAN.name}#{anchor})"
        new = f"[§{anchor_number[fixed]}]({PLAN.name}#{fixed})"
        if old != new:
            map_repairs.append((old, new))
            fail(f"review map: §{label} should be §{anchor_number[fixed]} (--relink)")

if (repairs or map_repairs) and "--relink" in sys.argv:
    for path, text, fixes in ((PLAN, plan, repairs), (REVIEW_MAP, rmap, map_repairs)):
        if not fixes:
            continue
        for old, new in fixes:
            text = text.replace(old, new)
        path.write_text(text)
        print(f"relinked {len(fixes)} reference(s) in {path.name}")
    print("re-run to verify")
    sys.exit(0)

for target in set(re.findall(r"\]\(([a-z_]+\.md)[#)]", plan + recon)):
    if not (HERE / target).exists():
        fail(f"link to missing file: {target}")


# 3. Terminology: *Specification* convention -------------------------------
def check_specification_term(text: str, name: str) -> None:
    fence = None
    for i, line in enumerate(text.split("\n"), 1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            tok = stripped[:3]
            fence = None if fence == tok else (fence or tok)
            continue
        if fence or line.startswith("#"):
            continue
        bare = re.search(r"(?<![\w*`>-])specifications?(?![\w*`])", line)
        if bare and "specification work" not in line:
            fail(f"{name}:{i}: un-italicized 'specification' -- {line.strip()[:60]}")


check_specification_term(plan, "plan")
check_specification_term(recon, "recon")


# 4. Every deliverable has a Progress Tracker row --------------------------
tracker = ""
for level, number, title, _ in headings(plan):
    if "Progress Tracker" in title:
        start = plan.index(f"## {number}. {title}")
        rest = plan[start:]
        nxt = re.search(r"\n## \d", rest[3:])
        tracker = rest[: nxt.start()] if nxt else rest

if not tracker:
    fail("plan: no Progress Tracker section found")
else:
    expected_rows = {
        "reconciliation": RECON.name,
        "deprecation register": "deprecation register",
        "argument matrix": "canonical argument matrix",
        "coverage matrix": "interface inventory",
    }
    for key, label in expected_rows.items():
        if key not in tracker.lower():
            fail(f"Progress Tracker: no row for {label}")


# 5. Artifacts appear in the reference list --------------------------------
refs = ""
for level, number, title, _ in headings(plan):
    if "Planning References" in title:
        refs = plan[plan.index(f"## {number}. {title}") :]

if refs:
    if RECON.name not in refs:
        fail(f"Reference list: {RECON.name} is not listed")
    if "ISSUE_TEMPLATE" not in refs:
        fail("Reference list: the v2-spec-gap issue template is not listed")


# 6. Requirements in 6.1 have enforcement siblings -------------------------
def lines_in(prefix: str):
    return [
        plan_lines[i]
        for i in range(len(plan_lines))
        if plan_sec[i] == prefix or plan_sec[i].startswith(prefix + ".")
    ]


def section_text(prefix: str) -> str:
    return "\n".join(lines_in(prefix)).lower()


req_section = None
content_section = None
dod_section = None
for level, number, title, _ in headings(plan):
    if "Requirements For Specification Pages" in title:
        req_section = number
    if "Required Content" in title:
        content_section = number
    if "Definition of Done" in title:
        dod_section = number

if req_section and content_section and dod_section:
    questions = section_text(content_section)
    dod = section_text(dod_section)
    # Each 6.1 subsection, by its distinguishing keyword
    topics = {
        "CF Compliance": ["cf compliance", "cf convention", "cf divergence"],
        "Workflow Root and Dataset Nodes": ["coordinate-compatible"],
        "Step Classification": ["data-bearing"],
        "Dataset Identity": ["dataset identity", "scientific compat"],
        "Provenance and Retention": ["retention"],
        "Units": ["unit"],
        "Dimensions and Composition": ["dimension"],
    }
    # Topics that are deliberately not enforced per page. Metadata Requirements
    # allocates responsibility between the base page and interface pages -- it is a
    # rule about where content is documented, not content any single page carries.
    not_per_page = {"Metadata Requirements"}
    for topic, keys in topics.items():
        if topic in not_per_page:
            continue
        in_q = any(k in questions for k in keys)
        in_d = any(k in dod for k in keys)
        if not in_q and not in_d:
            fail(f"6.1 topic '{topic}' has no question and no Definition of Done check")
        elif not in_q:
            ask(f"6.1 topic '{topic}' has a Definition of Done check but no required question")
        elif not in_d:
            ask(f"6.1 topic '{topic}' has a required question but no Definition of Done check")


# 7. Phase 0 checkboxes vs decisions actually present ----------------------
phase0 = ""
for level, number, title, _ in headings(plan):
    if title.startswith("Phase 0"):
        start = plan.index(f"### {number}. {title}")
        rest = plan[start:]
        nxt = re.search(r"\n### \d", rest[4:])
        phase0 = rest[: nxt.start()] if nxt else rest

if phase0:
    # Search the document with the Phase 0 checklist removed. Several items quote
    # their own evidence ("geoips lint", "(label)="), so searching the whole
    # document matches an item against itself and reports every one of them.
    body = plan.replace(phase0, "").lower()
    # decision keyword -> checklist item keyword
    decided = {
        "kind-to-interface": "`kind` token does a workflow step",
        "family deprecation and the `data_tree`": "family/`data_tree` migration axis",
        "validation commands": "geoips lint",
        "myst style conventions": "(label)=",
        "ownership/audience boundaries": "where-to-put",
    }
    for item_key, evidence in decided.items():
        m = re.search(
            r"^- \[([ x])\][^\n]*" + re.escape(item_key), phase0, re.I | re.M
        )
        if m and m.group(1) == " " and evidence.lower() in body:
            ask(
                f"Phase 0 item '{item_key}' is unchecked, but the decision appears "
                f"present in the document"
            )


# 8. Terms defined before first use ----------------------------------------
for term, definition_marker in {
    "coordinate-compatible variable group": "A **coordinate-compatible variable group**",
}.items():
    first_use = plan.lower().find(term.lower())
    definition = plan.find(definition_marker)
    if definition == -1:
        fail(f"term '{term}' is used but never defined")
    elif first_use < definition:
        line = plan[:first_use].count("\n") + 1
        ask(f"term '{term}' first used at line {line}, before its definition")


# Report -------------------------------------------------------------------
if problems:
    print(f"FAIL ({len(problems)})")
    for p in problems:
        print(f"  - {p}")
if prompts:
    print(f"\nNEEDS JUDGMENT ({len(prompts)})")
    for p in prompts:
        print(f"  - {p}")
if not problems and not prompts:
    print("OK -- all checks pass")

sys.exit(1 if problems else 0)
