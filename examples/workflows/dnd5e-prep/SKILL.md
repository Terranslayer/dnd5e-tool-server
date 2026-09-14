---
name: dnd5e-prep
description: Use when preparing or authoring DnD 5e content for a campaign — generating NPCs, encounters, plot hooks, locations, or factions and saving them into the Obsidian vault. Generates SRD-legal or clearly-tagged-homebrew content, self-validates with the dnd5e-engine MCP tools, and writes structured notes via create_note.
---

# DnD 5e 备团 / 创作

帮人类 DM 生成跑团资产并写入 vault。遵循 `dnd5e-grounding` 的防幻觉铁律：数值/事实走 `dnd5e-engine` 工具，绝不凭记忆。全中文输出。

## 通用流程
1. **确认战役**：character / encounter / quest / session / campaign_state 是战役内类型，需要 `campaign`。不确定就先问用户是哪个战役，或用 `list_notes` 看现有战役。
2. **加载风格档案**：`load_style(campaign)` 取该战役语气/禁忌（缺失会返回中性缺省）。生成时遵循其语气与禁忌——**仅影响叙事措辞，规则数值/事实仍走工具、风格不得凌驾正确性**。
3. **生成草稿**：按用户要求生成内容（全中文）。
4. **自校验**（见下，按类型）。
5. **写入 vault**：用 `create_note(note_type, name, frontmatter, body, campaign?)`。原创内容在 frontmatter 标 `source: original, license: homebrew`；引用 SRD 实体则标 `source: SRD 5.1, license: CC-BY-4.0` 并带 citation。（`srd` 不再单独写，由 source/license 派生 —— 见 design §4.4 修订）
6. **回报**：告诉用户写到了哪个路径、做了哪些校验（附算式）。

## 按类型的校验（必做，禁止心算）
- **遭遇 encounter**：
  1. `encounter_budget(party_levels, difficulty)` 取该难度 XP 预算。
  2. `monsters_by_cr(min_cr, max_cr)` 选 SRD 合法怪物（或生成原创怪并用 `cr_to_xp` 估其 XP）。
  3. `evaluate_encounter(party_levels, monsters)` 核实难度档与预算匹配；把算式写进笔记。
- **怪物 / NPC stat block**：SRD 已有的用 `lookup_monster` 取真值，不要重写；原创怪用 `cr_to_xp` 核 CR↔XP，有施法则用 `spell_save_dc` / `spell_attack_bonus` 核数值。
- **法术 / 规则引用**：`lookup_spell` / `lookup_rule` / `lookup_condition`；查不到就标原创、不冒充 SRD。

## SRD 子集守则
SRD 仅约 300 怪物、9 种族、每职业 1 子职业、1 背景（Acolyte 侍僧）、1 专长（Grappler 擒抱者），不含 beholder / mind flayer / displacer beast / yuan-ti 等。生成超出 SRD 的内容时标 `source: original`（原创/非 SRD），绝不冒称出自 SRD。

## 示例：给"失落矿坑"做一个中等难度遭遇（4 个 3 级 PC）
1. `encounter_budget([3,3,3,3], "medium")` → 预算 600 XP。
2. `monsters_by_cr("1/4", "1")` → 候选含地精（CR 1/4）。
3. `evaluate_encounter([3,3,3,3], [{"cr":"1/4","count":6}])` → 看 band / adjusted_xp 是否贴近 medium；不够就加量或提 CR，再核一次。
4. `create_note("encounter", "矿口哥布林哨卡", campaign="失落矿坑", frontmatter={"location":"失落矿坑入口","difficulty":"medium"}, body="（写入怪物、算式、战术、触发）")`。
5. 回报路径与难度算式。

## 创建/编辑风格档案
每战役一份 `style.md`：`create_note("style", "style", campaign=<战役>, body="## 系统提示\n…\n## 语气样例\n…\n## 禁忌\n…")`。三节：系统提示片段、语气 few-shot、禁忌。随时可改。
