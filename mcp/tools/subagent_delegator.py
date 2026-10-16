#!/usr/bin/env python3
"""
Subagent Delegálási Rendszer - Master-Slave Stratégia
Cél: Automatikus feladatszétosztás Qwen (Subagent) és Master között
Hely: /data/mcp_server/tools/subagent_delegator.py
"""

import os
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Any

class SubagentDelegator:
    """Subagent delegálási rendszer - Master stratégia"""
    
    def __init__(self, brain_path: str = "/data/Brain"):
        self.brain_path = brain_path
        self.qwen_analyzer = "/data/mcp_server/tools/qwen_analyzer.py"
        self.env_file = "/data/mcp_server/env.sh"
        
    def analyze_task_complexity(self, task_description: str) -> str:
        """Feladat komplexitás elemzése"""
        task_lower = task_description.lower()
        
        # Egyszerű feladatok - Qwen egyedül
        simple_keywords = [
            'olvas', 'elemz', 'keres', 'listáz', 'mutass', 'kiír', 
            'log', 'ment', 'kategóri', 'index', 'search', 'find'
        ]
        
        # Közepes feladatok - Qwen + Master irányítás
        medium_keywords = [
            'implementál', 'integrál', 'kódol', 'tool', 'mcp', 
            'tesztel', 'hiba javít', 'refactor', 'debugger'
        ]
        
        # Komplex feladatok - Master
        complex_keywords = [
            'architektúra', 'rendszer', 'döntés', 'biztonság',
            'stratégia', 'komplex hibaelhárítás', 'rendszerszintű'
        ]
        
        # Komplexitás elemzése
        if any(keyword in task_lower for keyword in simple_keywords):
            return "simple"
        elif any(keyword in task_lower for keyword in medium_keywords):
            return "medium"
        else:
            return "complex"
    
    def delegate_to_qwen(self, repository: str, max_files: int = 30, max_tokens: int = 2000) -> Dict[str, Any]:
        """Feladat delegálása Qwen-nek (Subagent)"""
        try:
            print(f"🤖 Delegálás Qwen-nek: {repository}")
            
            # Qwen elemzés indítása
            cmd = [
                "bash", "-c",
                f"source {self.env_file} && python3 {self.qwen_analyzer} "
                f"--max-files {max_files} --max-tokens {max_tokens} {repository}"
            ]
            
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                return {
                    "status": "success",
                    "repository": repository,
                    "output": stdout,
                    "token_usage": "minimal (Qwen - ingyenes)"
                }
            else:
                return {
                    "status": "failed",
                    "repository": repository,
                    "error": stderr,
                    "token_usage": "minimal (Qwen - ingyenes)"
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "repository": repository,
                "error": str(e),
                "token_usage": "minimal (Qwen - ingyenes)"
            }
    
    def batch_delegate(self, repositories: List[str], complexity: str = "medium") -> List[Dict[str, Any]]:
        """Batch delegálás több repository-ra"""
        results = []
        
        print(f"🚀 Batch delegálás - {complexity} komplexitás")
        
        for repo in repositories:
            repo_path = os.path.join(self.brain_path, repo)
            
            if os.path.exists(repo_path):
                # Komplexitás alapú paraméterek
                if complexity == "simple":
                    max_files = 20
                    max_tokens = 1500
                elif complexity == "medium":
                    max_files = 30
                    max_tokens = 2000
                else:  # complex
                    max_files = 50
                    max_tokens = 3000
                
                result = self.delegate_to_qwen(repo_path, max_files, max_tokens)
                results.append(result)
            else:
                results.append({
                    "status": "not_found",
                    "repository": repo,
                    "error": f"Repository nem található: {repo_path}"
                })
        
        return results
    
    def get_code_extraction_target(self) -> str:
        """Kód kitermelési cél repository keresése"""
        # Prioritási sorrend debugger és subagent repository-k
        priority_repos = [
            "debugger-mcp-main",
            "python-sdk-main",
            "autogen-main",
            "openai-agents-python"
        ]
        
        for repo in priority_repos:
            repo_path = os.path.join(self.brain_path, repo)
            if os.path.exists(repo_path):
                # Ellenőrizzük, hogy van-e elemzés
                analysis_dir = os.path.join(repo_path, "_qwen_analysis")
                if not os.path.exists(analysis_dir) or len(os.listdir(analysis_dir)) == 0:
                    return repo_path
        
        return os.path.join(self.brain_path, priority_repos[0])


def main():
    """Fő teszt program"""
    delegator = SubagentDelegator()
    
    print("🎯 Subagent Delegálási Rendszer Indítása")
    print("=" * 50)
    
    # 1. Cél repository keresése
    target_repo = delegator.get_code_extraction_target()
    print(f"🎯 Cél repository: {target_repo}")
    
    # 2. Qwen delegálás
    result = delegator.delegate_to_qwen(target_repo)
    print(f"📊 Eredmény: {result['status']}")
    
    # 3. Feladat komplexitás teszt
    task = "Keresd meg a debugger repository-ban a kódokat és implementációkat"
    complexity = delegator.analyze_task_complexity(task)
    print(f"📋 Feladat komplexitás: {complexity}")
    
    return result


if __name__ == "__main__":
    main()