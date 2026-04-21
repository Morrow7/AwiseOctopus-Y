import traceback
from .registry import registry
from models.sandbox.ao_local_sandbox import AOLocalSandbox

# 初始化全局沙箱单例，复用上下文状态
_sandbox_instance = None

def get_sandbox():
    global _sandbox_instance
    if _sandbox_instance is None:
        # 在首次调用时实例化沙箱
        _sandbox_instance = AOLocalSandbox()
    return _sandbox_instance

@registry.register(
    name="python_eval",
    description="执行一段Python代码并获取标准输出",
    parameters={
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "要执行的Python代码字符串"}
        },
        "required": ["code"]
    },
    requires_confirmation=True
)
def python_eval(code):
    print(f"\n    [系统提示] 执行Agent正在使用沙箱执行Python代码: \n{code}")
    try:
        sandbox = get_sandbox()
        result = sandbox.execute_code(code)
        return result
    except Exception:
        return f"代码执行发送给沙箱时发生异常:\n{traceback.format_exc()}"