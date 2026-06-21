"""
template_chooser.py
Loads dataset.json, picks an appropriate template for each record,
renders it with Jinja2, and saves output to rendered_templates/.

Usage
-----
# Render all records (smart strategy):
    python template_chooser.py

# Render a single record by index:
    python template_chooser.py --index 5

# Render first N records:
    python template_chooser.py --count 10

# Use random template selection:
    python template_chooser.py --strategy random

# Use index-based (sequential) template selection:
    python template_chooser.py --strategy index

# Specify custom dataset or output directory:
    python template_chooser.py --dataset my_data.json --output my_output/
"""

import argparse
import json
import os
import random
import sys
from typing import Optional, Union

from jinja2 import Environment, FileSystemLoader, select_autoescape

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TEMPLATES_DIR = "templates"
DATASET_PATH = "dataset.json"
OUTPUT_DIR = "rendered_templates"
TOTAL_TEMPLATES = 100

# ── Style / colour → template group overrides ──────────────────────────────
# If the user expresses a colour theme or design style, these mappings can
# override (or fine-tune) the business-type group so the chosen template
# better matches the user's visual preference.
STYLE_OVERRIDES: dict[str, tuple[int, int]] = {
    # Dark / moody palettes → food/amber group
    "dark":         (1, 20),
    "black":        (1, 20),
    "warm":         (1, 20),
    "amber":        (1, 20),
    "earthy":       (1, 20),
    "brown":        (1, 20),
    # Clean / minimal → fitness/wellness group
    "white":        (21, 40),
    "minimal":      (21, 40),
    "clean":        (21, 40),
    "light":        (21, 40),
    "pastel":       (21, 40),
    # Vibrant / neon / bold → tech group
    "neon":         (41, 60),
    "vibrant":      (41, 60),
    "colourful":    (41, 60),
    "colorful":     (41, 60),
    "bright":       (41, 60),
    "bold":         (41, 60),
    "gradient":     (41, 60),
    "purple":       (41, 60),
    "blue":         (41, 60),
    "electric":     (41, 60),
    # Card-grid / feminine → retail/beauty group
    "pink":         (61, 80),
    "rose":         (61, 80),
    "gold":         (61, 80),
    "luxury":       (61, 80),
    "feminine":     (61, 80),
    "elegant":      (61, 80),
    # Editorial / professional → professional group
    "professional": (81, 100),
    "corporate":    (81, 100),
    "editorial":    (81, 100),
    "modern":       (81, 100),
    "green":        (81, 100),
    "teal":         (81, 100),
    "navy":         (81, 100),
}

# Business-type keyword → template group (1-indexed ranges)
KEYWORD_GROUPS: dict[str, tuple[int, int]] = {
    # food & beverage → Group A (1–20): dark warm/amber
    "bakery":     (1, 20),
    "cafe":       (1, 20),
    "restaurant": (1, 20),
    "food":       (1, 20),
    "sweet":      (1, 20),
    "juice":      (1, 20),
    "hotel":      (1, 20),
    "takeaway":   (1, 20),
    "ice cream":  (1, 20),
    "tiffin":     (1, 20),
    "tea":        (1, 20),
    "coffee":     (1, 20),
    # fitness & wellness → Group B (21–40): minimal clean white
    "gym":        (21, 40),
    "fitness":    (21, 40),
    "yoga":       (21, 40),
    "health":     (21, 40),
    "nutritionist": (21, 40),
    "spa":        (21, 40),
    "wellness":   (21, 40),
    "martial":    (21, 40),
    "sports":     (21, 40),
    "dance":      (21, 40),
    "dentist":    (21, 40),
    "dental":     (21, 40),
    "clinic":     (21, 40),
    "pharmacy":   (21, 40),
    "optician":   (21, 40),
    "veterinary": (21, 40),
    # tech & digital → Group C (41–60): vibrant neon
    "tech":       (41, 60),
    "it ":        (41, 60),
    "software":   (41, 60),
    "startup":    (41, 60),
    "digital":    (41, 60),
    "web":        (41, 60),
    "developer":  (41, 60),
    "design":     (41, 60),
    "media":      (41, 60),
    "agency":     (41, 60),
    "content":    (41, 60),
    "editor":     (41, 60),
    "youtuber":   (41, 60),
    "data":       (41, 60),
    "ai ":        (41, 60),
    # retail & beauty → Group D (61–80): card-grid bold
    "salon":      (61, 80),
    "boutique":   (61, 80),
    "jewellery":  (61, 80),
    "jewelry":    (61, 80),
    "clothing":   (61, 80),
    "fashion":    (61, 80),
    "gift":       (61, 80),
    "flower":     (61, 80),
    "pet":        (61, 80),
    "furniture":  (61, 80),
    "electronics":(61, 80),
    "mobile":     (61, 80),
    "book":       (61, 80),
    "music store":(61, 80),
    "instrument": (61, 80),
    "toy":        (61, 80),
    "grocery":    (61, 80),
    "fruit":      (61, 80),
    "hardware":   (61, 80),
    "print":      (61, 80),
    # professional & other → Group E (81–100): editorial
    "law":        (81, 100),
    "accountan":  (81, 100),
    "finance":    (81, 100),
    "architect":  (81, 100),
    "interior":   (81, 100),
    "travel":     (81, 100),
    "resort":     (81, 100),
    "event":      (81, 100),
    "school":     (81, 100),
    "tuition":    (81, 100),
    "coaching":   (81, 100),
    "language":   (81, 100),
    "music class":(81, 100),
    "photography":(81, 100),
    "studio":     (81, 100),
    "tattoo":     (81, 100),
    "laundry":    (81, 100),
    "tailoring":  (81, 100),
    "car":        (81, 100),
    "recruitment":(81, 100),
    "security":   (81, 100),
    "library":    (81, 100),
    "nursery":    (81, 100),
    "landscaping":(81, 100),
    "farm":       (81, 100),
    "pottery":    (81, 100),
    "antique":    (81, 100),
    "life coach": (81, 100),
}

DEFAULT_GROUP = (81, 100)  # fallback for unrecognized business types


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def load_dataset(path: str = DATASET_PATH) -> list[dict]:
    """Load and return all records from the dataset JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset not found: {path!r}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("dataset.json must be a JSON array of records.")
    return data


def _get_ground_truth(record: dict) -> dict:
    """Extract ground_truth fields from a record, with safe defaults."""
    gt = record.get("ground_truth", record)  # fallback to root if no ground_truth key
    return {
        "business_name": gt.get("business_name", "Business Name"),
        "business_type": gt.get("business_type", "Business"),
        "services":      gt.get("services", []),
        "city":          gt.get("city", ""),
        "email":         gt.get("email", ""),
        "phone":         gt.get("phone", ""),
        "color_theme":   gt.get("color_theme", ""),
        "design_style":  gt.get("design_style", ""),
        "conversation":  record.get("conversation", ""),
    }


def choose_template(
    record: dict,
    index: int = 0,
    strategy: str = "smart",
) -> str:
    """
    Choose a template filename for the given record.

    Parameters
    ----------
    record   : one entry from dataset.json
    index    : positional index of the record in the dataset
    strategy : "smart" | "random" | "index"

    Returns
    -------
    Relative path to the chosen template, e.g. "templates/template42.html"
    """
    if not os.path.isdir(TEMPLATES_DIR):
        raise FileNotFoundError(
            f"Templates directory '{TEMPLATES_DIR}' not found. "
            "Run generate_templates.py first."
        )

    if strategy == "random":
        n = random.randint(1, TOTAL_TEMPLATES)

    elif strategy == "index":
        n = (index % TOTAL_TEMPLATES) + 1

    else:  # smart (default)
        gt = _get_ground_truth(record)
        btype = gt["business_type"].lower()

        # Step 1: resolve group from business type
        lo, hi = DEFAULT_GROUP
        for keyword, (klo, khi) in KEYWORD_GROUPS.items():
            if keyword in btype:
                lo, hi = klo, khi
                break

        # Step 2: optionally override with captured style/colour preference
        color_theme  = str(record.get("color_theme",  "") or "").lower()
        design_style = str(record.get("design_style", "") or "").lower()
        style_hint   = f"{color_theme} {design_style}".strip()

        if style_hint:
            for style_kw, (slo, shi) in STYLE_OVERRIDES.items():
                if style_kw in style_hint:
                    lo, hi = slo, shi
                    break  # first matching style keyword wins

        # Pick consistently within the group using the record index
        group_size = hi - lo + 1
        n = lo + (index % group_size)

    template_name = f"template{n}.html"
    template_path = os.path.join(TEMPLATES_DIR, template_name)

    if not os.path.exists(template_path):
        raise FileNotFoundError(
            f"Template not found: {template_path!r}. "
            "Run generate_templates.py first."
        )

    return template_path


def render_record(record: dict, template_path: str) -> str:
    """
    Render a single dataset record using the given template.

    Parameters
    ----------
    record        : one entry from dataset.json
    template_path : relative path returned by choose_template()

    Returns
    -------
    Rendered HTML string
    """
    gt = _get_ground_truth(record)

    # Jinja2 environment — load from templates/ folder
    template_dir = os.path.dirname(template_path)
    template_file = os.path.basename(template_path)

    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html"]),
    )
    tmpl = env.get_template(template_file)

    # Merge ground truth values with all keys in the record to pass detailed JSON properties
    context = {}
    context.update(gt)
    context.update(record)

    return tmpl.render(**context)


def run(
    dataset_path: str = DATASET_PATH,
    output_dir: str = OUTPUT_DIR,
    index: Optional[int] = None,
    count: Optional[int] = None,
    strategy: str = "smart",
) -> list[str]:
    """
    Main entry point — renders records and saves HTML files.

    Parameters
    ----------
    dataset_path : path to dataset.json
    output_dir   : folder to write rendered HTML files
    index        : if given, render only this record index
    count        : if given, render only the first N records
    strategy     : template selection strategy ("smart" | "random" | "index")

    Returns
    -------
    List of output file paths written
    """
    dataset = load_dataset(dataset_path)
    os.makedirs(output_dir, exist_ok=True)

    if index is not None:
        if index < 0 or index >= len(dataset):
            raise IndexError(
                f"Index {index} out of range (dataset has {len(dataset)} records)."
            )
        records_to_process = [(index, dataset[index])]
    else:
        records_to_process = list(enumerate(dataset))
        if count is not None:
            records_to_process = records_to_process[:count]

    output_files = []
    for i, record in records_to_process:
        template_path = choose_template(record, index=i, strategy=strategy)
        html = render_record(record, template_path)

        gt = _get_ground_truth(record)
        bname = gt["business_name"].lower().replace(" ", "_")
        # Sanitize filename
        safe_bname = "".join(c if c.isalnum() or c == "_" else "" for c in bname)
        out_name = f"record_{i:04d}_{safe_bname}.html"
        out_path = os.path.join(output_dir, out_name)

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)

        tmpl_used = os.path.basename(template_path)
        print(f"  [{i:04d}] {gt['business_name']!r:30s} -> {tmpl_used:<20s} -> {out_path}")
        output_files.append(out_path)

    print(f"\n[OK] Rendered {len(output_files)} file(s) -> '{output_dir}/'")
    return output_files



# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Choose a template and render a dataset record to HTML.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--dataset",  default=DATASET_PATH,
                        help=f"Path to dataset JSON file (default: {DATASET_PATH})")
    parser.add_argument("--output",   default=OUTPUT_DIR,
                        help=f"Output directory (default: {OUTPUT_DIR})")
    parser.add_argument("--index",    type=int, default=None,
                        help="Render a single record by its 0-based index")
    parser.add_argument("--count",    type=int, default=None,
                        help="Render only the first N records")
    parser.add_argument("--strategy", choices=["smart", "random", "index"],
                        default="smart",
                        help="Template selection strategy (default: smart)")

    args = parser.parse_args()

    print(f"[dataset]  {args.dataset}")
    print(f"[output]   {args.output}")
    print(f"[strategy] {args.strategy}")
    if args.index is not None:
        print(f"[index]    {args.index}")
    elif args.count is not None:
        print(f"[count]    {args.count}")
    else:
        print("[records]  ALL")
    print()

    run(
        dataset_path=args.dataset,
        output_dir=args.output,
        index=args.index,
        count=args.count,
        strategy=args.strategy,
    )


if __name__ == "__main__":
    main()
