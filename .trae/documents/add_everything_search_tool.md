# 新增 Everything 本地文件搜索工具计划

## 1. 当前问题分析 (Current State Analysis)
- 当前 `AwiseOctopus` 项目在 `models/tools/` 目录下通过 `@registry.register` 装饰器机制自动注册和加载执行工具。
- 项目内置了 Everything SDK 的动态链接库文件，存放路径为 `libs/Everything_SDK/dll/`。
- 为了增强 Agent 查找本地文件的能力，需要基于 Everything SDK 编写一个新的工具模块。

## 2. 改进方案 (Proposed Changes)

**新增文件**：`g:\programe\_python\AwiseOctopus\models\tools\search_local_file.py`

### 2.1 引入和配置 Everything SDK
- 在文件中使用 `ctypes` 模块加载 Everything 的 DLL。
- 通过判断操作系统的位数（`sys.maxsize > 2**32`）来动态决定是加载 `Everything64.dll` 还是 `Everything32.dll`。
- 配置所需的 C 函数的 `argtypes` 和 `restype`（如 `Everything_SetSearchW`, `Everything_SetMax`, `Everything_QueryW`, `Everything_GetNumResults`, `Everything_GetResultFullPathNameW` 等），以确保参数传递正确。

### 2.2 定义并注册 `search_local_file` 工具
- 使用 `@registry.register` 装饰器注册该工具。
- **工具名称**：`search_local_file`
- **参数定义**：
  - `keyword` (string): 搜索关键词（支持 Everything 的搜索语法，如通配符等）。
  - `max_results` (integer, 可选): 最大返回结果数量，默认建议设为 10，避免返回数据过大。
- **执行逻辑**：
  1. 检查 DLL 是否成功加载，未加载则返回错误信息。
  2. 调用 `Everything_SetSearchW` 设置查询关键词。
  3. 调用 `Everything_SetMax` 设置最大返回条数。
  4. 调用 `Everything_QueryW(True)` 执行同步查询。
  5. 调用 `Everything_GetNumResults` 获取命中条数。
  6. 遍历结果，使用 `Everything_GetResultFullPathNameW` 并配合 `ctypes.create_unicode_buffer(260)` 获取每个结果的绝对路径。
  7. 将结果组装为可读的文本列表返回给大模型。
  8. 异常处理：捕获 `ctypes` 调用可能产生的错误，并捕获 Everything 后台服务未启动的情况。

## 3. 假设与决策 (Assumptions & Decisions)
- **假设**：用户的 Windows 系统中已安装并正在后台运行 Everything 服务程序，因为 Everything SDK 查询依赖于 Everything 服务端提供的数据。
- **决策**：由于直接返回海量搜索结果会导致 LLM 上下文超载，所以强制通过 `Everything_SetMax` 限制返回数量。如果需要更多结果，可以让模型通过更精准的关键词进行搜索。

## 4. 验证步骤 (Verification)
1. 编写或直接运行一个 Python 单行脚本（或使用 `python_eval`），导入并执行 `registry.execute("search_local_file", {"keyword": "Everything64.dll"})`。
2. 确认脚本能够成功返回项目库中 `Everything64.dll` 的绝对路径，无崩溃或报错。