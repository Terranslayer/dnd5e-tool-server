"""Note model for the Obsidian vault: a type registry, path derivation, and
YAML-frontmatter render/parse. Pure functions — no filesystem access here.

Conventions (spec §7): frontmatter keys are ASCII; values may be Chinese; every
note carries a stable `id`; filenames are the cleaned display name (Chinese kept,
path-illegal chars removed)."""

from __future__ import annotations

import re
import uuid

import yaml

CAMPAIGN_ROOT = "04_Campaign_战役"

# note_type -> {folder, campaign_scoped}. Campaign-scoped notes live under
# CAMPAIGN_ROOT/<campaign>/<folder>/ (folder "" puts them at the campaign root).
NOTE_TYPES: dict[str, dict] = {
    "npc":            {"folder": "03_NPCs_角色", "campaign_scoped": False},
    "location":       {"folder": "02_World_世界/Locations_地点", "campaign_scoped": False},
    "faction":        {"folder": "02_World_世界/Factions_阵营", "campaign_scoped": False},
    "monster":        {"folder": "01_Rules_规则/Bestiary_怪物", "campaign_scoped": False},
    "character":      {"folder": "Characters_角色", "campaign_scoped": True},
    "encounter":      {"folder": "Encounters_遭遇", "campaign_scoped": True},
    "quest":          {"folder": "Quests_任务", "campaign_scoped": True},
    "session":        {"folder": "Sessions_分章", "campaign_scoped": True},
    "campaign_state": {"folder": "", "campaign_scoped": True},
    "campaign":       {"folder": "", "campaign_scoped": True},
    "scene":          {"folder": "Scenes_场景", "campaign_scoped": True},
    "clue":           {"folder": "Clues_线索", "campaign_scoped": True},
    "map":            {"folder": "Maps_地图", "campaign_scoped": True},
    "style":          {"folder": "", "campaign_scoped": True},
}

_ILLEGAL = re.compile(r'[\\/:*?"<>|]+')

# note_type -> frontmatter 键，其值为指向其它笔记的 [[wikilink]]（依赖图的边）。
RELATION_FIELDS: dict[str, tuple[str, ...]] = {
    "campaign": ("scenes", "exits"),
    "scene": ("location", "npcs", "encounters", "clues", "exits"),
    "clue": ("revealed_by", "unlocks"),
    "encounter": ("location", "monsters", "scene"),
    "npc": ("faction", "location"),
    "map": ("location", "scenes"),
}

_WIKILINK = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")


def parse_links(value) -> list[str]:
    """从一个 frontmatter 值（字符串或字符串列表）抽出链接目标名。
    识别 [[名称]] 与 [[名称|别名]]；无方括号的裸字符串按整体当作一个目标名。"""
    if value is None:
        return []
    items = value if isinstance(value, list) else [value]
    out: list[str] = []
    for item in items:
        s = str(item).strip()
        if not s:
            continue
        matches = _WIKILINK.findall(s)
        if matches:
            out.extend(m.strip() for m in matches)
        else:
            out.append(s)
    return out


def sanitize_filename(name: str) -> str:
    """Make a filesystem-safe filename, keeping Unicode (e.g. Chinese)."""
    cleaned = _ILLEGAL.sub("-", name).strip(" .-")
    if not cleaned:
        raise ValueError(f"name produces an empty filename: {name!r}")
    return cleaned


def new_id() -> str:
    return uuid.uuid4().hex


def note_path(note_type: str, name: str, campaign: str | None = None) -> str:
    """Vault-relative path (forward slashes) for a note of this type."""
    if note_type not in NOTE_TYPES:
        raise ValueError(f"unknown note_type: {note_type!r}")
    spec = NOTE_TYPES[note_type]
    filename = sanitize_filename(name) + ".md"
    if spec["campaign_scoped"]:
        if not campaign:
            raise ValueError(f"note_type {note_type!r} requires a campaign")
        parts = [CAMPAIGN_ROOT, sanitize_filename(campaign)]
        if spec["folder"]:
            parts.append(spec["folder"])
        parts.append(filename)
        return "/".join(parts)
    return f"{spec['folder']}/{filename}"


def render_note(frontmatter: dict, body: str = "") -> str:
    """Render a note as YAML frontmatter + markdown body."""
    fm = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).strip()
    body = body.strip()
    if body:
        return f"---\n{fm}\n---\n\n{body}\n"
    return f"---\n{fm}\n---\n"


def parse_note(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter + body. Returns ({}, text) if no frontmatter."""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            frontmatter = yaml.safe_load(parts[1]) or {}
            return frontmatter, parts[2].strip()
    return {}, text.strip()
