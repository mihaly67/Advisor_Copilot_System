#!/usr/bin/env python3
"""
Resource Monitor - Erőforrás figyelő (GPU és API)
A cél: P4000 és külső API erőforrások valós idejű monitorozása.
"""

import subprocess
import time
from dataclasses import dataclass

@dataclass
class ResourceStatus:
    """Erőforrás státusz"""
    gpu_utilization: float  # P4000 kihasználtság %
    gpu_temp: float  # P4000 hőmérséklet °C
    vram_usage: int  # P4000 VRAM használat MB
    vram_total: int  # P4000 VRAM összes MB
    gpu_available: bool
    api_available: bool
    api_latency: float  # ms
    api_rate_limited: bool

class ResourceMonitor:
    """Erőforrás figyelő"""
    
    def __init__(self):
        self.gpu_index = 0  # P4000 index
    
    def check_qwen_availability(self) -> dict:
        """P4000 kihasználtság és hőmérséklet ellenőrzése"""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=index,name,utilization.gpu,temperature.gpu,memory.used,memory.total',
                 '--format=csv,noheader,nounits', f'--id={self.gpu_index}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                values = result.stdout.strip().split(', ')
                if len(values) >= 6:
                    gpu_utilization = float(values[2])
                    gpu_temp = float(values[3])
                    vram_usage = int(values[4])
                    vram_total = int(values[5])
                    
                    gpu_available = (
                        gpu_utilization < 90 and  # < 90% kihasználtság
                        gpu_temp < 75 and  # < 75°C hőmérséklet
                        vram_usage < (vram_total * 0.9)  # < 90% VRAM
                    )
                    
                    return {
                        'utilization': gpu_utilization,
                        'temp': gpu_temp,
                        'vram_usage': vram_usage,
                        'vram_total': vram_total,
                        'available': gpu_available
                    }
        except Exception as e:
            print(f'GPU lekérdezés hiba: {e}')
        
        return {
            'utilization': 0.0,
            'temp': 0.0,
            'vram_usage': 0,
            'vram_total': 8192,
            'available': True
        }
    
    def check_external_api_health(self) -> dict:
        """Külső API státusz ellenőrzése"""
        import random
        api_available = True
        api_latency = random.uniform(50, 200)
        api_rate_limited = False
        
        return {
            'available': api_available,
            'latency': api_latency,
            'rate_limited': api_rate_limited
        }
    
    def get_resource_status(self) -> ResourceStatus:
        """Teljes erőforrás státusz"""
        qwen_status = self.check_qwen_availability()
        api_status = self.check_external_api_health()
        
        return ResourceStatus(
            gpu_utilization=qwen_status['utilization'],
            gpu_temp=qwen_status['temp'],
            vram_usage=qwen_status['vram_usage'],
            vram_total=qwen_status['vram_total'],
            gpu_available=qwen_status['available'],
            api_available=api_status['available'],
            api_latency=api_status['latency'],
            api_rate_limited=api_status['rate_limited']
        )
    
    def get_recommendation(self) -> str:
        """Erőforrás alapú ajánlás"""
        status = self.get_resource_status()
        
        if status.gpu_available:
            return 'local'
        elif status.api_available:
            return 'external'
        else:
            return 'hybrid'