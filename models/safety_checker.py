import json

def is_action_safe(client, model, tool_name, args):
    """
    判断工具执行是否安全，是否可以免除人工审查。
    返回 True 表示安全，可免审；False 表示高危，需人工确认。
    """
    # 1. 混合沙箱免审：如果是 python_eval 且 use_sandbox 为 True
    if tool_name == "python_eval":
        use_sandbox = args.get("use_sandbox", True)
        if isinstance(use_sandbox, str):
            use_sandbox = use_sandbox.lower() == 'true'
        if use_sandbox:
            return True
            
    # 2. LLM 动态分析
    prompt = f"""你是一个安全审查专家。请分析以下工具调用是否属于"仅仅获取信息、读取数据或安全的纯计算"，而不包含任何对系统的修改、删除或破坏性操作。

工具名称: {tool_name}
工具参数: {json.dumps(args, ensure_ascii=False, indent=2)}

如果该操作是安全的（如读取文件内容、获取系统状态、执行只读查询、纯逻辑计算等），请回复 "SAFE"。
如果该操作是高危的（如写入文件、删除文件、修改系统配置、执行可能修改状态的脚本、执行未知网络请求等），请回复 "UNSAFE"。
只回复 "SAFE" 或 "UNSAFE"，不要包含任何其他内容。"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        result = response.choices[0].message.content.strip().upper()
        if "SAFE" in result and "UNSAFE" not in result:
            return True
        elif "UNSAFE" in result:
            return False
        else:
            return False
    except Exception as e:
        print(f"\n    [安全审查] LLM 判断出错: {e}，默认要求人工确认。")
        return False
