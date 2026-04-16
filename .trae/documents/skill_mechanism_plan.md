# 技能与工具模块重构与现代Agent Skill机制设计方案 (Refactor & Skill Mechanism Plan)

## 1. 现状分析 (Current State Analysis)
目前项目中存在一个 `models/skills` 目录，其中存放的是大模型执行具体动作的函数（如 `calc`, `web_search`, `python_eval`）。但在现代 Agent 架构中，这些能够执行实际动作的函数更适合被称为 `tools`（工具），而 `skills`（技能）通常指代特定领域的“专家知识”、“SOP（标准操作流程）”或“指导提示词（Prompt）”。

## 2. 目标与范围 (Goal & Scope)
1. **重命名现有模块**：将原先的 `models/skills` 目录及其内部的逻辑更名为 `models/tools`，以符合实际的工具属性。
2. **新增现代 Skill 机制**：在项目根目录建立一个专门存放纯文本技能指导的 `skills` 文件夹。每个技能是一个子文件夹，其中包含 `skill.md`（技能的详细Prompt/SOP）。
3. **思考Agent的检索能力**：为思考Agent（Thinking Agent）配备一个新的工具 `search_skill(keyword)`。在面对复杂或特定领域的任务时，思考Agent可以主动检索这些纯文本技能，读取 `skill.md` 的内容并加载到自己的上下文中，从而获得“专家级”的决策指导。

## 3. 具体修改方案 (Proposed Changes)
### 3.1 工具模块重命名 (Rename to Tools)
- 移动/重命名：将 `models/skills/` 文件夹重命名为 `models/tools/`。
- 修改导入路径：
  - `models/tools/__init__.py` 中的扫描逻辑。
  - 各个工具文件（`calc.py`, `web_search.py`, `python_eval.py`）中对 `registry.py` 的导入。
  - `models/execution_agent.py` 中对 `registry` 的导入改为 `from .tools import registry`。

### 3.2 建立纯文本 Skill 目录结构 (Create Skills Directory)
- 在项目根目录（`g:\programe\_python\AwiseOctopus\`）创建 `skills` 文件夹。
- 为了演示，创建一个示例技能，例如 `skills/data_analysis/`。
- 在该技能文件夹下创建 `skill.md`，写入一些数据分析的指导原则和SOP。
- 在该技能文件夹下创建 `description.txt`，用一句话描述该技能，方便搜索匹配。

### 3.3 为思考Agent添加 `search_skill` 工具 (Add search_skill Tool)
- 在 `models/thinking_agent.py` 中：
  - 修改 `self.system_prompt`，增加关于“检索并加载专家技能（Skill）”的指导原则。
  - 在 `self.thinking_tools_schema` 中添加 `search_skill` 工具的定义（参数：`keyword`）。
  - 在 `run` 方法的工具分发逻辑中，实现 `search_skill` 的执行：遍历根目录的 `skills/` 文件夹，读取各个技能的 `description.txt` 或文件夹名，若与 `keyword` 匹配，则读取并返回其 `skill.md` 的完整内容。

## 4. 假设与决策 (Assumptions & Decisions)
- **匹配机制**：`search_skill` 采用简单的关键字匹配（匹配文件夹名称或 `description.txt` 内容）。这种“一步到位”的方式最符合用户需求，能够直接将相关的 `skill.md` 内容加载进上下文。
- **职责分离**：明确了 `ExecutionAgent` 使用 `tools`（执行动作），而 `ThinkingAgent` 使用 `skills`（获取指导策略）。

## 5. 验证步骤 (Verification Steps)
- 运行一个测试脚本或 `app.py`。
- 给出一个需要特定技能的任务（例如：“请帮我进行数据分析”）。
- 观察终端输出，确认思考Agent是否主动调用了 `search_skill`，是否成功读取了 `skill.md` 的内容，并根据该内容给出了相应的子任务指令。