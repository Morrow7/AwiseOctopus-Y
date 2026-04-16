import io
import contextlib
import traceback
from .registry import registry

# 维护一个全局的环境，使得多次调用python_eval能够共享变量
_python_global_env = {}

@registry.register(
    name="python_eval",
    description="执行一段Python代码并获取标准输出",
    parameters={
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "要执行的Python代码字符串"}
        },
        "required": ["code"]
    }
)
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