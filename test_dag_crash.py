import asyncio
from models.dag_executor import DAGExecutor
import json

# A mock ThinkingAgent to satisfy DAGExecutor arguments
class MockManager:
    pass

# Mock OpenAI client
class MockClient:
    pass

async def test_concurrency():
    tasks = []
    
    # Create 5 concurrent Everything queries
    for i in range(5):
        tasks.append({
            "id": f"search_{i}",
            "type": "tool",
            "tool": "search_local_file",
            "input": {"keyword": f"python{i}.exe"},
            "dependencies": []
        })
        
    # Create 5 concurrent python_eval queries
    for i in range(5):
        tasks.append({
            "id": f"eval_{i}",
            "type": "tool",
            "tool": "python_eval",
            "input": {"code": f"print('Hello from thread {i}')\n", "use_sandbox": True},
            "dependencies": []
        })
        
    executor = DAGExecutor(tasks, MockClient(), "mock-model", MockManager(), interaction_handler=None)
    
    print("Executing DAG...")
    results = await executor.execute()
    print("Execution completed.")
    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(test_concurrency())
