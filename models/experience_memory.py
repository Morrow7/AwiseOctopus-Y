import os
import json
import sqlite3
import uuid
import datetime
from pathlib import Path

try:
    import chromadb
except ImportError:
    chromadb = None

class ExperienceMemoryManager:
    _instance = None

    def __new__(cls, db_path="experience.db", chroma_path="experience_vector"):
        if cls._instance is None:
            cls._instance = super(ExperienceMemoryManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path="data/experience.db", chroma_path="data/experience_vector"):
        if self._initialized:
            return
            
        self._initialized = True
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.chroma_path = chroma_path
        
        # Initialize SQLite
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._create_table()
        
        # Initialize ChromaDB
        if chromadb:
            self.chroma_client = chromadb.PersistentClient(path=self.chroma_path)
            self.collection = self.chroma_client.get_or_create_collection(name="agent_experiences")
        else:
            self.chroma_client = None
            self.collection = None

    def _create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS experiences (
                id TEXT PRIMARY KEY,
                task_type TEXT,
                instruction TEXT,
                process_log TEXT,
                result TEXT,
                success_score REAL,
                weight REAL,
                created_at TIMESTAMP
            )
        ''')
        self.conn.commit()

    def add_experience(self, task_type, instruction, process_log, result, success_score):
        """记录任务经验，存储到 SQLite 和 ChromaDB"""
        exp_id = str(uuid.uuid4())
        created_at = datetime.datetime.now().isoformat()
        weight = float(success_score)
        
        # 1. 存入 SQLite
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO experiences (id, task_type, instruction, process_log, result, success_score, weight, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (exp_id, task_type, instruction, str(process_log), str(result), float(success_score), weight, created_at))
        self.conn.commit()
        
        # 2. 存入 ChromaDB
        if self.collection:
            self.collection.add(
                documents=[instruction],
                metadatas=[{"task_type": task_type}],
                ids=[exp_id]
            )

    def search_experience(self, task_type, instruction, top_k=3):
        """搜索历史经验，根据 weight 分为成功和失败两类"""
        if not self.collection:
            return ""
            
        # 1. 向量检索最相关的 instruction
        results = self.collection.query(
            query_texts=[instruction],
            n_results=top_k * 2,
            where={"task_type": task_type}
        )
        
        if not results['ids'] or not results['ids'][0]:
            return ""
            
        exp_ids = results['ids'][0]
        
        # 2. 从 SQLite 获取详细信息
        placeholders = ','.join('?' for _ in exp_ids)
        cursor = self.conn.cursor()
        cursor.execute(f'''
            SELECT id, instruction, process_log, result, weight 
            FROM experiences 
            WHERE id IN ({placeholders})
            ORDER BY weight DESC
        ''', exp_ids)
        
        rows = cursor.fetchall()
        
        successful_exps = []
        failed_exps = []
        
        for row in rows:
            exp = {
                "instruction": row[1],
                "process_log": row[2],
                "result": row[3],
                "weight": row[4]
            }
            if exp["weight"] >= 0.6:
                if len(successful_exps) < top_k:
                    successful_exps.append(exp)
            else:
                if len(failed_exps) < top_k:
                    failed_exps.append(exp)
                    
        if not successful_exps and not failed_exps:
            return ""
            
        # 3. 格式化输出
        hint = "【历史经验参考】\n针对类似的任务，系统有以下经验记录：\n"
        
        if successful_exps:
            hint += "\n✅ 成功的做法（高分经验）：\n"
            for i, exp in enumerate(successful_exps, 1):
                hint += f"  {i}. 任务: {exp['instruction']}\n     过程: {exp['process_log']}\n     结果: {exp['result']}\n"
                
        if failed_exps:
            hint += "\n❌ 失败的做法（请避免这些错误）：\n"
            for i, exp in enumerate(failed_exps, 1):
                hint += f"  {i}. 任务: {exp['instruction']}\n     过程: {exp['process_log']}\n     结果: {exp['result']}\n"
                
        return hint

def evaluate_experience(client, model, instruction, process_log, result):
    """使用 LLM 评估任务执行是否成功，返回 0.0 到 1.0 的分数"""
    prompt = (
        "你是一个任务评估专家。请根据以下信息，评估任务的执行是否成功。\n\n"
        f"原始任务指令：\n{instruction}\n\n"
        f"执行过程记录：\n{process_log}\n\n"
        f"最终结果：\n{result}\n\n"
        "请给出一个 0.0 到 1.0 之间的浮点数作为评分（1.0 表示完美完成，0.0 表示完全失败）。\n"
        "评分标准：\n"
        "- 1.0: 完美解决，没有任何错误\n"
        "- 0.8: 基本解决，但有些许瑕疵\n"
        "- 0.5: 部分解决，存在明显问题\n"
        "- 0.2: 严重错误，偏离目标\n"
        "- 0.0: 完全失败或崩溃\n"
        "请直接回复这个浮点数，不要输出任何其他内容。"
    )
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=10
        )
        score_str = response.choices[0].message.content.strip()
        # 提取浮点数
        score = float(score_str)
        return max(0.0, min(1.0, score))
    except Exception as e:
        print(f"\n[经验记忆] 评估失败，默认给予 0.5 分: {e}")
        return 0.5
