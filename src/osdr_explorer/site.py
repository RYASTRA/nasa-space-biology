"""Render the committed OSDR mirror into a static, faceted explorer site."""

import json
import shutil
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

DEFAULT_BASE_URL = "https://ryastra.github.io/nasa-space-biology"


def load_studies(data_dir: Path) -> list[dict[str, Any]]:
    """Load the normalized studies array from ``data_dir/studies.json``."""
    return json.loads((data_dir / "studies.json").read_text(encoding="utf-8"))


def make_env(templates_dir: Path) -> Environment:
    """Build a Jinja2 environment that autoescapes HTML/XML templates."""
    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def copy_tree(src: Path, dest: Path) -> None:
    """Replace ``dest`` with a fresh copy of the ``src`` directory tree."""
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def _write(path: Path, text: str) -> None:
    """Write text to path (creating parents), ensuring a trailing newline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def render_sitemap(env: Environment, studies: list[dict[str, Any]], base_url: str) -> str:
    """Render sitemap.xml listing the index and every study page."""
    template = env.get_template("sitemap.xml.j2")
    return template.render(studies=studies, base_url=base_url.rstrip("/"))


def render_study(env: Environment, study: dict[str, Any]) -> str:
    """Render one study's standalone page."""
    return env.get_template("study.html.j2").render(s=study)


def render_index(env: Environment, meta: dict[str, Any]) -> str:
    """Render the explorer index shell (app.js populates it at runtime)."""
    return env.get_template("index.html.j2").render(meta=meta)


def build_site(
    *,
    data_dir: Path,
    site_dir: Path,
    templates_dir: Path,
    assets_dir: Path,
    base_url: str = DEFAULT_BASE_URL,
) -> None:
    """Render the static explorer site from the committed mirror in ``data_dir``."""
    studies = load_studies(data_dir)
    meta = json.loads((data_dir / "meta.json").read_text(encoding="utf-8"))
    env = make_env(templates_dir)
    copy_tree(data_dir, site_dir / "data")
    copy_tree(assets_dir, site_dir / "assets")
    _write(site_dir / "sitemap.xml", render_sitemap(env, studies, base_url))
    for study in studies:
        accession = study["identity"]["accession"]
        _write(site_dir / "study" / f"{accession}.html", render_study(env, study))
    _write(site_dir / "index.html", render_index(env, meta))
