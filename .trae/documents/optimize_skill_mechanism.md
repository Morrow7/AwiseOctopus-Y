# 优化 Skill 机制计划

## 1. 当前问题分析 (Current State Analysis)
经过对代码库的探索，发现目前 Agent 无法正常找到合适 Skill 的原因主要有以下几点：
- **文件名强依赖与大小写敏感**：`_read_skill_md` 函数硬编码要求文件必须名为 `skill.md`。而实际存在的技能（如 `daily-report-assistant`）使用的是 `SKILL.md`，导致系统判定为缺少技能文件。
- **检索范围过于局限**：`_search_skill` 函数目前仅匹配“文件夹名称”和 `description.txt` 的内容。如果一个技能没有 `description.txt`，且文件夹名（如 `daily-report-assistant`）与用户的中文查询词（如“日报”）不匹配，Agent 就会搜索失败。
- **失败后缺乏上下文反馈**：当搜索失败时，系统仅返回 `"未找到与 'xxx' 相关的技能。"`，Agent 无法得知当前系统到底存在哪些技能，从而无法调整关键字重新搜索。

## 2. 改进方案 (Proposed Changes)

需要修改的文件：`g:\programe\_python\AwiseOctopus\models\thinking_agent.py`

### 2.1 增强 `_read_skill_md` 函数
- **逻辑优化**：优先查找 `skill.md` 或 `SKILL.md`。如果仍然找不到，则扫描文件夹并读取第一个找到的 `.md` 文件。
- **目的**：增强对不同命名习惯的兼容性。

### 2.2 优化 `_search_skill` 函数的检索与反馈逻辑
- **扩大搜索范围**：在原有的文件夹名和 `description.txt` 匹配基础上，**增加对技能目录下 `.md` 文件内容的匹配**。只要关键字出现在 Markdown 内容中，即视为匹配成功。
- **提供可用技能列表反馈**：如果搜索后未能找到匹配项，在返回错误信息的同时，**附带列出当前 `skills` 目录下所有可用的技能名称**（即文件夹列表）。这能帮助 Agent 在首次搜索失败后，根据返回的列表重新进行精准调用。
- **支持空关键字**：处理关键字为空的情况，此时直接返回所有可用技能列表。
- **支持多结果返回**：如果有多个技能匹配，将它们的内容拼接后一并返回，而不是只返回第一个。

### 2.3 优化 Agent 工具描述 (Tool Schema)
- **修改 `ThinkingAgent` 中 `search_skill` 的描述**：明确告知 Agent “如果不知道具体技能名，可以先传入空字符串获取所有可用技能列表”，帮助 Agent 更好地利用该工具。

## 3. 验证步骤 (Verification)
1. 确认修改后，无论是 `skill.md` 还是 `SKILL.md` 都能被成功读取。
2. 确认搜索诸如“日报”等关键字时，能够通过内容匹配到 `daily-report-assistant` 技能。
3. 确认输入不匹配的关键字或空关键字时，系统能够返回可用技能名称列表（如 `daily-report-assistant`, `data_analysis`）。