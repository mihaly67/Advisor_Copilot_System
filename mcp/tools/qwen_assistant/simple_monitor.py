#!/usr/bin/env python3
print("REAL-TIME MONITORING CONSOLE")
print("=" * 70)
import subprocess
import time
from datetime import datetime

# GPU check
result = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], capture_output=True, text=True)
gpus = result.stdout.strip().split("\n")
print("AVAILABLE GPUS:")
for gpu in gpus:
    print(f"  - {gpu}")
print("=" * 70)

# Test tasks
test_tasks = [
    'Fix syntax error in this function',
    'Write unit tests for Python class',
    'Design scalable microservice architecture',
    'Create complex cloud-based system',
    'Implement load balancing algorithm'
]

print(f"Starting real-time monitoring with {len(test_tasks)} tasks...")
print("=" * 70)

# Simple routing test
keywords = {'architecture':0.3, 'design':0.2, 'system':0.25, 'microservice':0.25, 'cloud':0.2, 'api':0.15, 'optimization':0.15}
counts = {'P4000': 0, 'P2000': 0, 'Z.ai Premium': 0}
total_cost = 0.0
total_tokens = 0

for i, task in enumerate(test_tasks, 1):
    start_time = time.time()
    task_id = f"req_{i:03d}"
    
    # Calculate complexity
    score = 0.0
    for k, v in keywords.items():
        if k.lower() in task.lower():
            score += v
    score = min(score + min(len(task.split()) / 1000, 0.3), 1.0)
    
    # Routing decision
    if score < 0.45:
        model = "P4000"
        cost = 0.0
        reasoning = "Simple task, P4000 local"
    elif score < 0.85:
        model = "P2000"
        cost = 0.0
        reasoning = "Medium complexity, P2000 local"
    else:
        model = "Z.ai Premium"
        cost = (len(task.split()) * 1.3 / 1000) * 0.002
        reasoning = "High complexity, Z.ai Premium"
    
    # Simulate processing
    time.sleep(0.1)
    latency = time.time() - start_time
    tokens = len(task.split()) * 1.3
    
    # Update aggregates
    counts[model] += 1
    total_cost += cost
    total_tokens += tokens
    
    # Real-time output
    timestamp = datetime.now().strftime('%H:%M:%S')
    cost_display = "FREE" if cost == 0 else f"${cost:.4f}"
    
    print(f"[{timestamp}] {task_id}: {model} | {cost_display}")
    print(f"          Task: {task[:35]}{'...' if len(task) > 35 else ''}")
    print(f"          Complexity: {score:.2f} | Tokens: {tokens:.0f} | Latency: {latency:.3f}s")
    print(f"          Reasoning: {reasoning}")
    print(f"          Running Total: ${total_cost:.4f} | {total_tokens:.0f} tokens")
    print("-" * 70)

# Final summary
print("=" * 70)
print("SESSION SUMMARY")
print("=" * 70)
print(f"Requests processed: {len(test_tasks)}")
print(f"Total cost: ${total_cost:.4f}")
print(f"Total tokens: {total_tokens:.0f}")

print("\nROUTING DISTRIBUTION:")
for model, count in counts.items():
    pct = (count / len(test_tasks)) * 100
    print(f"  {model}: {pct:.0f}% ({count}/{len(test_tasks)})")

# Cost savings
cost_without_routing = (total_tokens / 1000) * 0.002
savings = cost_without_routing - total_cost
savings_pct = (savings / cost_without_routing * 100) if cost_without_routing > 0 else 0

print(f"\nCOST SAVINGS:")
print(f"  Without routing: ${cost_without_routing:.4f}")
print(f"  With routing: ${total_cost:.4f}")
print(f"  Saved: ${savings:.4f} ({savings_pct:.1f}%)")

# 70/20/10 evaluation
print(f"\n70/20/10 DISTRIBUTION EVALUATION:")
targets = {'P4000': 70, 'P2000': 20, 'Z.ai Premium': 10}
met_count = 0

for model, count in counts.items():
    if model in targets:
        pct = (count / len(test_tasks)) * 100
        target = targets[model]
        deviation = abs(pct - target)
        met = deviation < 15
        if met:
            met_count += 1
        status = "MET" if met else "NOT MET"
        print(f"  {model}: {pct:.0f}% (target: {target}%) | {status}")

overall = met_count == len(targets)
print(f"\n  Overall: {'ALL GOALS MET' if overall else 'SOME GOALS NOT MET'}")

print("=" * 70)
print("TEST KÉSZ!")
print("=" * 70)