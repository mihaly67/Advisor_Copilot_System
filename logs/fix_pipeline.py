#!/usr/bin/env python3
"""Generate v110_volbar_pipeline.py with correct syntax"""
TARGET = '/data/dev/projects/z-ai-copilot/src/v110_volbar_pipeline.py'

# Read the generated file and fix typos
with open('/data/mcp_server/logs/v110_volbar_pipeline.py', 'r') as f:
    code = f.read()

# Fix typos
code = code.replace('   (fig.add_trace', '    fig.add_trace')
code = code.replace('Ftextposition', 'textposition')
code = code.replace("with open(os.path.join(DOCS),'volbar_results.json'),'w') as f:",
                     "with open(os.path.join(DOCS,'volbar_results.json'),'w') as f:")

with open(TARGET, 'w') as f:
    f.write(code)

import py_compile
py_compile.compile(TARGET, doraise=True)
print(f'Syntax OK! Written to {TARGET} ({len(code)} bytes)')
