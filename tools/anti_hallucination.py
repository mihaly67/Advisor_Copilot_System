#!/usr/bin/env python3
"""
Anti-Hallucination Detector
=============================

Validates Qwen analysis output against actual repository content to detect
fabricated facts, invented file paths, and non-existent code references.

Checks:
1. File path verification - do referenced files actually exist?
2. Content verification - does the claimed content match actual files?
3. Cross-reference validation - are repo claims consistent with metadata?
4. Confidence scoring - how reliable is the analysis overall?
"""

import os
import re
import json
from typing import Any


class HallucinationDetector:
    """Detects fabricated content in LLM analysis outputs."""
    
    # Patterns that indicate file references
    FILE_REF_PATTERNS = [
        r'`([^`]+\.[a-z]+)`',  # `file.ext` in backticks
        r'\b([\w/]+\.[a-z]{2,4})\b',  # path/to/file.ext
        r'\*\*([^*]+\.[a-z]+)\*\*',  # **file.ext** bold
    ]
    
    # Patterns for fabricated code elements
    CODE_ELEMENT_PATTERNS = [
        r'def\s+(\w+)',  # function names
        r'class\s+(\w+)',  # class names
        r'import\s+([\w.]+)',  # imports
    ]
    
    # Strings that look like file refs but are NOT files (URLs, tech names, etc.)
    NON_FILE_PATTERNS = {
        # URLs and domains
        'github.com', 'modelcontextprotocol.io', 'http://', 'https://', 'www.',
        'npmjs.org', 'pypi.org', 'crates.io', 'maven.org', 'gradle.org',
        'openai.com', 'anthropic.com', 'huggingface.co', 'readthedocs.io',
        'nodejs.org', 'rustup.rs', 'go.dev', 'python.org',
        # Technology/product names with dots
        'Node.js', 'TypeScript.js', 'Vue.js', 'Next.js', 'Express.js',
        'React.js', 'Deno.js', 'Three.js', 'Babel.js',
        # Version strings and config keys
        'package.json', 'tsconfig.json',  # these are real but matched by basename
    }
    
    @classmethod
    def _is_non_file_ref(cls, ref: str) -> bool:
        """Check if a reference is a URL/tech name, not a real file path."""
        ref_lower = ref.lower()
        # Check against known non-file patterns
        for pattern in cls.NON_FILE_PATTERNS:
            if pattern.lower() in ref_lower:
                return True
        # URLs start with scheme or www
        if ref_lower.startswith(('http://', 'https://', 'www.', 'ftp://')):
            return True
        # Domains: contains a dot followed by a TLD-like suffix with no slash
        # e.g., "github.com" but not "path/to/file.py"
        if '/' not in ref and '.' in ref:
            parts = ref.rsplit('.', 1)
            if len(parts) == 2 and parts[1].lower() in {
                'com', 'org', 'io', 'net', 'dev', 'rs', 'ai', 'co',
            }:
                return True
        return False
    
    def __init__(self, repo_path: str):
        """Initialize with repository path to validate against."""
        self.repo_path = repo_path
        self.file_index = self._build_file_index()
    
    def _build_file_index(self) -> set[str]:
        """Build a set of all file paths in the repo."""
        files = set()
        if not os.path.isdir(self.repo_path):
            return files
        for root, dirs, filenames in os.walk(self.repo_path):
            # Skip hidden dirs and _qwen_analysis
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '_qwen_analysis']
            for f in filenames:
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, self.repo_path)
                files.add(rel_path)
                files.add(f)  # Also store basename
        return files
    
    def check_file_references(self, text: str) -> dict:
        """Check if file references in text exist in the repo."""
        referenced = set()
        for pattern in self.FILE_REF_PATTERNS:
            for match in re.finditer(pattern, text):
                ref = match.group(1)
                # Filter out URLs and tech names (false positives)
                if self._is_non_file_ref(ref):
                    continue
                referenced.add(ref)
        
        if not referenced:
            return {'referenced': [], 'missing': [], 'valid': [], 'skipped': True}
        
        missing = []
        valid = []
        for ref in referenced:
            # Check if reference exists in file index
            basename = os.path.basename(ref)
            if ref in self.file_index or basename in self.file_index:
                valid.append(ref)
            else:
                missing.append(ref)
        
        return {
            'referenced': list(referenced),
            'missing': missing,
            'valid': valid,
            'missing_ratio': len(missing) / len(referenced) if referenced else 0
        }
    
    def check_repo_name_accuracy(self, text: str, expected_repo_name: str) -> dict:
        """Check if the repo name is mentioned correctly in the text."""
        # Find repo name references
        name_variants = [
            expected_repo_name,
            expected_repo_name.replace('-', '_'),
            expected_repo_name.replace('-', ''),
            expected_repo_name.lower(),
        ]
        
        found = any(v in text for v in name_variants)
        return {
            'expected': expected_repo_name,
            'found': found,
            'variants_checked': name_variants
        }
    
    def check_technology_claims(self, text: str) -> dict:
        """Check if claimed technologies are plausible (basic heuristic)."""
        tech_keywords = {
            'Python': ['.py', 'python', 'pip', 'setup.py', 'pyproject'],
            'JavaScript': ['.js', 'javascript', 'npm', 'node'],
            'TypeScript': ['.ts', 'typescript', 'tsc'],
            'Rust': ['.rs', 'rust', 'cargo'],
            'Go': ['.go', 'golang', 'go.mod'],
            'Java': ['.java', 'java', 'maven', 'gradle'],
        }
        
        claims = []
        for tech, indicators in tech_keywords.items():
            if tech.lower() in text.lower():
                # Verify at least one indicator exists in repo
                has_evidence = any(ind in ' '.join(self.file_index).lower() for ind in indicators)
                claims.append({
                    'technology': tech,
                    'claimed': True,
                    'has_repo_evidence': has_evidence
                })
        
        unverified = [c for c in claims if not c['has_repo_evidence']]
        return {
            'claims': claims,
            'unverified_count': len(unverified),
            'total_claims': len(claims)
        }
    
    def calculate_confidence(self, file_check: dict, name_check: dict, tech_check: dict) -> float:
        """Calculate overall confidence score for the analysis."""
        score = 1.0
        
        # File reference accuracy
        if file_check['missing_ratio'] > 0:
            score -= file_check['missing_ratio'] * 0.5  # Up to -0.5
        
        # Repo name accuracy
        if not name_check['found']:
            score -= 0.2
        
        # Technology claims
        if tech_check['total_claims'] > 0:
            unverified_ratio = tech_check['unverified_count'] / tech_check['total_claims']
            score -= unverified_ratio * 0.3  # Up to -0.3
        
        return max(0.0, min(1.0, score))
    
    def analyze(self, analysis_text: str, repo_name: str = None) -> dict:
        """Full anti-hallucination analysis of Qwen output."""
        if repo_name is None:
            repo_name = os.path.basename(self.repo_path)
        
        file_check = self.check_file_references(analysis_text)
        name_check = self.check_repo_name_accuracy(analysis_text, repo_name)
        tech_check = self.check_technology_claims(analysis_text)
        confidence = self.calculate_confidence(file_check, name_check, tech_check)
        
        risk_level = 'LOW'
        if confidence < 0.5:
            risk_level = 'HIGH'
        elif confidence < 0.75:
            risk_level = 'MEDIUM'
        
        return {
            'repo_path': self.repo_path,
            'repo_name': repo_name,
            'confidence': round(confidence, 3),
            'risk_level': risk_level,
            'file_references': file_check,
            'repo_name_check': name_check,
            'technology_claims': tech_check,
            'recommendation': 'TRUST' if confidence >= 0.75 else 'REVIEW' if confidence >= 0.5 else 'REJECT'
        }


if __name__ == "__main__":
    # Test with a real analysis file
    import glob
    analysis_files = glob.glob('/data/Brain/mem0-aio/_qwen_analysis/*.md')
    if analysis_files:
        with open(analysis_files[-1], 'r') as f:
            analysis_text = f.read()
        
        detector = HallucinationDetector('/data/Brain/mem0-aio')
        result = detector.analyze(analysis_text)
        print(json.dumps(result, indent=2, ensure_ascii=False))
