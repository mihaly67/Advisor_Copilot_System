#!/usr/bin/env python3
import sys
sys.path.insert(0, '/data/mcp_server/tools/qwen_assistant')

from qwen_weak_router import QwenWeakRouter
from token_optimizer import TokenOptimizer

class QwenIntegratedSystem:
    def __init__(self):
        self.router = QwenWeakRouter()
        self.optimizer = TokenOptimizer()
        
        # Token cost data (küldés Qwenre)
        self.COSTS = {
            'local_qwen': 0.0,
            'weak_model': 0.0005,
            'strong_model': 0.002
        }
        
        # Token limit (P4000)
        self.TOKEN_LIMITS = {
            'local_qwen': 8000,
            'weak_model': 16000,
            'strong_model': 128000
        }
        
        print('Qwen Integrated System inicializálva')
    
    def process_task(self, task: str, verbose: bool = False) -> dict:
        if verbose:
            print(f'\nTask feldolgozás: {task[:50]}...')
            print('=' * 70)
        
        relevant_context = self.optimizer.get_relevant_context(task)
        token_savings = self.optimizer.estimate_token_savings(task)
        
        if verbose:
            print(f'Token optimalizáció:')
            print(f'   Tokencsökkentés: {token_savings} token')
            print(f'   Kontextus: {relevant_context[:50] if relevant_context else "Nincs releváns kontextus"}...')
        
        routing = self.router.route_task(task)
        
        if verbose:
            print(f'\nRouting:')
            print(f'   Complexity: {routing.complexity:.2f}')
            print(f'   Model: {routing.recommended_model}')
            print(f'   Költség: ${routing.cost_estimate:.4f}')
            print(f'   Indoklás: {routing.reasoning}')
        
        result = self.execute_task(task, routing)
        
        self.optimizer.add_entry(task, result, routing.estimated_tokens)
        
        return {
            'task': task,
            'model': routing.recommended_model,
            'cost': routing.cost_estimate,
            'token_savings': token_savings,
            'result': result,
            'complexity': routing.complexity,
            'estimated_tokens': routing.estimated_tokens
        }
    
    def execute_task(self, task: str, routing) -> str:
        if 'local_qwen' in routing.recommended_model:
            return f'Helyi Qwen eredmény: {task[:30]}...'
        elif 'weak_model' in routing.recommended_model:
            return f'Weak model eredmény: {task[:30]}...'
        else:
            return f'Strong model eredmény: {task[:30]}...'
    
    def analyze_batch(self, tasks: list, verbose: bool = False) -> dict:
        results = []
        total_cost = 0.0
        total_savings = 0
        model_counts = {}
        complexity_distribution = {'low': 0, 'medium': 0, 'high': 0}
        
        for task in tasks:
            result = self.process_task(task, verbose=verbose)
            results.append(result)
            total_cost += result['cost']
            total_savings += result['token_savings']
            
            model = result['model']
            model_counts[model] = model_counts.get(model, 0) + 1
            
            complexity = result['complexity']
            if complexity < 0.45:
                complexity_distribution['low'] += 1
            elif complexity < 0.85:
                complexity_distribution['medium'] += 1
            else:
                complexity_distribution['high'] += 1
        
        if verbose:
            print('\n' + '=' * 70)
            print('BATCH EREDMENYOK')
            print('=' * 70)
            print(f'Osszes tasks: {len(results)}')
            print(f'Osszes költség: ${total_cost:.4f}')
            print(f'Osszes tokencsökkentés: {total_savings} token')
            print(f'\nModel eloszlás:')
            for model, count in model_counts.items():
                percentage = (count / len(results)) * 100
                print(f'  {model}: {count} ({percentage:.0f}%)')
            
            print(f'\nComplexity eloszlás:')
            for level, count in complexity_distribution.items():
                percentage = (count / len(results)) * 100
                print(f'  {level}: {count} ({percentage:.0f}%)')
        
        return {
            'total_tasks': len(results),
            'total_cost': total_cost,
            'total_savings': total_savings,
            'model_distribution': model_counts,
            'complexity_distribution': complexity_distribution,
            'results': results
        }
    
    def get_model_costs(self) -> dict:
        """ Költségstruktúria """
        return self.COSTS
    
    def get_token_limits(self) -> dict:
        """ Token limit (P4000) """
        return self.TOKEN_LIMITS
    
    def get_stats(self) -> dict:
        """ System statisztika """
        return {
            'total_entries': len(self.optimizer.entries),
            'max_entries': self.optimizer.max_entries,
            'model_costs': self.COSTS,
            'token_limits': self.TOKEN_LIMITS
        }

if __name__ == '__main__':
    system = QwenIntegratedSystem()
    
    test_tasks = [
        'Fix syntax error in this function',
        'Design scalable microservice architecture',
        'Optimize code for better performance',
        'Write unit tests for Python class',
        'Create complex cloud-based system',
        'Analyze system architecture design',
        'Implement load balancing algorithm'
    ]
    
    print('\n' + '=' * 70)
    print('SYSTEM INFORMÁCIÓK')
    print('=' * 70)
    stats = system.get_stats()
    print(f'Memória bejegyzések: {stats["total_entries"]}/{stats["max_entries"]}')
    print(f'Model költségek: {stats["model_costs"]}')
    print(f'Token limitek: {stats["token_limits"]}')
    
    print('\n' + '=' * 70)
    print('BATCH FELDOLGOZÁS')
    print('=' * 70)
    results = system.analyze_batch(test_tasks, verbose=True)
    print(f'\nBatch feldolgozás kész: {results["total_tasks"]} task')
    print(f'Összes költség: ${results["total_cost"]:.4f}')
    
    # 70/20/10 cél vizsgálata
    print('\n' + '=' * 70)
    print('CEL ÉRTÉKELÉS (70/20/10)')
    print('=' * 70)
    model_dist = results['model_distribution']
    local_pct = model_dist.get('Qwen/Qwen2.5-Coder-7B', 0) / len(test_tasks) * 100
    weak_pct = model_dist.get('Qwen/Qwen2.5-Coder-7B', 0) / len(test_tasks) * 100
    strong_pct = model_dist.get('Z.ai Premium Model', 0) / len(test_tasks) * 100
    
    print(f'Helyi Qwen: {local_pct:.0f}% (cél: 70%)')
    print(f'Weak model: {weak_pct:.0f}% (cél: 20%)')
    print(f'Strong model: {strong_pct:.0f}% (cél: 10%)')
    
    cost_savings = (1 - results['total_cost'] / 0.01) * 100
    print(f'\nBecsült költségcsökkentés: {cost_savings:.0f}%')