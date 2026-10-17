#!/usr/bin/env python3
"""
REAL-TIME PYQT6 MONITORING DASHBOARD
Token tracking and cost monitoring for Qwen routing system
"""
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
from collections import defaultdict

try:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                                 QHBoxLayout, QWidget, QLabel, QProgressBar,
                                 QTextEdit, QGroupBox, QPushButton, QFrame,
                                 QGridLayout)
    from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal
    from PyQt6.QtGui import QFont
except ImportError:
    print("❌ PyQt6 not installed. Install with: pip install PyQt6")
    sys.exit(1)

class TokenTracker:
    """Track token usage and costs for different models"""
    
    def __init__(self):
        self.session_start = time.time()
        self.tokens = {
            'P4000': {'input': 0, 'output': 0, 'total': 0},
            'P2000': {'input': 0, 'output': 0, 'total': 0}, 
            'Z.ai Basic': {'input': 0, 'output': 0, 'total': 0},
            'Z.ai Premium': {'input': 0, 'output': 0, 'total': 0}
        }
        self.costs = {
            'P4000': 0.0,
            'P2000': 0.0,
            'Z.ai Basic': 0.0,
            'Z.ai Premium': 0.0
        }
        self.request_count = {
            'P4000': 0,
            'P2000': 0, 
            'Z.ai Basic': 0,
            'Z.ai Premium': 0
        }
        self.cost_rates = {
            'P4000': 0.0,
            'P2000': 0.0,
            'Z.ai Basic': 0.0005,
            'Z.ai Premium': 0.002
        }
        self.latency_history = []
        self.activity_log = []
        
        # GPU status
        self.p4000_available = False
        self.p2000_available = False
        self.check_gpu_status()
        
    def check_gpu_status(self):
        """Check GPU availability and memory"""
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.used', 
                                   '--format=csv,noheader'], 
                                  capture_output=True, text=True, timeout=5)
            gpus = result.stdout.strip().split('\n')
            
            for gpu_info in gpus:
                if 'P4000' in gpu_info:
                    self.p4000_available = True
                elif 'P2000' in gpu_info:
                    self.p2000_available = True
        except Exception as e:
            print(f"GPU check failed: {e}")
    
    def track_tokens(self, model, input_tokens, output_tokens, latency=0.0):
        """Track token usage for a specific model"""
        if model in self.tokens:
            self.tokens[model]['input'] += input_tokens
            self.tokens[model]['output'] += output_tokens
            self.tokens[model]['total'] += input_tokens + output_tokens
            self.request_count[model] += 1
            
            # Calculate cost for API models
            if 'Z.ai' in model:
                total_tokens = input_tokens + output_tokens
                cost = (total_tokens / 1000) * self.cost_rates[model]
                self.costs[model] += cost
            
            # Track latency
class RoutingSimulator(QThread):
    """Simulate routing requests for testing"""
    request_processed = pyqtSignal(dict)
    
    def __init__(self, token_tracker):
        super().__init__()
        self.token_tracker = token_tracker
        self.running = False
        self.test_tasks = [
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
        
        self.complexity_keywords = {
            'architecture': 0.3, 'design': 0.2, 'system': 0.25,
            'algorithm': 0.2, 'optimization': 0.15,
            'microservice': 0.25, 'cloud': 0.2, 'api': 0.15,
            'database': 0.15, 'security': 0.2, 'authentication': 0.15,
            'deployment': 0.15, 'testing': 0.1, 'integration': 0.15
        }
    
    def calculate_complexity(self, task):
        """Calculate task complexity score"""
        score = 0.0
        for kw, weight in self.complexity_keywords.items():
            if kw.lower() in task.lower():
                score += weight
        
        token_factor = min(len(task.split()) / 1000, 0.3)
        score += token_factor
        return min(score, 1.0)
    
    def route_task(self, task):
        """Route task to appropriate model"""
        complexity = self.calculate_complexity(task)
        estimated_tokens = len(task.split()) * 1.3
        
        if complexity < 0.45 and estimated_tokens <= 8000:
            model = 'P4000'
            cost = 0.0
            reasoning = 'Simple task, P4000 local'
        elif complexity < 0.85 and estimated_tokens <= 10000:
            if self.token_tracker.p2000_available:
                model = 'P2000'
                cost = 0.0
                reasoning = 'Medium complexity, P2000 local'
            else:
                model = 'Z.ai Basic'
                cost = (estimated_tokens / 1000) * self.token_tracker.cost_rates['Z.ai Basic']
                reasoning = 'Medium complexity, Z.ai Basic (P2000 unavailable)'
        else:
            model = 'Z.ai Premium'
            cost = (estimated_tokens / 1000) * self.token_tracker.cost_rates['Z.ai Premium']
            reasoning = 'High complexity, Z.ai Premium'
        
        return model, complexity, estimated_tokens, cost, reasoning
    
    def run(self):
        """Run routing simulation"""
        self.running = True
        task_index = 0
        
        while self.running:
            if task_index >= len(self.test_tasks):
                task_index = 0  # Loop through tasks
            
            task = self.test_tasks[task_index]
            start_time = time.time()
            
            # Route task
            model, complexity, estimated_tokens, cost, reasoning = self.route_task(task)
            
            # Simulate processing
            time.sleep(0.1)
class MonitoringDashboard(QMainWindow):
    """Main monitoring dashboard window"""
    
    def __init__(self):
        super().__init__()
        self.token_tracker = TokenTracker()
        self.routing_simulator = RoutingSimulator(self.token_tracker)
        
        self.setup_ui()
        self.connect_signals()
        self.start_monitoring()
    
    def setup_ui(self):
        """Setup the UI layout"""
        self.setWindowTitle('🚀 QWEN ROUTING MONITOR - TOKEN TRACKING DASHBOARD')
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("QMainWindow { background-color: #ecf0f1; }")
        
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Main layout
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(10)
        
        # Header
        header = self.create_header()
        layout.addWidget(header)
        
        # Token dashboard
        token_dashboard = self.create_token_dashboard()
        layout.addWidget(token_dashboard)
        
        # Distribution monitoring
        distribution = self.create_distribution_monitor()
        layout.addWidget(distribution)
        
        # Statistics and log layout
        stats_log_layout = QHBoxLayout()
        
        # Session statistics
        stats = self.create_statistics_panel()
        stats_log_layout.addWidget(stats, 1)
        
        # Live log
        log_panel = self.create_log_panel()
        stats_log_layout.addWidget(log_panel, 1)
        
        layout.addLayout(stats_log_layout, 1)
        
        # Control buttons
        controls = self.create_controls()
        layout.addWidget(controls)
    
    def create_token_dashboard(self):
        """Create token usage dashboard"""
        dashboard = QGroupBox('💰 TOKEN USAGE & COST TRACKING')
        dashboard.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #34495e;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        layout = QGridLayout(dashboard)
        
        # Model panels
        models = ['P4000', 'P2000', 'Z.ai Basic', 'Z.ai Premium']
        colors = ['#27ae60', '#3498db', '#e67e22', '#e74c3c']
        
        for i, (model, color) in enumerate(zip(models, colors)):
            panel = self.create_model_panel(model, color)
            layout.addWidget(panel, 0, i, 2, 1)
        
        # Total panel
        total_panel = self.create_total_panel()
        layout.addWidget(total_panel, 0, 4, 2, 2)
        
        return dashboard
    
    def create_model_panel(self, model, color):
        """Create individual model panel"""
        panel = QFrame()
        panel.setStyleSheet(f"background-color: {color}; color: white; padding: 15px; border-radius: 10px;")
        layout = QVBoxLayout(panel)
        
        # Model name
        model_label = QLabel(model)
        model_label.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        model_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(model_label)
        
        # Token count
        token_label = QLabel(f'{self.token_tracker.tokens[model]["total"]} tokens')
        token_label.setFont(QFont('Arial', 12))
        token_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        setattr(self, f'{model.replace(".", "_")}_token_label', token_label)
        layout.addWidget(token_label)
        
        # Cost
        cost = self.token_tracker.costs[model]
        cost_text = 'FREE' if cost == 0 else f'${cost:.4f}'
        cost_label = QLabel(cost_text)
        cost_label.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        cost_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        setattr(self, f'{model.replace(".", "_")}_cost_label', cost_label)
        layout.addWidget(cost_label)
        
        # Request count
        req_label = QLabel(f'{self.token_tracker.request_count[model]} requests')
        req_label.setFont(QFont('Arial', 10))
        req_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        setattr(self, f'{model.replace(".", "_")}_req_label', req_label)
        layout.addWidget(req_label)
        
        return panel
    
    def create_total_panel(self):
        """Create total summary panel"""
        panel = QFrame()
        panel.setStyleSheet("background-color: #8e44ad; color: white; padding: 15px; border-radius: 10px;")
        layout = QVBoxLayout(panel)
        
        # Title
        title = QLabel('TOTAL COST')
        title.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Total cost
        total_cost = self.token_tracker.get_total_cost()
        cost_label = QLabel(f'${total_cost:.4f}')
    def create_distribution_monitor(self):
        """Create distribution monitoring panel"""
        distribution = QGroupBox('📊 ROUTING DISTRIBUTION (70/20/10 TARGETS)')
        distribution.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #34495e;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        layout = QVBoxLayout(distribution)
        
        # Create progress bars for each model
        models = ['P4000', 'P2000', 'Z.ai Premium']
        targets = {'P4000': 70, 'P2000': 20, 'Z.ai Premium': 10}
        
        for model in models:
            model_layout = QHBoxLayout()
            
            # Label
            label = QLabel(f'{model}:')
            label.setMinimumWidth(100)
            model_layout.addWidget(label)
            
            # Progress bar
            progress = QProgressBar()
            progress.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #34495e;
                    border-radius: 5px;
                    text-align: center;
                    height: 25px;
                }
                QProgressBar::chunk {
                    background-color: #3498db;
                    border-radius: 3px;
                }
            """)
            progress.setMinimum(0)
            progress.setMaximum(100)
            progress.setValue(0)
            setattr(self, f'{model.replace(".", "_")}_progress', progress)
            model_layout.addWidget(progress)
            
            # Percentage label
            pct_label = QLabel('0%')
            pct_label.setMinimumWidth(50)
            setattr(self, f'{model.replace(".", "_")}_pct_label', pct_label)
            model_layout.addWidget(pct_label)
    def create_statistics_panel(self):
        """Create session statistics panel"""
        stats = QGroupBox('📈 SESSION STATISTICS')
        stats.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #34495e;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        layout = QGridLayout(stats)
        
        # Session duration
        layout.addWidget(QLabel('Session Duration:'), 0, 0)
        self.duration_label = QLabel('00:00:00')
        layout.addWidget(self.duration_label, 0, 1)
        
        # Total requests
        layout.addWidget(QLabel('Total Requests:'), 1, 0)
        self.total_requests_label = QLabel('0')
        layout.addWidget(self.total_requests_label, 1, 1)
        
        # Total tokens
        layout.addWidget(QLabel('Total Tokens:'), 2, 0)
        self.total_tokens_label = QLabel('0')
        layout.addWidget(self.total_tokens_label, 2, 1)
        
        # Average latency
        layout.addWidget(QLabel('Avg Latency:'), 3, 0)
        self.avg_latency_label = QLabel('0.000s')
        layout.addWidget(self.avg_latency_label, 3, 1)
        
        # Throughput
        layout.addWidget(QLabel('Throughput:'), 4, 0)
        self.throughput_label = QLabel('0.0 req/s')
        layout.addWidget(self.throughput_label, 4, 1)
        
        # 70/20/10 evaluation
        layout.addWidget(QLabel('70/20/10 Status:'), 5, 0)
        self.targets_status_label = QLabel('Evaluating...')
        layout.addWidget(self.targets_status_label, 5, 1)
        
        return stats
    
    def create_log_panel(self):
        """Create live log panel"""
        log = QGroupBox('📝 LIVE ACTIVITY LOG')
        log.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #34495e;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        layout = QVBoxLayout(log)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: #2c3e50; color: #ecf0f1; font-family: monospace;")
        layout.addWidget(self.log_text)
        
        return log
    
    def create_controls(self):
        """Create control buttons"""
        controls = QHBoxLayout()
        
        # Start button
        start_btn = QPushButton('🚀 Start Monitoring')
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        start_btn.clicked.connect(self.start_routing)
        controls.addWidget(start_btn)
        
        # Stop button
        stop_btn = QPushButton('⏹️ Stop Monitoring')
        stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
    def connect_signals(self):
        """Connect signals and slots"""
        self.routing_simulator.request_processed.connect(self.on_request_processed)
    
    def start_monitoring(self):
        """Start monitoring timers"""
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self.update_session_time)
        self.session_timer.start(1000)
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_dashboard)
        self.update_timer.start(1000)
    
    def start_routing(self):
        """Start routing simulation"""
        if not self.routing_simulator.isRunning():
            self.routing_simulator.start()
            self.log_text.append("🚀 Routing simulation started...")
    
    def stop_routing(self):
        """Stop routing simulation"""
        if self.routing_simulator.isRunning():
            self.routing_simulator.running = False
            self.routing_simulator.wait()
            self.log_text.append("⏹️ Routing simulation stopped...")
    
    def clear_session(self):
        """Clear session data"""
        self.token_tracker = TokenTracker()
        self.routing_simulator.token_tracker = self.token_tracker
        self.log_text.clear()
        self.update_dashboard()
        self.log_text.append("🗑️ Session cleared...")
    def on_request_processed(self, request_data):
        """Handle request processed signal"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        cost_display = 'FREE' if request_data['cost'] == 0 else f'${request_data["cost"]:.4f}'
        
        log_entry = f"[{timestamp}] {request_data['model']} | {request_data['total_tokens']:.0f} tokens | {cost_display}"
        log_entry += f"\n          Task: {request_data['task'][:40]}..."
        log_entry += f"\n          Complexity: {request_data['complexity']:.2f} | Latency: {request_data['latency']:.3f}s"
        
        self.log_text.append(log_entry)
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_session_time(self):
        """Update session time display"""
        duration = int(time.time() - self.token_tracker.session_start)
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60
        
        time_str = f'{hours:02d}:{minutes:02d}:{seconds:02d}'
        self.session_time_label.setText(f'Session: {time_str}')
        self.duration_label.setText(time_str)
    
    def update_dashboard(self):
        """Update all dashboard elements"""
        models = ['P4000', 'P2000', 'Z.ai Basic', 'Z.ai Premium']
        
        for model in models:
            token_label = getattr(self, f'{model.replace(".", "_")}_token_label')
            token_label.setText(f'{self.token_tracker.tokens[model]["total"]} tokens')
            
            cost_label = getattr(self, f'{model.replace(".", "_")}_cost_label')
            cost = self.token_tracker.costs[model]
            cost_text = 'FREE' if cost == 0 else f'${cost:.4f}'
            cost_label.setText(cost_text)
            
            req_label = getattr(self, f'{model.replace(".", "_")}_req_label')
            req_label.setText(f'{self.token_tracker.request_count[model]} requests')
        
        total_cost = self.token_tracker.get_total_cost()
        self.total_cost_label.setText(f'${total_cost:.4f}')
        
        savings, savings_pct = self.token_tracker.get_cost_savings()
        self.savings_label.setText(f'Saved: ${savings:.4f} ({savings_pct:.1f}%)')
        
    def update_targets_status(self):
        """Update 70/20/10 targets status"""
        total_requests = sum(self.token_tracker.request_count.values())
        if total_requests == 0:
            self.targets_status_label.setText('Evaluating...')
            return
        
        targets = {'P4000': 70, 'P2000': 20, 'Z.ai Premium': 10}
        met_count = 0
        
        for model, target in targets.items():
            count = self.token_tracker.request_count[model]
            actual = (count / total_requests) * 100
            deviation = abs(actual - target)
            
            if deviation < 15:
                met_count += 1
        
        if met_count == 3:
            self.targets_status_label.setText('✅ ALL GOALS MET')
            self.targets_status_label.setStyleSheet('color: #27ae60; font-weight: bold;')
        elif met_count == 2:
            self.targets_status_label.setText('⚠️ 2/3 GOALS MET')
            self.targets_status_label.setStyleSheet('color: #f39c12; font-weight: bold;')
        else:
            self.targets_status_label.setText('❌ GOALS NOT MET')
            self.targets_status_label.setStyleSheet('color: #e74c3c; font-weight: bold;')

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    dashboard = MonitoringDashboard()
    dashboard.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
        total_requests = sum(self.token_tracker.request_count.values())
        if total_requests > 0:
            models_for_dist = ['P4000', 'P2000', 'Z.ai Premium']
            for model in models_for_dist:
                progress = getattr(self, f'{model.replace(".", "_")}_progress')
                pct_label = getattr(self, f'{model.replace(".", "_")}_pct_label')
                
                count = self.token_tracker.request_count[model]
                pct = (count / total_requests) * 100
                progress.setValue(int(pct))
                pct_label.setText(f'{pct:.0f}%')
        
        self.total_requests_label.setText(str(total_requests))
        self.total_tokens_label.setText(str(self.token_tracker.get_total_tokens()))
        self.avg_latency_label.setText(f'{self.token_tracker.get_avg_latency():.3f}s')
        
        duration = time.time() - self.token_tracker.session_start
        throughput = total_requests / duration if duration > 0 else 0
        self.throughput_label.setText(f'{throughput:.2f} req/s')
        
        self.update_targets_status()
    
    def export_session(self):
        """Export session data"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'/data/mcp_server/data/session_export_{timestamp}.json'
        
        session_data = {
            'timestamp': timestamp,
            'session_duration': time.time() - self.token_tracker.session_start,
            'tokens': self.token_tracker.tokens,
            'costs': self.token_tracker.costs,
            'request_count': self.token_tracker.request_count,
            'activity_log': self.token_tracker.activity_log
        }
        
        try:
            Path('/data/mcp_server/data').mkdir(parents=True, exist_ok=True)
            with open(filename, 'w') as f:
                json.dump(session_data, f, indent=2)
            self.log_text.append(f"💾 Session exported to {filename}")
        except Exception as e:
            self.log_text.append(f"❌ Export failed: {e}")
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #922b21;
            }
        """)
        stop_btn.clicked.connect(self.stop_routing)
        controls.addWidget(stop_btn)
        
        # Clear button
        clear_btn = QPushButton('🗑️ Clear Session')
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d68910;
            }
            QPushButton:pressed {
                background-color: #b9770e;
            }
        """)
        clear_btn.clicked.connect(self.clear_session)
        controls.addWidget(clear_btn)
        
        # Export button
        export_btn = QPushButton('💾 Export Session')
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        export_btn.clicked.connect(self.export_session)
        controls.addWidget(export_btn)
        
        controls.addStretch()
        
        return controls
            
            # Target label
            target_label = QLabel(f'(target: {targets[model]}%)')
            model_layout.addWidget(target_label)
            
            layout.addLayout(model_layout)
        
        return distribution
        cost_label.setFont(QFont('Arial', 20, QFont.Weight.Bold))
        cost_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.total_cost_label = cost_label
        layout.addWidget(cost_label)
        
        # Savings
        savings, savings_pct = self.token_tracker.get_cost_savings()
        savings_label = QLabel(f'Saved: ${savings:.4f} ({savings_pct:.1f}%)')
        savings_label.setFont(QFont('Arial', 12))
        savings_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.savings_label = savings_label
        layout.addWidget(savings_label)
        
        return panel
    def create_header(self):
        """Create header panel"""
        header = QFrame()
        header.setStyleSheet("background-color: #2c3e50; color: white; padding: 10px; border-radius: 5px;")
        layout = QHBoxLayout(header)
        
        # Title
        title = QLabel('🚀 QWEN ROUTING MONITOR')
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        layout.addStretch()
        
        # GPU status
        gpu_status = QLabel(f'GPU: P4000 {"✅" if self.token_tracker.p4000_available else "❌"} | P2000 {"✅" if self.token_tracker.p2000_available else "❌"}')
        layout.addWidget(gpu_status)
        
        # Session time
        self.session_time_label = QLabel('Session: 00:00:00')
        layout.addWidget(self.session_time_label)
        
        return header
            latency = time.time() - start_time
            
            # Track tokens (simulate token usage)
            input_tokens = estimated_tokens * 0.6  # 60% input, 40% output
            output_tokens = estimated_tokens * 0.4
            
            self.token_tracker.track_tokens(model, input_tokens, output_tokens, latency)
            
            # Emit signal for GUI update
            request_data = {
                'task': task,
                'model': model,
                'complexity': complexity,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens,
                'cost': cost,
                'latency': latency,
                'reasoning': reasoning
            }
            
            self.request_processed.emit(request_data)
            
            task_index += 1
            time.sleep(2)  # Wait 2 seconds between requests
            if latency > 0:
                self.latency_history.append(latency)
                if len(self.latency_history) > 100:
                    self.latency_history.pop(0)
            
            # Log activity
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.activity_log.append({
                'timestamp': timestamp,
                'model': model,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens,
                'cost': self.costs[model] if 'Z.ai' in model else 0.0,
                'latency': latency
            })
    
    def get_total_cost(self):
        """Get total session cost"""
        return sum(self.costs.values())
    
    def get_total_tokens(self):
        """Get total tokens processed"""
        return sum(self.tokens[model]['total'] for model in self.tokens)
    
    def get_cost_savings(self):
        """Calculate cost savings compared to using Z.ai Premium for everything"""
        total_tokens = self.get_total_tokens()
        cost_without_routing = (total_tokens / 1000) * 0.002  # Premium only
        cost_with_routing = self.get_total_cost()
        savings = cost_without_routing - cost_with_routing
        savings_pct = (savings / cost_without_routing * 100) if cost_without_routing > 0 else 0
        return savings, savings_pct
    
    def get_avg_latency(self):
        """Get average request latency"""
        if not self.latency_history:
            return 0.0
        return sum(self.latency_history) / len(self.latency_history)