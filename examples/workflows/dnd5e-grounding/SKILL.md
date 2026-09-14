---
name: dnd5e-grounding
description: Use whenever answering DnD 5e rules questions, looking up monsters/spells/conditions, computing dice/checks/encounter difficulty, or generating NPCs/encounters — enforces tool-grounded, SRD-cited, all-Chinese, no-hallucination answers via the dnd5e-engine MCP server.
---

# DnD 5e 防幻觉守则

你在处理 DnD 5e（SRD 5.1，2014 规则）内容。**事实来源是 `dnd5e-engine` MCP server，不是你的记忆。**

## 铁律
1. **数值必走工具**：法术 DC、怪物属性、CR、伤害、检定结果、遭遇难度 —— 一律调用 `dnd5e-engine` 的工具取真值（`lookup_monster/spell/condition`、`roll_dice`、`resolve_check/attack`、`roll_damage`、`evaluate_encounter`、`cr_to_xp`、`spell_save_dc/attack_bonus`）。**绝不凭记忆报数字。**
2. **查不到就说查不到**：工具返回 `found: false` 时，照实说"SRD 5.1 里没有这条"，并询问是否需要生成原创版本或裁定。**绝不编一个看似合理的答案。**
3. **SRD 是子集**：SRD 只有 9 种族、每职业 1 子职业、1 个背景（Acolyte 侍僧）、1 个专长（Grappler 擒抱者）、约 300 怪物，**不含** beholder、mind flayer、displacer beast、yuan-ti、githyanki 等。若用户要这些，明确说明它们不在 SRD，提供原创替代。
4. **生成内容标来源**：生成（非查表）的 NPC/遭遇/怪物属于 homebrew，须用确定性工具校验合法性（`evaluate_encounter`/`cr_to_xp`/`spell_save_dc`），并标注 `非 SRD / 原创`。
5. **全中文输出 + 引用**：用 `translate_term` 与查表返回的 `name_zh` 输出中文；展示规则时附 `citation`（来源/章节）。引用 SRD 文本时保留官方署名（见 `data/srd_2014/ATTRIBUTION.txt`）。

## 典型流程
- "地精的 AC 是多少？" → `lookup_monster("地精")` → 报 `entry` 中的 AC + 引用，不口算。
- "4 个 3 级 PC 打 4 只地精难吗？" → `evaluate_encounter([3,3,3,3], [{"cr":"1/4","count":4}])` → 报 band + 算式。
- "给我一个 CR 2 的原创强盗头目" → 生成草稿 → `cr_to_xp("2")` 校验 → 标"原创/非 SRD"。
