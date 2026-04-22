import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from models import ThinkingAgent

load_dotenv()
api_key = os.getenv("api_key")
base_url = os.getenv("base_url")
MODEL = os.getenv("MODEL")

client = OpenAI(api_key=api_key, base_url=base_url)

print("Starting test...")
agent = ThinkingAgent(client, MODEL)

try:
    print("\n--- Turn 1 ---")
    res1 = agent.run("请告诉我 1+1 等于几，只需要直接告诉我数字。")
    print(f"Turn 1 result: {res1}")

    print("\n--- Turn 2 ---")
    res2 = agent.run("我上一个问题问了什么？")
    print(f"Turn 2 result: {res2}")
except Exception as e:
    print("ERROR:", e)
    for i, m in enumerate(agent.messages):
        if isinstance(m, dict):
            print(f"[{i}] {m.get('role')}: {m.get('name')} {m.get('content')} | {m.get('tool_call_id')}")
        else:
            print(f"[{i}] {m.role}: tool_calls={m.tool_calls[0].function.name if m.tool_calls else 'None'}")
