"""FastMCP server `dnd5e-engine`: registers deterministic compute tools and
SRD lookup tools. Each tool returns a structured dict with breakdown/citation."""

from __future__ import annotations

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from dnd5e_engine import checks, config, dice, encounter, spellcasting  # noqa: F401  (config loads .env)
from dnd5e_engine.data import SRDData
from dnd5e_engine.lookup import LookupService
from dnd5e_engine.terms import TermMap
from dnd5e_engine.vault import VaultService

mcp = FastMCP("dnd5e-engine")

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_lookup_service: LookupService | None = None


def _service() -> LookupService:
    global _lookup_service
    if _lookup_service is None:
        srd = SRDData.load(_DATA_DIR / "srd_2014")
        terms = TermMap.load(_DATA_DIR / "term_map.json")
        _lookup_service = LookupService(srd, terms)
    return _lookup_service


def _vault() -> VaultService:
    root = os.environ.get("DND5E_VAULT") or str(_DATA_DIR.parent / "vault")
    return VaultService(root)


def _state():
    from dnd5e_engine.state import StateService
    root = os.environ.get("DND5E_VAULT") or str(_DATA_DIR.parent / "vault")
    return StateService(root)


_semantic_search_service = None


def _semantic():
    global _semantic_search_service
    if _semantic_search_service is None:
        from dnd5e_engine.embeddings import OpenAIEmbedder
        from dnd5e_engine.retrieval import SemanticSearch
        from dnd5e_engine.vectorstore import VectorStore
        store = VectorStore(_DATA_DIR / "vector_index")
        _semantic_search_service = SemanticSearch(OpenAIEmbedder(), store)
    return _semantic_search_service


# ---- pure compute tools ----

@mcp.tool()
def roll_dice(notation: str, advantage: bool = False, disadvantage: bool = False,
              crit: bool = False) -> dict:
    """掷骰。notation 如 '2d6+3'。advantage/disadvantage 仅对单个 d20 有效。
    返回统一结构：notation, rolls, natural, modifier, advantage, disadvantage, crit, total。
    natural 仅在单颗骰时为该骰点数，多颗骰时为 None。"""
    if advantage or disadvantage:
        count, sides, modifier = dice.parse(notation)
        if (count, sides) != (1, 20):
            raise ValueError("advantage/disadvantage only apply to a single d20")
        nat, rolls, total = dice.roll_d20(modifier, advantage, disadvantage)
        return {"notation": notation, "rolls": rolls, "natural": nat,
                "modifier": modifier, "advantage": advantage, "disadvantage": disadvantage,
                "crit": False, "total": total}
    r = dice.roll_notation(notation, crit=crit)
    natural = r.rolls[0] if len(r.rolls) == 1 else None
    return {"notation": notation, "rolls": r.rolls, "natural": natural,
            "modifier": r.modifier, "advantage": False, "disadvantage": False,
            "crit": crit, "total": r.total}


@mcp.tool()
def resolve_check(modifier: int, dc: int, proficiency_bonus: int = 0,
                  advantage: bool = False, disadvantage: bool = False) -> dict:
    """解析属性/技能/豁免检定（d20 + 调整值 vs DC）。检定时 nat20/nat1 不自动成败。"""
    return checks.resolve_check(modifier, dc, proficiency_bonus, advantage, disadvantage)


@mcp.tool()
def resolve_attack(attack_bonus: int, target_ac: int,
                   advantage: bool = False, disadvantage: bool = False) -> dict:
    """解析攻击骰。nat20 必中且暴击，nat1 必失。"""
    return checks.resolve_attack(attack_bonus, target_ac, advantage, disadvantage)


@mcp.tool()
def roll_damage(dice_notation: str, modifier: int = 0, crit: bool = False) -> dict:
    """掷伤害。暴击只翻倍骰子数、调整值只加一次。"""
    return checks.roll_damage(dice_notation, modifier=modifier, crit=crit)


@mcp.tool()
def cr_to_xp(cr: str) -> dict:
    """挑战等级转经验值（接受 '1/4'、'5' 等）。"""
    return {"cr": cr, "xp": encounter.cr_to_xp(cr)}


@mcp.tool()
def encounter_budget(party_levels: list[int], difficulty: str = "medium") -> dict:
    """按队伍各角色等级求某难度的 XP 预算（2014）。"""
    return encounter.encounter_budget(party_levels, difficulty)


@mcp.tool()
def evaluate_encounter(party_levels: list[int], monsters: list[dict], ruleset: str = "2014") -> dict:
    """评估遭遇难度（2014：含遭遇乘数 + 队伍人数偏移）。monsters: [{'cr'|'xp', 'count'}]。"""
    return encounter.evaluate_encounter(party_levels, monsters, ruleset)


@mcp.tool()
def spell_save_dc(ability_mod: int, proficiency_bonus: int) -> dict:
    """法术豁免 DC = 8 + 熟练 + 属性调整。"""
    return {"spell_save_dc": spellcasting.spell_save_dc(ability_mod, proficiency_bonus)}


@mcp.tool()
def spell_attack_bonus(ability_mod: int, proficiency_bonus: int) -> dict:
    """法术攻击加值 = 熟练 + 属性调整。"""
    return {"spell_attack_bonus": spellcasting.spell_attack_bonus(ability_mod, proficiency_bonus)}


# ---- read-only SRD lookup tools ----

@mcp.tool()
def lookup_monster(query: str) -> dict:
    """按名字（中/英）或 slug 查 SRD 怪物，返回数据 + 中文名 + 来源引用。"""
    return _service().lookup_monster(query)


@mcp.tool()
def lookup_spell(query: str) -> dict:
    """按名字（中/英）或 slug 查 SRD 法术，返回数据 + 中文名 + 来源引用。"""
    return _service().lookup_spell(query)


@mcp.tool()
def lookup_condition(query: str) -> dict:
    """按名字（中/英）或 slug 查 SRD 状态，返回数据 + 中文名 + 来源引用。"""
    return _service().lookup_condition(query)


@mcp.tool()
def lookup_rule(query: str) -> dict:
    """关键词检索 SRD 规则条目；查不到则明确返回 found=false，绝不编造。"""
    return _service().lookup_rule(query)


@mcp.tool()
def translate_term(term: str, direction: str = "en2zh") -> dict:
    """中英术语映射（en2zh / zh2en）。"""
    return _service().translate_term(term, direction)


@mcp.tool()
def monsters_by_cr(min_cr: str, max_cr: str | None = None) -> dict:
    """列出某 CR（或 CR 区间 min..max）的 SRD 怪物，供按遭遇预算选合法怪物。
    接受 '1/4'、'5' 等。返回 {count, monsters:[{index,name_en,name_zh,cr}], citation}。"""
    return _service().monsters_by_cr(min_cr, max_cr)


@mcp.tool()
def semantic_search(query: str, k: int = 5, campaign: str = "", ruleset: str = "") -> dict:
    """对 SRD 叙事 + 已索引模组散文做语义检索，返回带出处的片段。
    campaign/ruleset 为空=不限（含共享规则）；给定 campaign 时只召回该战役+共享规则，避免串味。
    精确数值仍用 lookup_* 工具。需已建索引（scripts/build_index.py / index_module）。"""
    return _semantic().search(query, k, campaign=campaign or None, ruleset=ruleset or None)


@mcp.tool()
def index_module(text: str, campaign: str, source: str, license: str,
                 note_id: str = "", ruleset: str = "dnd5e-2014") -> dict:
    """把一段模组散文切块嵌入并追加进向量库（带 campaign/source/license/note_id 元数据），
    使其可经 semantic_search 按战役召回。需已配置 OpenAI key。返回 {count}。"""
    return _semantic().index_text(text, campaign=campaign, source=source,
                                  license=license, note_id=note_id, ruleset=ruleset)


@mcp.tool()
def validate_module_graph(campaign: str) -> dict:
    """确定性校验某战役模组依赖图：孤立场景(unreachable_scene)/无来源线索(clue_without_source)/
    悬空链接(dangling_link)。返回 {campaign, counts, issues}。"""
    from dnd5e_engine import modulegraph
    return modulegraph.validate(_vault(), campaign)


# ---- vault asset tools ----

@mcp.tool()
def create_note(note_type: str, name: str, frontmatter: dict | None = None,
                body: str = "", campaign: str | None = None,
                overwrite: bool = False) -> dict:
    """创建一条 vault 笔记（YAML frontmatter + 正文）。note_type 见 NOTE_TYPES
    （npc/location/faction/monster/character/encounter/quest/session/campaign_state/
    campaign/scene/clue/map）；campaign-scoped 类型需传 campaign。自动写入 id/type/name。
    overwrite=True 时覆盖同名笔记（用于模组解析等可续/幂等重跑）。"""
    return _vault().create_note(note_type, name, frontmatter=frontmatter,
                                body=body, campaign=campaign, overwrite=overwrite)


@mcp.tool()
def read_note(path: str) -> dict:
    """读取 vault 笔记，返回 {path, frontmatter, body}。"""
    return _vault().read_note(path)


@mcp.tool()
def list_notes(note_type: str | None = None, campaign: str | None = None) -> dict:
    """列出 vault 笔记（可按 note_type / campaign 过滤），返回 {notes:[{path,name,type}]}。"""
    return {"notes": _vault().list_notes(note_type=note_type, campaign=campaign)}


@mcp.tool()
def load_style(campaign: str) -> dict:
    """加载某战役的风格档案（系统提示片段/语气样例/禁忌）；缺失则返回中性缺省。
    备团/解析/带团前调用，使产出贴合该团语气。返回 {campaign, found, frontmatter, body}。"""
    return _vault().load_style(campaign)


# ---- state-write tools (Phase 2-A; 写人类可审计的实例层 frontmatter) ----

@mcp.tool()
def start_encounter(campaign: str, name: str, combatants: list[dict],
                    variant: str = "main", terrain: str = "", summary: str = "") -> dict:
    """开一场运行态遭遇（落在 variants/<variant>/，不动模板）。combatants 每项含
    name/side/initiative/ac/hp{value,max,temp?}；自动补 id、按先攻降序、round=1/turn_index=0。"""
    return _state().start_encounter(campaign, name, combatants, variant=variant,
                                    terrain=terrain, summary=summary)


@mcp.tool()
def apply_hp_change(campaign: str, encounter: str, combatant_id: str, delta: int,
                    variant: str = "main") -> dict:
    """改某 combatant 的 HP（delta<0 伤害：临时HP先抵、夹到0；delta>0 治疗：不超 max）。
    到 0 标 status=down。返回新 hp + status。"""
    return _state().apply_hp_change(campaign, encounter, combatant_id, delta, variant=variant)


@mcp.tool()
def manage_combat_state(campaign: str, encounter: str, variant: str = "main",
                        advance_turn: bool = False, combatant_id: str = "",
                        set_conditions: list[str] | None = None,
                        clear_conditions: list[str] | None = None,
                        spell_slots: dict | None = None) -> dict:
    """推先攻游标（advance_turn：越界则 round+1、归零）/ 给 combatant 设清 conditions / 设 spell_slots。
    返回 {round, turn_index, active_combatant, changed}。"""
    return _state().manage_combat_state(
        campaign, encounter, variant=variant, advance_turn=advance_turn,
        combatant_id=combatant_id, set_conditions=set_conditions,
        clear_conditions=clear_conditions, spell_slots=spell_slots)


@mcp.tool()
def update_campaign_state(campaign: str, variant: str = "main",
                          patch: dict | None = None) -> dict:
    """合并 patch 进运行态 state.md（current/clocks/quests/world_flags 等）；首次自动建。
    world_flags 增量合并（不清旧旗标），其它 key 整体替换。返回合并后状态。"""
    return _state().update_campaign_state(campaign, variant=variant, patch=patch)


@mcp.tool()
def load_play_context(campaign: str, variant: str = "main") -> dict:
    """开局/续团一次性载入某战役实例：当前状态(state.md)、风格档案、活动遭遇概要。
    返回 {campaign, variant, state, style, active_encounters}。solo-dm 带团入口。"""
    return _state().load_play_context(campaign, variant=variant)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
