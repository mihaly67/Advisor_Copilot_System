#!/usr/bin/env python3
"""Konkrét működő memória manager MCP-nek és Qwen-nek.

Kezeli a /data/mcp_server/context könyvtárban lévő:
  - active_memory.json  (MCP 'agy': repók, snippetek, stratégiák, státuszok)
  - qwen_memory.json    (Qwen elemzések: repo -> analysis/patterns/main_files)

Megjegyzés: a rendszer többi komponense (master_orchestrator,
memory_event_watcher, reasoning_pipeline, stb.) közvetlenül az
active_memory.json fájlútvonalat használja — ez az osztály egy
önálló segédprogram a memória inicializálására és karbantartására.
"""
import os
import json
from datetime import datetime
from pathlib import Path


class MemoryManager:
    """Központi memória-kezelő az MCP és a Qwen elemzések fölött."""

    def __init__(self, base_path="/data/mcp_server/context"):
        self.base_path = Path(base_path)
        self.memory_file = self.base_path / "active_memory.json"
        self.qwen_memory = self.base_path / "qwen_memory.json"
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._initialize_memory()

    # ---- Inicializálás ----

    def _initialize_memory(self):
        """Ha nem léteznek a memória fájlok, létrehozza őket alap struktúrával.

        Meglévő fájlokat NEM írja felül — csak hiány esetén hoz létre.
        """
        if not self.memory_file.exists():
            active_memory = {
                "timestamp": datetime.now().isoformat(),
                "repositories": {},
            }
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(active_memory, f, indent=2, ensure_ascii=False)
        if not self.qwen_memory.exists():
            qwen_mem = {
                "timestamp": datetime.now().isoformat(),
                "analyses": {},
            }
            with open(self.qwen_memory, "w", encoding="utf-8") as f:
                json.dump(qwen_mem, f, indent=2, ensure_ascii=False)


    # ---- Aktív memória (active_memory.json) ----

    def add_repository_memory(self, repo_name: str, repo_data: dict) -> bool:
        """Hozzáadja/frissíti a repo bejegyzést az active_memory.json
        'repositories' szekciójában.

        Args:
            repo_name: a repó neve (pl. 'debugger-mcp-main')
            repo_data: a repó adatai (dict)

        Returns:
            True sikeres írás esetén, False hiba esetén.
        """
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                memory = json.load(f)
            memory.setdefault("repositories", {})
            memory["repositories"][repo_name] = {
                "timestamp": datetime.now().isoformat(),
                "data": repo_data,
            }
            memory["timestamp"] = datetime.now().isoformat()
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(memory, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"HIBA repository memória: {e}")
            return False

    # ---- Qwen memória (qwen_memory.json) ----

    def add_qwen_analysis(self, repo_name: str, analysis: str, patterns: list) -> bool:
        """Hozzáadja/frissíti a Qwen elemzést a qwen_memory.json
        'analyses' szekciójában.

        Args:
            repo_name: a repó neve
            analysis: az elemzés szövege
            patterns: a felismert minták listája

        Returns:
            True sikeres írás esetén, False hiba esetén.
        """
        try:
            with open(self.qwen_memory, "r", encoding="utf-8") as f:
                qwen_mem = json.load(f)
            qwen_mem.setdefault("analyses", {})
            qwen_mem["analyses"][repo_name] = {
                "timestamp": datetime.now().isoformat(),
                "analysis": analysis,
                "patterns": patterns,
            }
            qwen_mem["timestamp"] = datetime.now().isoformat()
            with open(self.qwen_memory, "w", encoding="utf-8") as f:
                json.dump(qwen_mem, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"HIBA Qwen elemzés: {e}")
            return False
    # ---- Lekérdezés ----

    def get_context_for_qwen(self, repo_name: str) -> dict:
        """Visszaadja az adott repo Qwen-elemzését, valamint az összes
        eddig elemzett repo nevét — ez szolgál kontextusként egy újabb
        Qwen futtatás előtt.

        Args:
            repo_name: a kontextushoz lekérdezett repo neve

        Returns:
            {
              "current_repo": {...},   # az adott repo elemzése (vagy {})
              "all_repos": [...]        # az összes eddig elemzett repo neve
            }
            Hiba esetén: {"error": "<üzenet>"}
        """
        try:
            with open(self.qwen_memory, "r", encoding="utf-8") as f:
                qwen_mem = json.load(f)
            analyses = qwen_mem.get("analyses", {})
            return {
                "current_repo": analyses.get(repo_name, {}),
                "all_repos": list(analyses.keys()),
            }
        except Exception as e:
            return {"error": str(e)}

    def get_memory_summary(self) -> dict:
        """Visszaadja a memória-állapot összegzését.

        Kezeli a meglévő active_memory.json strukturált alakját is,
        amelyben a 'snippets' (lista) és 'code_snippets' (dict) kulcsok
        egyaránt előfordulhatnak.

        Returns:
            {
              "mcp_memory": {
                "total_snippets": <int>,
                "total_repos": <int>,
                "last_update": <iso-ts>
              },
              "qwen_memory": {
                "total_analyses": <int>,
                "last_update": <iso-ts>
              }
            }
            Hiba esetén: {"error": "<üzenet>"}
        """
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                memory = json.load(f)
            with open(self.qwen_memory, "r", encoding="utf-8") as f:
                qwen_mem = json.load(f)

            # A 'snippets' lehet lista; a 'code_snippets' dict.
            snippets = memory.get("snippets", [])
            total_snippets = len(snippets)
            code_snippets = memory.get("code_snippets", {})
            if isinstance(code_snippets, dict):
                total_snippets += len(code_snippets)

            return {
                "mcp_memory": {
                    "total_snippets": total_snippets,
                    "total_repos": len(memory.get("repositories", {})),
                    "last_update": memory.get("timestamp", "unknown"),
                },
                "qwen_memory": {
                    "total_analyses": len(qwen_mem.get("analyses", {})),
                    "last_update": qwen_mem.get("timestamp", "unknown"),
                },
            }
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    manager = MemoryManager()
    print("✅ Gyakorlati Memória Rendszer MŰKÖDIK!")
    manager.add_qwen_analysis("debugger-mcp-main", "Node.js debugger", ["DAP", "Node.js"])
    manager.add_repository_memory("debugger-mcp-main", {"type": "debugger"})
    print(manager.get_memory_summary())



