import json
import os
from .execution_agent import ExecutionAgent

def _search_skill(keyword):
    """根据关键字搜索 skills 目录，返回匹配的 skill.md 内容"""
    skills_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills")
    if not os.path.exists(skills_dir):
        return "未找到 skills 目录。"
    
    keyword = keyword.lower().strip() if keyword else ""
    available_skills = []
    matched_skills = []
    
    for skill_name in os.listdir(skills_dir):
        skill_path = os.path.join(skills_dir, skill_name)
        if not os.path.isdir(skill_path):
            continue
            
        available_skills.append(skill_name)
        
        # 如果没有关键字，直接继续收集所有可用技能
        if not keyword:
            continue
            
        is_match = False
        
        # 1. 匹配文件夹名
        if keyword in skill_name.lower():
            is_match = True
            
        # 2. 匹配 description.txt
        if not is_match:
            desc_file = os.path.join(skill_path, "description.txt")
            if os.path.exists(desc_file):
                with open(desc_file, "r", encoding="utf-8") as f:
                    desc_content = f.read()
                    if keyword in desc_content.lower():
                        is_match = True
                        
        # 3. 匹配 md 文件内容
        if not is_match:
            for filename in os.listdir(skill_path):
                if filename.lower().endswith(".md"):
                    md_file = os.path.join(skill_path, filename)
                    try:
                        with open(md_file, "r", encoding="utf-8") as f:
                            md_content = f.read()
                            if keyword in md_content.lower():
                                is_match = True
                                break
                    except Exception:
                        pass
                        
        if is_match:
            matched_skills.append(_read_skill_md(skill_path))
            
    if not keyword:
        return f"当前可用的技能有: {', '.join(available_skills)}"
        
    if not matched_skills:
        return f"未找到与 '{keyword}' 相关的技能。当前可用的技能有: {', '.join(available_skills)}"
        
    return "\n\n".join(matched_skills)

def _read_skill_md(skill_path):
    # 优先查找 skill.md 或 SKILL.md
    for filename in ["skill.md", "SKILL.md"]:
        skill_md_file = os.path.join(skill_path, filename)
        if os.path.exists(skill_md_file):
            with open(skill_md_file, "r", encoding="utf-8") as f:
                return f"成功加载技能 [{os.path.basename(skill_path)}] ({filename})：\n" + f.read()
    
    # 否则查找任意 .md 文件
    for filename in os.listdir(skill_path):
        if filename.lower().endswith(".md"):
            skill_md_file = os.path.join(skill_path, filename)
            try:
                with open(skill_md_file, "r", encoding="utf-8") as f:
                    return f"成功加载技能 [{os.path.basename(skill_path)}] ({filename})：\n" + f.read()
            except Exception:
                pass
                
    return f"技能 [{os.path.basename(skill_path)}] 缺少 .md 文件。"

class ThinkingAgent:
    def __init__(self, client, model):
        self.client = client
        self.model = model
        self.system_prompt = (
            "你是一个思考Agent（Manager）。你的任务是拆解用户的复杂请求，并协调执行Agent完成它。\n"
            "你可以使用工具 `execute_subtask` 将子任务委派给执行Agent。\n"
            "执行Agent会返回结果。你需要判断结果是否符合要求，如果符合，继续委派下一个任务；如果不符合，调整任务指令再次委派。\n"
            "\n【专家技能加载】\n"
            "如果你遇到了特定领域的任务（例如数据分析、前端开发等），请先使用 `search_skill` 工具查找并加载相关的专家技能指导（skill.md）。\n"
            "将加载出来的指导原则和SOP作为你后续思考、规划和委派任务的重要参考依据！\n"
            "\n【重要容错与修正策略】\n"
            "当某一个任务或方法多次失败、无法获得预期结果（例如网络搜索失败、计算出错等）时，你必须**主动修正思考方向**。\n"
            "一种非常有效的替代方案是：**让执行Agent通过编写并运行Python代码（使用其内置的 python_eval 工具）来完成任务**。例如通过Python去请求API、爬取网页、处理复杂逻辑等。\n"
            "如果各种方法都尝试失败，或者你对下一步的执行方向有严重疑虑时，请**使用 `ask_user_for_help` 工具向用户提问**。你可以提供几个你思考的方向供用户选择，或者让用户直接给你提供新的解决思路。\n"
            "\n"
            "当所有子任务都已完成并且你收集到了所需的全部信息后，必须使用 `finish_task` 工具向用户返回最终答案。\n"
            "千万不要自己去猜事实或做计算，必须依靠执行Agent去完成实际操作！"
        )
        self.thinking_tools_schema = [
            {
                "type": "function",
                "function": {
                    "name": "search_skill",
                    "description": "搜索并加载相关的专家技能（纯文本Prompt/SOP）。如果不知道具体技能名，可以先传入空字符串获取所有可用技能列表。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keyword": {"type": "string", "description": "技能的关键字。传入空字符串可以列出所有可用技能。"}
                        },
                        "required": ["keyword"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_subtask",
                    "description": "将一个子任务委派给执行Agent并获取执行结果。你需要给出详细的任务描述。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "instruction": {"type": "string", "description": "子任务的详细指令"}
                        },
                        "required": ["instruction"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "ask_user_for_help",
                    "description": "当你多次尝试失败，或者无法确定下一步如何执行时调用。你可以向用户描述当前困境，提供几个候选方案让用户选择，或者让用户直接给出思路。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string", "description": "向用户提出的问题，包括当前的困境和可能的新思考方向。"}
                        },
                        "required": ["question"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "finish_task",
                    "description": "当整个用户任务完成时调用，返回最终的综合答案。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "final_answer": {"type": "string", "description": "最终回复用户的答案"}
                        },
                        "required": ["final_answer"]
                    }
                }
            }
        ]
        
    def run_stream(self, user_request):
        yield ("RUNNING", "\n=== [思考Agent 启动] 开始分析任务 ===")
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_request}
        ]
        
        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.thinking_tools_schema
            )
            msg = response.choices[0].message
            messages.append(msg)
            
            if msg.tool_calls:
                for tool_call in msg.tool_calls:
                    name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    
                    if name == "search_skill":
                        keyword = args.get("keyword", "")
                        yield ("RUNNING", f"\n[思考Agent 检索技能] 关键词: {keyword}")
                        skill_content = _search_skill(keyword)
                        
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": name,
                            "content": str(skill_content)
                        })
                    elif name == "execute_subtask":
                        instruction = args.get("instruction", "")
                        yield ("RUNNING", f"\n[思考Agent 决策] 委派子任务 -> {instruction}")
                        worker = ExecutionAgent(self.client, self.model)
                        
                        # 消费 ExecutionAgent 的流式输出
                        worker_gen = worker.run_stream(instruction)
                        try:
                            while True:
                                log_msg = next(worker_gen)
                                yield ("RUNNING", log_msg)
                        except StopIteration as e:
                            result = e.value
                        
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": name,
                            "content": result
                        })
                    elif name == "ask_user_for_help":
                        question = args.get("question", "")
                        yield ("RUNNING", f"\n[思考Agent 遇到困难求助] {question}")
                        
                        user_reply = yield ("ASK_USER", question)
                        
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": name,
                            "content": f"用户提供的思路/回答: {user_reply}"
                        })
                    elif name == "finish_task":
                        final_answer = args.get("final_answer", "")
                        yield ("RUNNING", "\n=== [思考Agent 完成] 所有任务已完成 ===")
                        yield ("FINISHED", final_answer)
                        return final_answer
            else:
                if msg.content:
                    yield ("RUNNING", f"\n[思考Agent 自言自语] {msg.content}")
                    messages.append({"role": "user", "content": "请使用工具 execute_subtask 委派任务，或使用 finish_task 结束。"})

    def run(self, user_request):
        gen = self.run_stream(user_request)
        user_input_to_send = None
        
        try:
            while True:
                if user_input_to_send is not None:
                    status, payload = gen.send(user_input_to_send)
                    user_input_to_send = None
                else:
                    status, payload = next(gen)
                    
                if status == "RUNNING":
                    print(payload)
                elif status == "ASK_USER":
                    user_reply = input(f"[提示] 请给Agent提供思路或选择方案: ")
                    user_input_to_send = user_reply
                elif status == "FINISHED":
                    return payload
        except StopIteration as e:
            return e.value
