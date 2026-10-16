#!/usr/bin/env python3
"""
REAL-TIME MONITORING CONSOLE FOR QWEN ROUTING SYSTEM
Based on original token optimization plans
"""
import time
import subprocess
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict

@dataclass
class RequestMetrics:
    task_id: str
    task: str
    timestamp: float
    model_used: str
    gpu_used: str
    complexity: float
    estimated_tokens: int
    actual_tokens: int
    cost: float
    latency: float
    status: str

class RealtimeMonitor:
    def __init__(self):
        self.requests = []
        self.session_start = time.time()
        self.total_cost = 0.0
        self.total_tokens = 0
        self.routing_counts = defaultdict(int)
        self.cost_accumulator = defaultdict(float)
        
        # Cost configuration
        self.COSTS = {
            'P4000': 0.0,
            'P2000': 0.0,
            'Z.ai Basic': 0.0005,
            'Z.ai Premium': 0.002
        }
        
        # Complexity keywords
        self.complexity_keywords = {
            'architecture': 0.3, 'design': 0.2, 'system': 0.25,
            'algorithm': 0.2, 'optimization': 0.15,
            'microservice': 0.25, 'cloud': 0.2, 'api': 0.15,
            'database': 0.15, 'security': 0.2, 'authentication': 0.15,
            'deployment': 0.15, 'testing': 0.1, 'integration': 0.15
        }
        
        # GPU availability check
        self.p2000_available = False
        self.p2000_vram = 0
        self.check_gpu_availability()
        
        print("✅ REAL-TIME MONITOR CONSOLE INITIALIZED")
        self.print_gpu_info()
        print("=" * 70)
    
    def check_gpu_availability(self):
        """Check P2000 GPU availability"""
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', 
                                   '--format=csv,noheader'], 
                                  capture_output=True, text=True, timeout=5)
            gpus = result.stdout.strip().split('\n')
            
            for gpu_info in gpus:
                if 'P2000' in gpu_info:
                    self.p2000_available = True
                    parts = gpu_info.split(', ')
                    self.p2000_vram = int(parts[1].split()[0])
                    break
        except Exception as e:
            print(f"⚠️  GPU check failed: {e}")
            self.p2000_available = False
    
    def print_gpu_info(self):
        """Display GPU information"""
        print(f"🖥️  P2000 GPU: {'✓ Available' if self.p2000_available else '✗ Not Available'}")
        if self.p2000_available:
            print(f"   VRAM: {self.p2000_vram}MiB")
        print("💰 Cost Rates:")
        for model, cost in self.COSTS.items():
            status = "FREE" if cost == 0 else f"${cost}/1K tokens"
            print(f"   {model}: {status}")
    
    
    def process_request(self, task: str, task_id: str = None) -> RequestMetrics:
        """Process a request and track metrics in real-time"""
        start_time = time.time()
        if task_id is None:
            task_id = f"req_{len(self.requests) + 1}"
        
        # Route task
        model, gpu, cost, complexity, estimated_tokens, reasoning = self.route_task(task)
        
        # Simulate processing (in real system, this would be actual API call)
        time.sleep(0.1)  # Simulate processing time
        
        # Calculate actual tokens and latency
        actual_tokens = estimated_tokens  # In real system, would count actual tokens
        latency = time.time() - start_time
        
        # Create metrics record
        metrics = RequestMetrics(
            task_id=task_id,
            task=task,
            timestamp=time.time(),
            model_used=model,
            gpu_used=gpu,
            complexity=complexity,
            estimated_tokens=int(estimated_tokens),
            actual_tokens=int(actual_tokens),
            cost=cost,
            latency=latency,
            status='completed'
        )
        
        # Update aggregates
        self.requests.append(metrics)
        self.total_cost += cost
        self.total_tokens += actual_tokens
        self.routing_counts[model] += 1
        self.cost_accumulator[model] += cost
        
        # Print real-time info
        self.print_request_info(metrics, reasoning)
        
        return metrics
    def print_session_summary(self):
        """Print session summary"""
        session_duration = time.time() - self.session_start
        
        print("=" * 70)
        print("📊 SESSION SUMMARY")
        print("=" * 70)
        print(f"Duration: {session_duration:.2f}s | Requests: {len(self.requests)}")
        print(f"Total Cost: ${self.total_cost:.4f} | Total Tokens: {self.total_tokens:.0f}")
        
        print("\n📈 ROUTING DISTRIBUTION:")
        for model, count in sorted(self.routing_counts.items()):
            pct = (count / len(self.requests) * 100) if self.requests else 0
            cost = self.cost_accumulator[model]
            print(f"  {model}: {count} requests ({pct:.1f}%) | ${cost:.4f}")
        
        print(f"\n⚡ PERFORMANCE:")
        avg_latency = sum(r.latency for r in self.requests) / len(self.requests) if self.requests else 0
        throughput = len(self.requests) / session_duration if session_duration > 0 else 0
        print(f"  Avg Latency: {avg_latency:.3f}s | Throughput: {throughput:.2f} req/s")
        
        # Cost savings calculation
        cost_without_routing = (self.total_tokens / 1000) * 0.002  # Premium only
        savings = cost_without_routing - self.total_cost
        savings_pct = (savings / cost_without_routing * 100) if cost_without_routing > 0 else 0
        
        print(f"\n💰 COST SAVINGS:")
        print(f"  Without routing: ${cost_without_routing:.4f}")
        print(f"  With routing: ${self.total_cost:.4f}")
        print(f"  Saved: ${savings:.4f} ({savings_pct:.1f}%)")
        
        # 70/20/10 evaluation
        print(f"\n🎯 70/20/10 DISTRIBUTION EVALUATION:")
        targets = {'P4000': 70, 'P2000': 20, 'Z.ai Premium': 10}
        met_count = 0
        
        for model, count in self.routing_counts.items():
            if model in targets:
                pct = (count / len(self.requests) * 100) if self.requests else 0
                target = targets[model]
                deviation = abs(pct - target)
                met = deviation < 15
                if met:
                    met_count += 1
                status = "✓ MET" if met else "✗ NOT MET"
                print(f"  {model}: {pct:.1f}% (target: {target}%) | {status}")
        
        overall = met_count == len(targets)
        print(f"\n  Overall: {'✓ ALL GOALS MET' if overall else '✗ SOME GOALS NOT MET'}")
        
        print("=" * 70)

def run_realtime_test():
    """Run a real-time test with monitoring"""
    monitor = RealtimeMonitor()
    
    # Test tasks simulating real usage
    test_tasks = [
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
        'Design scalable microservice architecture',
        'Optimize code for better performance',
        'Create complex cloud-based system',
        'Implement load balancing algorithm',
        'Analyze system architecture design',
        'Design distributed system architecture'
    ]
    
    print("🚀 STARTING REAL-TIME MONITORING TEST")
    print("=" * 70)
    
    # Process each request with real-time monitoring
    for i, task in enumerate(test_tasks, 1):
        task_id = f"req_{i:03d}"
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Processing request {i}/{len(test_tasks)}")
        monitor.process_request(task, task_id)
        time.sleep(0.2)  # Small delay between requests
    
    # Print final summary
    monitor.print_session_summary()

if __name__ == '__main__':
    run_realtime_test()
            status='completed'
        )
        
        # Update aggregates
        self.requests.append(metrics)
        self.total_cost += cost
        self.total_tokens += actual_tokens
        self.routing_counts[model] += 1
        self.cost_accumulator[model] += cost
        
        # Print real-time info
        self.print_request_info(metrics, reasoning)
        
        return metrics
    
    def print_request_info(self, metrics: RequestMetrics, reasoning: str):
        """Print real-time request information"""
        timestamp = datetime.fromtimestamp(metrics.timestamp).strftime('%H:%M:%S')
        cost_display = "FREE" if metrics.cost == 0 else f"${metrics.cost:.4f}"
        
        print(f"[{timestamp}] {metrics.task_id}: {metrics.model_used} | {cost_display}")
        print(f"          Task: {metrics.task[:40]}{'...' if len(metrics.task) > 40 else ''}")
        print(f"          Complexity: {metrics.complexity:.2f} | Tokens: {metrics.actual_tokens} | Latency: {metrics.latency:.3f}s")
        print(f"          Reasoning: {reasoning}")
        print(f"          Running Total: ${self.total_cost:.4f} | {self.total_tokens:.0f} tokens")
        print("-" * 70)
    def calculate_complexity(self, task: str) -> float:
        """Calculate task complexity score"""
        score = 0.0
        for kw, weight in self.complexity_keywords.items():
            if kw.lower() in task.lower():
                score += weight
        
        token_factor = min(len(task.split()) / 1000, 0.3)
        score += token_factor
        return min(score, 1.0)
    
    def route_task(self, task: str) -> tuple:
        """Route task to appropriate model and return routing info"""
        complexity = self.calculate_complexity(task)
        estimated_tokens = len(task.split()) * 1.3
        
        if complexity < 0.45 and estimated_tokens <= 8000:
            model = 'P4000'
            gpu = 'P4000 Local'
            cost = 0.0
            reasoning = 'Simple task, P4000 local sufficient'
        elif complexity < 0.85 and estimated_tokens <= 10000:
            if self.p2000_available:
                model = 'P2000'
                gpu = 'P2000 Local'
                cost = 0.0
                reasoning = 'Medium complexity, P2000 weak model'
            else:
                model = 'Z.ai Basic'
                gpu = 'Z.ai API'
                cost = (estimated_tokens / 1000) * self.COSTS['Z.ai Basic']
                reasoning = 'Medium complexity, Z.ai Basic (P2000 unavailable)'
        else:
            model = 'Z.ai Premium'
            gpu = 'Z.ai API'
            cost = (estimated_tokens / 1000) * self.COSTS['Z.ai Premium']
            reasoning = 'High complexity, Z.ai Premium required'
        
        return model, gpu, cost, complexity, estimated_tokens, reasoning