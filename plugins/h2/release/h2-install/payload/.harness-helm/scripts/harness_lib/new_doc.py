from __future__ import annotations

import argparse
import re

from . import paths
from .templates import CANONICAL_TEMPLATES, TEMPLATE_TARGETS
from .utils import now_kst, read_text, write_text


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9가-힣]+", "-", value.strip()).strip("-")
    return slug.lower() or "untitled"


def render_template_text(text: str, args: argparse.Namespace, dtype: str) -> str:
    today = now_kst().strftime("%Y%m%d")
    title = args.title or args.topic or args.feature or dtype
    topic = slugify(args.topic or title)
    feature = slugify(args.feature or topic)
    replacements = {
        "<TODO: feature title>": title,
        "<TODO: task summary>": title,
        "<TODO: 도메인 규칙 또는 용어 제목>": title,
        "<TODO: contract 또는 명세 제목>": title,
        "<TODO: 규칙 제목>": title,
        "<TODO: 재사용 가능한 교훈 제목>": title,
        "<TODO: 해결책 제목>": title,
        "<TODO: 운영 절차 제목>": title,
        "<TODO: 사고 제목>": title,
        "<TODO: 버전 또는 릴리스 이름>": title,
        "YYYYMMDD": today,
        "NNNN": args.number,
        "NNN": args.sequence,
        "<TODO: git username 또는 team id>": args.owner,
        "<TODO: domain owner username 또는 team id>": args.owner,
        "<TODO: spec owner username 또는 team id>": args.owner,
        "<TODO: convention owner username 또는 team id>": args.owner,
        "<TODO: learning owner username 또는 team id>": args.owner,
        "<TODO: operations owner username>": args.owner,
        "<TODO: incident commander username>": args.owner,
        "<TODO: release manager username>": args.owner,
    }
    rendered = text
    for old, new in replacements.items():
        rendered = rendered.replace(old, new)
    if dtype == "decision":
        rendered = rendered.replace("ADR-NNNN", f"ADR-{args.number}")
    rendered = set_frontmatter_field(rendered, "status", args.status)
    rendered = set_frontmatter_field(rendered, "owner", f'"{args.owner}"')
    if dtype == "decision":
        rendered = set_frontmatter_field(rendered, "id", f'"ADR-{args.number}"')
    return rendered


def set_frontmatter_field(text: str, key: str, value: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---", 4)
    if end == -1:
        return text
    raw_lines = text[4:end].splitlines()
    for index, line in enumerate(raw_lines):
        if re.match(rf"^{re.escape(key)}\s*:", line):
            raw_lines[index] = f"{key}: {value}"
            break
    else:
        raw_lines.append(f"{key}: {value}")
    return "---\n" + "\n".join(raw_lines) + text[end:]


def command_new_doc(args: argparse.Namespace) -> int:
    dtype = args.type
    template_name = CANONICAL_TEMPLATES[dtype]
    template_path = paths.DOCS / "_templates" / template_name
    if not template_path.exists():
        print(f"new-doc: missing template {template_path.relative_to(paths.ROOT)}")
        return 1
    topic = slugify(args.topic or args.title or args.feature or dtype)
    feature = slugify(args.feature or topic)
    target_template = args.target or TEMPLATE_TARGETS[dtype]
    target_rel = target_template.format(
        feature=feature,
        topic=topic,
        domain=args.domain,
        area=args.area,
        number=args.number,
        status=args.status,
    )
    try:
        target = paths.resolve_under_root(target_rel, paths.ROOT, "target")
    except ValueError as error:
        print(f"new-doc: {error}")
        return 1
    content = render_template_text(read_text(template_path), args, dtype)
    if args.dry_run:
        print(f"new-doc: would write {target.relative_to(paths.ROOT)}")
        return 0
    if target.exists() and not args.force:
        print(f"new-doc: target exists {target.relative_to(paths.ROOT)}; use --force to overwrite.")
        return 1
    write_text(target, content)
    print(f"new-doc: wrote {target.relative_to(paths.ROOT)}")
    return 0
