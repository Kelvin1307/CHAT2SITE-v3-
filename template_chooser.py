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
TOTAL_TEMPLATES = 20

# ── Style / colour → template group overrides ──────────────────────────────
# If the user expresses a colour theme or design style, these mappings can
# override (or fine-tune) the business-type group so the chosen template
# better matches the user's visual preference.
STYLE_OVERRIDES: dict[str, tuple[int, int]] = {
    "blue":         (1, 1),
    "red":          (2, 2),
    "green":        (3, 3),
    "pink":         (4, 4),
    "orange":       (5, 5),
    "violet":       (6, 6),
    "teal":         (7, 7),
    "indigo":       (8, 8),
    "cyan":         (9, 9),
    "lime":         (10, 10),
    "amber":        (11, 11),
    "magenta":      (12, 12),
    "emerald":      (13, 13),
    "slate":        (14, 14),
    "coral":        (15, 15),
    "navy":         (16, 16),
    "purple":       (17, 17),
    "gold":         (18, 18),
    "rose":         (19, 19),
    "black":        (20, 20),
    # Style keywords
    "dark":         (20, 20),
    "white":        (14, 14),
    "minimal":      (20, 20),
    "clean":        (14, 14),
    "light":        (14, 14),
    "pastel":       (4, 4),
    "neon":         (9, 9),
    "vibrant":      (9, 9),
    "colorful":     (17, 17),
    "bright":       (9, 9),
    "bold":         (2, 2),
    "gradient":     (1, 1),
    "luxury":       (6, 6),
    "elegant":      (18, 18),
    "professional": (8, 8),
    "corporate":    (16, 16),
    "editorial":    (14, 14),
    "modern":       (1, 1),
}

# Business-type keyword → template group (1-indexed ranges)
KEYWORD_GROUPS: dict[str, tuple[int, int]] = {
    # Group 1: Blue - SaaS/Tech
    "tech":         (1, 1),
    "software":     (1, 1),
    "startup":      (1, 1),
    "ai ":          (1, 1),
    "it ":          (1, 1),
    # Group 2: Red - Bold Agency
    "agency":       (2, 2),
    "media":        (2, 2),
    "creative":     (2, 2),
    "design":       (2, 2),
    "studio":       (2, 2),
    # Group 3: Green - Eco/Health
    "health":       (3, 3),
    "nutritionist": (3, 3),
    "organic":      (3, 3),
    "eco":          (3, 3),
    # Group 4: Pink - Beauty/Salon
    "salon":        (4, 4),
    "beauty":       (4, 4),
    "fashion":      (4, 4),
    "boutique":     (4, 4),
    "clothing":     (4, 4),
    # Group 5: Orange - Restaurant
    "restaurant":   (5, 5),
    "food":         (5, 5),
    "cafe":         (5, 5),
    "takeaway":     (5, 5),
    # Group 6: Violet - Luxury Brand
    "luxury":       (6, 6),
    "hotel":        (6, 6),
    # Group 7: Teal - Clinic/Spa
    "spa":          (7, 7),
    "wellness":     (7, 7),
    "clinic":       (7, 7),
    "dentist":      (7, 7),
    "dental":       (7, 7),
    "pharmacy":     (7, 7),
    # Group 8: Indigo - Consulting
    "consulting":   (8, 8),
    "coaching":     (8, 8),
    "advisor":      (8, 8),
    # Group 9: Cyan - Digital/Web
    "web":          (9, 9),
    "digital":      (9, 9),
    "developer":    (9, 9),
    # Group 10: Lime - Gym/Fitness
    "gym":          (10, 10),
    "fitness":      (10, 10),
    "sports":       (10, 10),
    "martial":      (10, 10),
    "dance":        (10, 10),
    # Group 11: Amber - Bakery/Coffee
    "bakery":       (11, 11),
    "coffee":       (11, 11),
    "tea":          (11, 11),
    "sweet":        (11, 11),
    # Group 12: Magenta - Events
    "event":        (12, 12),
    "entertainment":(12, 12),
    "music store":  (12, 12),
    # Group 13: Emerald - Finance/Law
    "law":          (13, 13),
    "attorney":     (13, 13),
    "legal":        (13, 13),
    "accountan":    (13, 13),
    "finance":      (13, 13),
    # Group 14: Slate - Architecture
    "architect":    (14, 14),
    "interior":     (14, 14),
    # Group 15: Coral - Travel
    "travel":       (15, 15),
    "resort":       (15, 15),
    # Group 16: Navy - Corporate
    "corporate":    (16, 16),
    "enterprise":   (16, 16),
    "recruitment":  (16, 16),
    "security":     (16, 16),
    # Group 17: Purple - Creative/Music
    "music class":  (17, 17),
    "photography":  (17, 17),
    "youtuber":     (17, 17),
    "content":      (17, 17),
    # Group 18: Gold - Jewelry/Retail
    "jewellery":    (18, 18),
    "jewelry":      (18, 18),
    "antique":      (18, 18),
    "watch":        (18, 18),
    # Group 19: Rose - Floral/Gifting
    "flower":       (19, 19),
    "gift":         (19, 19),
    "wedding":      (19, 19),
    "nursery":      (19, 19),
    # Group 20: Black - Fallback/Minimal
    "life coach":   (20, 20),
    "tattoo":       (20, 20),
    "laundry":      (20, 20),
}

DEFAULT_GROUP = (20, 20)  # fallback for unrecognized business types


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
    Relative path to the chosen template, e.g. "templates/template42/index.html"
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

    template_path = os.path.join(TEMPLATES_DIR, f"template{n}", "index.html")

    if not os.path.exists(template_path):
        raise FileNotFoundError(
            f"Template not found: {template_path!r}. "
            "Please run generate_templates.py or check folder content."
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

    # Inject safe defaults for nested dict structures to avoid Jinja UndefinedError
    defaults = {
        "brand": {"name": context.get("business_name", "Business Name"), "tagline": ""},
        "hero": {
            "title": context.get("business_name", "Business Name"),
            "subtitle": f"Serving {context.get('city', 'your area')} with pride.",
            "subtitle_short": "Excellence Defined",
            "cta": {"text": "Get Started", "link": "#contact"}
        },
        "about": {
            "title": "Why Choose Us",
            "description": f"We are a leading provider in {context.get('city', 'your area')}.",
            "features": ["Exceptional Quality", "Professional Team", "Proven Track Record"]
        },
        "footer": {
            "about": f"Leading {context.get('business_type', 'business')} in {context.get('city', 'your area')}.",
            "social": []
        }
    }
    for key, val in defaults.items():
        if key not in context or not isinstance(context[key], dict):
            context[key] = val
        else:
            merged = val.copy()
            merged.update(context[key])
            context[key] = merged

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

        # Copy styles.css and script.js from the chosen template directory
        import shutil
        template_dir = os.path.dirname(template_path)
        for asset in ["styles.css", "script.js"]:
            src = os.path.join(template_dir, asset)
            dst = os.path.join(output_dir, asset)
            if os.path.exists(src):
                shutil.copy2(src, dst)

        tmpl_used = os.path.basename(os.path.dirname(template_path))
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
