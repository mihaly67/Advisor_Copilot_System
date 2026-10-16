#!/usr/bin/env python3
import sys
import time
sys.path.insert(0, '/data/mcp_server/tools/qwen_assistant')

from qwen_integrated_system import QwenIntegratedSystem

def run_comprehensive_test():
    system = QwenIntegratedSystem()
    
    # Valósabb tesztkészlet complexity szerint elosztva
    test_tasks = [
        # Low complexity (70%)
        'Fix syntax error in this function',
        'Write unit tests for Python class',
        'Debug memory leak in application',
        'Refactor legacy codebase',
        'Create REST API endpoint',
        'Implement caching mechanism',
        'Design database schema',
        'Write documentation for API',
        'Fix CSS layout issue',
        'Optimize SQL query performance',
        'Implement authentication system',
        'Create automated deployment pipeline',
        'Analyze security vulnerabilities',
        'Write integration tests',
        
        # Medium complexity (20%)
        'Design scalable microservice architecture',
        'Optimize code for better performance',
        'Create complex cloud-based system',
        'Implement load balancing algorithm',
        
        # High complexity (10%)
        'Analyze system architecture design',
        'Design distributed system architecture'
    ]
    
    print('=' * 70)
    print('COMPREHENSIVE TEST - 19 TASK')
    print('=' * 70)
    
    start_time = time.time()
    results = system.analyze_batch(test_tasks, verbose=True)
    end_time = time.time()
    
    print('\n' + '=' * 70)
    print('FINAL RESULTS')
    print('=' * 70)
    print(f'Total execution time: {end_time - start_time:.3f}s')
    print(f'Tasks processed: {results["total_tasks"]}')
    print(f'Total cost: ${results["total_cost"]:.4f}')
    print(f'Total token savings: {results["total_savings"]} token')
    
    # 70/20/10 Analysis
    model_dist = results['model_distribution']
    local_pct = model_dist.get('Qwen/Qwen2.5-Coder-7B', 0) / len(test_tasks) * 100
    weak_pct = model_dist.get('qwen/qwen-2.5-7b', 0) / len(test_tasks) * 100
    strong_pct = model_dist.get('gpt-4o', 0) / len(test_tasks) * 100
    
    print('\n' + '=' * 70)
    print('ROUTING DISTRIBUTION')
    print('=' * 70)
    print(f'Helyi Qwen (free): {local_pct:.0f}% | Cél: 70%')
    print(f'Weak model ($0.0005): {weak_pct:.0f}% | Cél: 20%')
    print(f'Strong model ($0.002): {strong_pct:.0f}% | Cél: 10%')
    
    # Complexity Analysis
    comp_dist = results['complexity_distribution']
    print('\n' + '=' * 70)
    print('COMPLEXITY DISTRIBUTION')
    print('=' * 70)
    print(f'Low complexity: {comp_dist["low"]}/{len(test_tasks)} ({comp_dist["low"]/len(test_tasks)*100:.0f}%)')
    print(f'Medium complexity: {comp_dist["medium"]}/{len(test_tasks)} ({comp_dist["medium"]/len(test_tasks)*100:.0f}%)')
    print(f'High complexity: {comp_dist["high"]}/{len(test_tasks)} ({comp_dist["high"]/len(test_tasks)*100:.0f}%)')
    
    # Cost Analysis
    print('\n' + '=' * 70)
    print('COST ANALYSIS')
    print('=' * 70)
    avg_tokens = 1000
    cost_no_routing = len(test_tasks) * avg_tokens * 0.002 / 1000
    savings_pct = (1 - results['total_cost'] / max(cost_no_routing, 0.001)) * 100
    print(f'Estimated cost without routing: ${cost_no_routing:.4f}')
    print(f'Actual cost with routing: ${results["total_cost"]:.4f}')
    print(f'Cost reduction: {savings_pct:.0f}%')
    
    # P4000 Performance
    print('\n' + '=' * 70)
    print('P4000 PERFORMANCE METRICS')
    print('=' * 70)
    local_tasks = model_dist.get('Qwen/Qwen2.5-Coder-7B', 0)
    print(f'Local Qwen tasks (P4000): {local_tasks}')
    print(f'External API tasks: {len(test_tasks) - local_tasks}')
    print(f'Average processing time: {(end_time - start_time)/len(test_tasks):.3f}s/task')
    
    # Goal Achievement
    print('\n' + '=' * 70)
    print('GOAL ACHIEVEMENT (70/20/10)')
    print('=' * 70)
    local_met = abs(local_pct - 70) < 15
    weak_met = abs(weak_pct - 20) < 10
    strong_met = abs(strong_pct - 10) < 5
    
    print(f'70% local target: {"✓ MET" if local_met else "✗ NOT MET"} ({local_pct:.0f}%)')
    print(f'20% weak target: {"✓ MET" if weak_met else "✗ NOT MET"} ({weak_pct:.0f}%)')
    print(f'10% strong target: {"✓ MET" if strong_met else "✗ NOT MET"} ({strong_pct:.0f}%)')
    
    overall = local_met and weak_met and strong_met
    print(f'\nOverall: {"✓ ALL GOALS MET" if overall else "✗ GOALS NOT MET"}')
    
    return results

if __name__ == '__main__':
    run_comprehensive_test()