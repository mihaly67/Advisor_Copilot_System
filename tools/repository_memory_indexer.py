#!/usr/bin/env python3
from datetime import datetime
import os

def repository_memory_indexer(repository_path, memory_stage):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if not os.path.isdir(repository_path):
        return "HIBA: Path nem letezik"
    repos = []
    for item in os.listdir(repository_path):
        path = os.path.join(repository_path, item)
        if os.path.isdir(path) and not item.startswith("."):
