---
name: parse-module
description: Use when parsing an existing DnD 5e adventure module (text/markdown the user provides) into structured Obsidian vault assets — scenes, NPCs, encounters, clues, maps — linked into a dependency graph, with its prose made semantically searchable. Complements dnd5e-prep (which generates new content). Decomposes → create_note with [[links]] → index_module → validate_module_graph; all-Chinese, tagged with source/license.
---

# DnD 5e 模组解析

把用户提供的**已有模组文本**拆成 vault 资产（与 `dnd5e-prep` 互补：prep 生成新内容，本 skill 解析既有模组）。遵循 `dnd5e-grounding` 防幻觉铁律：数值/事实走 `dnd5e-engine` 工具，绝不凭记忆。全中文输出。

## 输入
模组文本（vault 内 md 路径或用户粘贴）+ 目标 `campaign` 名 + `source`（模组标题）+ `license`（如 `user-provided` / `fan-translation` / `CC-BY-4.0`）+ `ruleset`（默认 `dnd5e-2014`）。文本大就分趟、可续（`create_note` 的 `overwrite` 保证幂等重跑）。

## 流程
0. **加载风格档案**：先 `load_style(campaign)`，解析产出的中文叙事遵循该团语气/禁忌（仅措辞；数值/SRD 事实仍走工具）。
1. **拆 outline**：通读文本，列出 场景（及其 `exits` 顺序）、地点、NPC、遭遇、线索、地图。先把大纲给用户过目确认。
2. **逐节点 `create_note`**（全中文正文，据原文翻译/提炼）：
   - 类型用 `scene` / `npc` / `encounter` / `clue` / `map` / `campaign`（campaign 是模组概览/索引，用 `scenes` 字段以 `[[ ]]` 列出各场景，使图校验能把起始场景判为可达）。
   - frontmatter 带 `ruleset`、`campaign`、`source`、`license`、`layer: template`，以及关系链接（`[[ ]]`）：
     - `scene`：`location` / `npcs` / `encounters` / `clues` / `exits`
     - `clue`：`revealed_by` / `unlocks`；`encounter`：`location` / `monsters` / `scene`
   - 遭遇里的 SRD 实体（怪物/法术）用 `lookup_monster` / `lookup_spell` 取真值并引用；非 SRD 标 `source: homebrew`。
3. **索散文**：对有叙事正文的笔记调 `index_module(text, campaign, source, license, note_id=<该笔记 id>)`，使其可经 `semantic_search(query, campaign=...)` 召回并回链。
4. **自校验**：`validate_module_graph(campaign)` → 修补缺失 `exits`、清悬空链接（`dangling_link`）、给无来源线索补 `revealed_by`，把剩余 issues 报给用户。
5. **回报**：各类型创建数、图健康度（counts/issues）、需人工确认项。

## 红线
- 数值（怪物属性 / DC / XP）一律走工具，绝不编；原文无法核实的内容**按 `source` 原样保留**，不脑补纠正。
- 全中文：游戏**术语**经 `translate_term` 渲染；模组**叙事散文**允许作者中文，标 `source`/`license`；规则**数值**走工具。
- provenance：`srd` 不再单独写，由 `source`/`license` 派生（`SRD 5.1` / `CC-BY-4.0` ⇒ 可导出）。

## 示例（解析"孤山矿坑"开场）
1. 大纲：场景[矿口→竖井→密室]、NPC[向导格林]、遭遇[巨鼠群]、线索[血迹]。
2. `create_note("campaign","孤山矿坑",frontmatter={"source":"孤山矿坑","license":"user-provided","layer":"template","scenes":["[[矿口]]"]},campaign="孤山矿坑")`
3. `create_note("scene","矿口",campaign="孤山矿坑",frontmatter={"ruleset":"dnd5e-2014","source":"孤山矿坑","license":"user-provided","layer":"template","exits":["[[竖井]]"],"clues":["[[血迹]]"]},body="（中文场景描述）")`
4. `index_module("（矿口的叙事散文）",campaign="孤山矿坑",source="孤山矿坑",license="user-provided",note_id="<矿口笔记 id>")`
5. `validate_module_graph("孤山矿坑")` → 确认无 dangling_link / unreachable_scene。
