# 双Agent架构设计方案 (Dual-Agent Architecture Plan)

## 1. 现状分析 (Current State Analysis)
当前 `app.py` 中实现了一个基础的单Agent工具调用循环，能够调用 `calc` 工具进行简单的数学计算，但缺乏任务拆解和复杂任务流的控制能力，无法满足复杂任务的处理需求。

## 2. 目标与范围 (Goal & Scope)
目标是重构 `app.py`，实现一个“思考-执行”双LLM代理架构 (Manager-Worker Pattern)：
- **思考Agent (Thinking Agent)**：负责理解用户总任务，将其拆解为子任务。通过工具将子任务逐个委派给执行Agent。如果执行结果不符合预期，思考Agent会调整指令并重新委派；如果符合预期，则继续下一个子任务，直到完成所有任务并输出最终结果。
- **执行Agent (Execution Agent)**：接收来自思考Agent的具体子任务指令，利用自身配备的具体工具（如计算器、模拟网络搜索等）去实际执行，并将最终执行结果返回给思考Agent。

## 3. 具体修改方案 (Proposed Changes)
修改目标文件：`app.py`
### 3.1 工具定义 (Tools Definition)
- **为思考Agent配备的工具**：
  - `execute_subtask(instruction)`: 将子任务传达给执行Agent并获取结果。
  - `finish_task(final_answer)`: 结束整个任务流，向用户返回最终答案。
- **为执行Agent配备的工具**：
  - `calc(expression)`: 现有的数学计算工具。
  - `web_search(query)`: 新增的网络搜索工具（模拟），用于演示获取外部信息。
  - `python_eval(code)`: 新增的Python代码执行工具（模拟），用于演示代码运行。

### 3.2 Agent类设计 (Agent Class Design)
- **`ExecutionAgent` 类**：
  - 维护自己的系统提示词（System Prompt）和对话历史。
  - 实现一个标准的工具调用循环（Tool-calling Loop）：当LLM返回工具调用时，执行对应函数并将结果追加到历史记录；当LLM返回普通文本时，将其作为子任务的最终结果返回给思考Agent。
- **`ThinkingAgent` 类**：
  - 维护系统提示词（指导其进行任务拆解、逐步执行和结果检查）。
  - 实现高层级的工具调用循环：当它调用 `execute_subtask` 时，内部实例化或调用 `ExecutionAgent` 去执行；当它调用 `finish_task` 时，跳出循环并返回最终结果。

### 3.3 主循环逻辑 (Main Loop)
- 初始化 OpenAI 客户端（沿用当前的阿里云 DashScope 兼容配置及 `qwen3.5-flash` 模型）。
- 在 `while True` 循环中接收用户输入。
- 实例化 `ThinkingAgent`，传入用户输入，启动双Agent协同处理流程。
- 打印思考Agent的内部决策过程以及执行Agent的执行过程，以便直观展示双Agent的交互。

## 4. 假设与决策 (Assumptions & Decisions)
- **模型统一**：根据确认，两个Agent均使用 `qwen3.5-flash` 模型。
- **模拟工具**：为了演示双Agent能力，新增的 `web_search` 和 `python_eval` 将以模拟方式实现（返回固定或简单的逻辑结果），后续用户可以根据需要替换为真实的API调用。
- **鉴权**：沿用原代码中的 API Key 和 Base URL。

## 5. 验证步骤 (Verification Steps)
- 运行重构后的 `app.py`。
- 输入一个需要多步处理的复杂问题，例如：“请先搜索2024年奥运会的主办城市，然后计算该城市名字的字母数量的平方”。
- 观察终端输出，确认思考Agent是否正确拆解任务，执行Agent是否正确调用了 `web_search` 和 `calc` 工具，并且任务失败时是否有重试/调整逻辑。
