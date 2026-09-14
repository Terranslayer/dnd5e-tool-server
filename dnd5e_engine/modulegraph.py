"""模组依赖图校验（确定性，无嵌入）。读取某战役的全部笔记，用 notes.RELATION_FIELDS
把 [[wikilink]] 解析成边，报告：悬空链接、孤立场景、无来源线索。"""

from __future__ import annotations

from dnd5e_engine import notes


def validate(vault, campaign: str) -> dict:
    # 取该战役所有笔记（list_notes() 列出 vault 全部，再按 frontmatter.campaign 过滤）
    records: list[tuple[str, str, dict]] = []  # (type, name, frontmatter)
    for item in vault.list_notes():
        fm = vault.read_note(item["path"])["frontmatter"]
        if fm.get("campaign") != campaign:
            continue
        records.append((fm.get("type") or "", fm.get("name") or item.get("name") or "", fm))

    names = {name for _, name, _ in records if name}
    inbound: set[str] = set()
    issues: list[dict] = []

    for ntype, name, fm in records:
        for field in notes.RELATION_FIELDS.get(ntype, ()):
            for target in notes.parse_links(fm.get(field)):
                if target in names:
                    inbound.add(target)   # 只有真实存在的目标才算入边
                else:
                    issues.append({"type": "dangling_link", "note": name,
                                   "field": field, "target": target})

    for ntype, name, fm in records:
        if ntype == "scene" and name not in inbound:
            issues.append({"type": "unreachable_scene", "note": name, "target": None})
        if ntype == "clue" and not notes.parse_links(fm.get("revealed_by")):
            issues.append({"type": "clue_without_source", "note": name, "target": None})

    counts: dict[str, int] = {}
    for ntype, _, _ in records:
        counts[ntype] = counts.get(ntype, 0) + 1
    return {"campaign": campaign, "counts": counts, "issues": issues}
