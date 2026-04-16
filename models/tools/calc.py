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
        return str(eval(expression))
    except Exception as e:
        return f"Error evaluating expression: {e}"