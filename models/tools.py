import io
import sys
import traceback
import contextlib
from duckduckgo_search import DDGS

def calc(expression):
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Error evaluating expression: {e}"

def web_search(query):
    print(f"\n    [系统提示] 执行Agent正在使用真实网络搜索工具，搜索: {query}")
    try:
        results = DDGS().text(query, max_results=3)
        if not results:
            return "未找到相关结果。"
        
        formatted_results = []
        for i, res in enumerate(results, 1):
            formatted_results.append(f"结果 {i}:\n标题: {res['title']}\n摘要: {res['body']}\n")
        return "\n".join(formatted_results)
    except Exception as e:
        return f"网络搜索失败: {e}"

# 维护一个全局的环境，使得多次调用python_eval能够共享变量
_python_global_env = {}

def python_eval(code):
    print(f"\n    [系统提示] 执行Agent正在执行Python代码: \n{code}")
    output = io.StringIO()
    error_output = io.StringIO()
    
    try:
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error_output):
            exec(code, _python_global_env)
        
        out_str = output.getvalue()
        err_str = error_output.getvalue()
        
        result = ""
        if out_str:
            result += out_str
        if err_str:
            result += f"\n[Error Output]:\n{err_str}"
            
        return result.strip() or "代码执行成功，无输出。"
    except Exception:
        return f"代码执行发生异常:\n{traceback.format_exc()}"

execution_tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "calc",
            "description": "进行数学计算，例如加减乘除",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "数学表达式，如 5 * 5"}
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "进行网络搜索获取外部信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "python_eval",
            "description": "执行一段Python代码并获取标准输出",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "要执行的Python代码字符串"}
                },
                "required": ["code"]
            }
        }
    }
]
