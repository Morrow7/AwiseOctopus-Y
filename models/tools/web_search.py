from duckduckgo_search import DDGS
from .registry import registry

@registry.register(
    name="web_search",
    description="进行网络搜索获取外部信息",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词"}
        },
        "required": ["query"]
    }
)
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