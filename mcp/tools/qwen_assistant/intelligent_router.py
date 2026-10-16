#!/usr/bin/env python3
from dataclasses import dataclass
from task_classifier import TaskClassifier, TaskClassification
from resource_monitor import ResourceMonitor, ResourceStatus

@dataclass
class RoutingDecision:
    task: str
    mode: str
    confidence: float
    reasoning: str
    cost_estimate: float
    performance_estimate: float
    resource_status: ResourceStatus

class IntelligentRouter:
    def __init__(self):
        self.task_classifier = TaskClassifier()
        self.resource_monitor = ResourceMonitor()
        self.LOCAL_COST = 0.0
        self.EXTERNAL_COST_PER_1K_TOKENS = 0.002
    
    def route_task(self, task: str) -> RoutingDecision:
        task_classification = self.task_classifier.classify_task(task)
        resource_status = self.resource_monitor.get_resource_status()
        cost_estimate = self.estimate_cost(task, task_classification.recommended_mode)
        performance_estimate = self.estimate_performance(task, task_classification.recommended_mode)
        final_mode = self.intelligent_routing(task_classification, resource_status)
        
        return RoutingDecision(
            task=task,
            mode=final_mode,
            confidence=task_classification.confidence,
            reasoning=f"{task_classification.reasoning}. GPU: {resource_status.gpu_available}",
            cost_estimate=cost_estimate,
            performance_estimate=performance_estimate,
            resource_status=resource_status
        )
    
    def intelligent_routing(self, task_classification: TaskClassification, resource_status: ResourceStatus) -> str:
        if resource_status.gpu_available and task_classification.is_local_capable:
            return 'local'
        elif not resource_status.gpu_available and task_classification.recommended_mode == 'external':
            return 'external'
        elif task_classification.recommended_mode == 'hybrid':
            return 'hybrid'
        else:
            return 'local'
    
    def estimate_cost(self, task: str, mode: str) -> float:
        estimated_tokens = self.task_classifier.estimate_tokens(task)
        if mode == 'local':
            return self.LOCAL_COST
        elif mode == 'external':
            return (estimated_tokens / 1000) * self.EXTERNAL_COST_PER_1K_TOKENS
        else:
            return (estimated_tokens / 1000) * self.EXTERNAL_COST_PER_1K_TOKENS * 0.5
    
    def estimate_performance(self, task: str, mode: str) -> float:
        if mode == 'local':
            return 0.1
        elif mode == 'external':
            return 0.2
        else:
            return 0.15

if __name__ == '__main__':
    router = IntelligentRouter()
    test_tasks = [
        'Javítsd ki ezt a függvényt szintaktikai hiba miatt',
        'Tervezz egy skálázható mikroszolgáltatás architektúrát',
        'Optimalizáld ezt a kódot a teljesítmény javítása érdekében'
    ]
    
    print('🚀 Intelligent Router Tesztelése:')
    for i, task in enumerate(test_tasks, 1):
        decision = router.route_task(task)
        print(f'{i}. {task[:40]}... → {decision.mode.upper()} (${decision.cost_estimate:.4f}, {decision.performance_estimate:.1f}s)')