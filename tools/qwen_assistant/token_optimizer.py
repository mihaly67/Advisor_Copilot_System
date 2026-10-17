#!/usr/bin/env python3
from dataclasses import dataclass
from typing import List, Dict
import json
import os

@dataclass
class ContextEntry:
    task: str
    result: str
    timestamp: float
    tokens_used: int
    embedding: List[float]

class TokenOptimizer:
    def __init__(self, storage_path: str = '/data/mcp_server/data/token_optimizer.json'):
        self.storage_path = storage_path
        self.entries: List[ContextEntry] = []
        self.max_entries = 1000
        self.load_memory()
    
    def save_memory(self):
        data = [{
            'task': e.task,
            'result': e.result,
            'timestamp': e.timestamp,
            'tokens_used': e.tokens_used,
            'embedding': e.embedding
        } for e in self.entries]
        
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump(data, f)
    
    def load_memory(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                self.entries = [ContextEntry(**entry) for entry in data]
    
    def add_entry(self, task: str, result: str, tokens_used: int):
        import time
        entry = ContextEntry(
            task=task,
            result=result,
            timestamp=time.time(),
            tokens_used=tokens_used,
            embedding=self.encode_context(task)
        )
        self.entries.append(entry)
        
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]
        
        self.save_memory()
    
    def encode_context(self, text: str) -> List[float]:
        return [float(ord(c)) / 256.0 for c in text[:100]]
    
    def get_relevant_context(self, current_task: str, top_k: int = 5) -> str:
        if not self.entries:
            return ''
        
        current_embedding = self.encode_context(current_task)
        scored = []
        
        for entry in self.entries:
            score = self.cosine_similarity(current_embedding, entry.embedding)
            scored.append((score, entry))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        top_entries = [entry for _, entry in scored[:top_k]]
        
        context_parts = []
        total_tokens = 0
        
        for entry in top_entries:
            if total_tokens + entry.tokens_used <= 2000:
                context_parts.append(f"Eredmény: {entry.result}")
                total_tokens += entry.tokens_used
            else:
                break
        
        return ' '.join(context_parts)
    
    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        if len(a) != len(b) or len(a) == 0:
            return 0.0
        
        dot = sum(ai * bi for ai, bi in zip(a, b))
        mag_a = sum(ai * ai for ai in a) ** 0.5
        mag_b = sum(bi * bi for bi in b) ** 0.5
        
        return dot / (mag_a * mag_b) if mag_a * mag_b > 0 else 0.0
    
    def estimate_token_savings(self, task: str) -> int:
        relevant_context = self.get_relevant_context(task)
        original_tokens = len(task.split()) * 2
        optimized_tokens = len(task.split()) + len(relevant_context.split())
        
        return max(0, original_tokens - optimized_tokens)

if __name__ == '__main__':
    optimizer = TokenOptimizer()
    print('Token Optimizer inicializálva')