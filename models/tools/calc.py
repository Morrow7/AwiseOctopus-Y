from .registry import registry

@registry.register(
    name="calc",
    description="进行数学计算，例如加减乘除",
    parameters={
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "数学表达式，如 5 * 5"}
        },
        "required": ["expression"]
    }
)
def calc(expression):
    try:
        # 使用受限的命名空间进行 eval，防止执行任意恶意代码
        allowed_names = {
            "__builtins__": {},
            "abs": abs, "round": round, "min": min, "max": max,
            "int": int, "float": float
        }
        return str(eval(expression, allowed_names, {}))
    except Exception as e:
        return f"Error evaluating expression: {e}"