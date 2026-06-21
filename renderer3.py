from jinja2 import Environment, FileSystemLoader
import os

from template_chooser import choose_template, render_record


def render_page(
    data: dict,
    template_path: str = "template.html",
    output_dir: str = "site_output",
    strategy: str = "smart",
):
    """
    Render a Jinja2 HTML template with the given data dict.

    This function prefers to use the `template_chooser` to pick one of the
    generated templates (templates/template1.html ... templateN.html). If the
    `templates/` folder or templates are not present, it falls back to the
    original behaviour using the provided `template_path`.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Try to pick a template using the chooser (preferred path)
    try:
        chosen = choose_template(data, index=0, strategy=strategy)
    except FileNotFoundError:
        chosen = None

    if chosen:
        # Render using template_chooser.render_record for consistent context handling
        html = render_record(data, chosen)
        out_path = os.path.join(output_dir, "index.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"[OK] HTML generated -> {out_path}  (template: {chosen})")
        return output_dir

    # Fallback: load template directly (original behaviour)
    tmpl_dir = os.path.dirname(template_path) or "."
    tmpl_file = os.path.basename(template_path)

    env = Environment(loader=FileSystemLoader(tmpl_dir))
    template = env.get_template(tmpl_file)

    output = template.render(data=data)

    out_path = os.path.join(output_dir, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"[OK] HTML generated -> {out_path}  (template: {template_path})")
    return output_dir