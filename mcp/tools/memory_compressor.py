#!/usr/bin/env python3
"""
Memory Compressor
==================

Compresses memory entries to save context space. Strategies:
  1. Deduplicate: remove identical/near-identical entries
  2. Summarize: replace verbose entries with concise summaries
  3. Archive: move old, low-relevance entries to cold storage
  4. Merge: combine related entries into one
"""

import json
import hashlib
from datetime import datetime, timezone


class MemoryCompressor:
    def __init__(self, memory_file='/data/mcp_server/context/active_memory.json',
                 archive_file='/data/mcp_server/context/archive_memory.json'):
        self.memory_file = memory_file
        self.archive_file = archive_file
        with open(self.memory_file, 'r') as f:
            self.memory = json.load(f)
        self.archive = self._load_archive()

    def _load_archive(self):
        try:
            with open(self.archive_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {'archived_entries': []}

    def _save_archive(self):
        with open(self.archive_file, 'w') as f:
            json.dump(self.archive, f, ensure_ascii=False, indent=2)

    def _entry_hash(self, entry):
        """Stable hash for dedup."""
        # Use only stable fields
        stable = json.dumps({k: v for k, v in sorted(entry.items())
                            if k in ('repo_name', 'repo_path', 'description',
                                     'confidence', 'recommendation')},
                           sort_keys=True, ensure_ascii=False)
        return hashlib.md5(stable.encode()).hexdigest()

    def deduplicate(self, section_name, entries):
        """Remove exact duplicates from a dict/list section."""
        if isinstance(entries, dict):
            seen = {}
            removed = 0
            for key, entry in entries.items():
                h = self._entry_hash(entry) if isinstance(entry, dict) else str(entry)
                if h in seen:
                    removed += 1
                    continue
                seen[h] = (key, entry)
            new_section = {k: v for k, v in seen.values()}
            return new_section, removed
        elif isinstance(entries, list):
            seen = []
            removed = 0
            for entry in entries:
                h = self._entry_hash(entry) if isinstance(entry, dict) else str(entry)
                if any(h == self._entry_hash(e) if isinstance(e, dict) else h == str(e) for e in seen):
                    removed += 1
                    continue
                seen.append(entry)
            return seen, removed
        return entries, 0

    def summarize_entry(self, entry, max_chars=200):
        """Create a compact summary of an entry."""
        desc = entry.get('description', '')
        if len(desc) <= max_chars:
            return entry  # Already compact
        summary = desc[:max_chars-3] + '...'
        new_entry = dict(entry)
        new_entry['description'] = summary
        new_entry['_summarized'] = True
        return new_entry

    def archive_old(self, section_name, entries, max_age_days=30):
        """Move entries older than max_age_days to archive."""
        now = datetime.now(timezone.utc)
        if isinstance(entries, dict):
            keep = {}
            archived = []
            for key, entry in entries.items():
                if not isinstance(entry, dict):
                    keep[key] = entry
                    continue
                ts_str = entry.get('timestamp', '')
                if not ts_str:
                    keep[key] = entry
                    continue
                try:
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    age = (now - ts).days
                    if age > max_age_days:
                        archived.append({'section': section_name, 'key': key, 'entry': entry})
                    else:
                        keep[key] = entry
                except (ValueError, TypeError):
                    keep[key] = entry
            return keep, archived
        return entries, []

    def compress(self, max_age_days=30, max_desc_chars=200):
        """Run full compression pipeline."""
        stats = {'deduplicated': 0, 'archived': 0, 'summarized': 0}

        for section_name in list(self.memory.keys()):
            section = self.memory[section_name]
            if not isinstance(section, (dict, list)):
                continue

            # 1. Deduplicate
            section, removed = self.deduplicate(section_name, section)
            stats['deduplicated'] += removed

            # 2. Summarize verbose descriptions
            if isinstance(section, dict):
                for key, entry in section.items():
                    if isinstance(entry, dict) and 'description' in entry:
                        new = self.summarize_entry(entry, max_desc_chars)
                        if new.get('_summarized'):
                            section[key] = new
                            stats['summarized'] += 1
            elif isinstance(section, list):
                for i, entry in enumerate(section):
                    if isinstance(entry, dict) and 'description' in entry:
                        new = self.summarize_entry(entry, max_desc_chars)
                        if new.get('_summarized'):
                            section[i] = new
                            stats['summarized'] += 1

            # 3. Archive old
            section, archived = self.archive_old(section_name, section, max_age_days)
            self.archive['archived_entries'].extend(archived)
            stats['archived'] += len(archived)

            self.memory[section_name] = section

        # Save
        with open(self.memory_file, 'w') as f:
            json.dump(self.memory, f, ensure_ascii=False, indent=2)
        self._save_archive()

        return stats


if __name__ == '__main__':
    mc = MemoryCompressor()
    stats = mc.compress(max_age_days=60, max_desc_chars=200)
    print('Memória tömörítés eredménye:')
    print(f"  Deduplicált: {stats['deduplicated']}")
    print(f"  Archivált (60+ napos): {stats['archived']}")
    print(f"  Tömörített leírások: {stats['summarized']}")
    print('\n✅ Memória optimalizálva!')
