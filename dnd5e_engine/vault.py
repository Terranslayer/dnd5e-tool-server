"""VaultService: create/read/list notes on a vault root directory.
Delegates path + (de)serialization to notes.py."""

from __future__ import annotations

from pathlib import Path

from dnd5e_engine import notes

DEFAULT_STYLE = "语气中性、清晰，贴合 DnD 5e 奇幻基调；无特殊禁忌。"


class VaultService:
    def __init__(self, root):
        self.root = Path(root)

    def create_note(self, note_type: str, name: str, frontmatter: dict | None = None,
                    body: str = "", campaign: str | None = None,
                    id: str | None = None, overwrite: bool = False) -> dict:
        rel = notes.note_path(note_type, name, campaign)
        dest = self.root / rel
        if dest.exists() and not overwrite:
            raise FileExistsError(f"note already exists: {rel} (use overwrite=True)")
        fm: dict = {"id": id or notes.new_id(), "type": note_type, "name": name}
        if campaign:
            fm["campaign"] = campaign
        if frontmatter:
            fm.update(frontmatter)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(notes.render_note(fm, body), encoding="utf-8")
        return {"path": rel, "id": fm["id"], "type": note_type, "created": True}

    def read_note(self, rel_path: str) -> dict:
        dest = (self.root / rel_path).resolve()
        if not dest.is_relative_to(self.root.resolve()):
            raise ValueError(f"path escapes vault root: {rel_path!r}")
        if not dest.exists():
            raise FileNotFoundError(rel_path)
        frontmatter, body = notes.parse_note(dest.read_text(encoding="utf-8"))
        return {"path": str(rel_path).replace("\\", "/"), "frontmatter": frontmatter, "body": body}

    def load_style(self, campaign: str) -> dict:
        """加载某战役的风格档案 style.md；命中返回 frontmatter+body，缺失返回中性缺省。"""
        rel = notes.note_path("style", "style", campaign=campaign)
        dest = self.root / rel
        if dest.exists():
            frontmatter, body = notes.parse_note(dest.read_text(encoding="utf-8"))
            return {"campaign": campaign, "found": True,
                    "frontmatter": frontmatter, "body": body}
        return {"campaign": campaign, "found": False,
                "frontmatter": {}, "body": DEFAULT_STYLE}

    def list_notes(self, note_type: str | None = None, campaign: str | None = None) -> list[dict]:
        if note_type is not None:
            spec = notes.NOTE_TYPES.get(note_type)
            if spec is None:
                raise ValueError(f"unknown note_type: {note_type!r}")
            if spec["campaign_scoped"]:
                if not campaign:
                    raise ValueError(f"note_type {note_type!r} requires a campaign")
                base = self.root / notes.CAMPAIGN_ROOT / notes.sanitize_filename(campaign)
                if spec["folder"]:
                    base = base / spec["folder"]
            else:
                base = self.root / spec["folder"]
        else:
            base = self.root
        results: list[dict] = []
        if base.exists():
            for path in sorted(base.rglob("*.md")):
                frontmatter, _ = notes.parse_note(path.read_text(encoding="utf-8"))
                results.append({
                    "path": str(path.relative_to(self.root)).replace("\\", "/"),
                    "name": frontmatter.get("name"),
                    "type": frontmatter.get("type"),
                })
        return results
