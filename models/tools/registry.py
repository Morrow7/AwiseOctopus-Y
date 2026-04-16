class SkillRegistry:
    def __init__(self):
        self.skills = {}
        self.schemas = []

    def register(self, name, description, parameters):
        """
        注册技能的装饰器
        """
        def decorator(func):
            self.skills[name] = func
            self.schemas.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters
                }
            })
            return func
        return decorator

    def execute(self, name, args):
        """
        执行技能
        """
        if name in self.skills:
            try:
                return self.skills[name](**args)
            except Exception as e:
                return f"执行技能 {name} 发生异常: {e}"
        else:
            return f"技能 {name} 不存在"

# 全局的技能注册表实例
registry = SkillRegistry()
