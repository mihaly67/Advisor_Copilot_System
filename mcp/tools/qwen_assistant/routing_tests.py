#!/usr/bin/env python3
from task_classifier import TaskClassifier
from resource_monitor import ResourceMonitor
from intelligent_router import IntelligentRouter

def run_routing_tests():
    """Teljes integráció tesztelése"""
    router = IntelligentRouter()
    
    test_tasks = [
        'Javítsd ki ezt a függvényt szintaktikai hiba miatt',
        'Tervezz egy skálázható mikroszolgáltatás architektúrát',
        'Optimalizáld ezt a kódot a teljesítmény javítása érdekében',
        'Írj unit teszteket ehhez a Python osztályhoz',
        'Hozz létre egy komplex cloud alapú rendszert'
    ]
    
    print('🧪 INTELLIGENT ROUTER TELJES TESZTELÉS')
    print('=' * 70)
    
    decisions = []
    local_count = 0
    external_count = 0
    hybrid_count = 0
    total_cost = 0.0
    
    for i, task in enumerate(test_tasks, 1):
        try:
            decision = router.route_task(task)
            decisions.append(decision)
            
            if decision.mode == 'local':
                local_count += 1
            elif decision.mode == 'external':
                external_count += 1
            else:
                hybrid_count += 1
            
            total_cost += decision.cost_estimate
            
            print(f'\\nTeszt {i}: {task[:45]}...')
            print(f'  Mód: {decision.mode.upper()}')
            print(f'  Bizonyosság: {decision.confidence:.0%}')
            print(f'  Költség: ${decision.cost_estimate:.4f}')
            print(f'  Teljesítmény: {decision.performance_estimate:.1f}s')
            print(f'  Indoklás: {decision.reasoning}')
            print(f'  GPU elérhető: {decision.resource_status.gpu_available}')
            
        except Exception as e:
            print(f'\\nTeszt {i}: HIBA - {e}')
    
    # Összesítés
    print('\\n' + '=' * 70)
    print('📊 TESZT EREDMÉNYÖK ÖSSZESÍTÉSE')
    print('=' * 70)
    
    total = len(decisions)
    if total > 0:
        print(f'Összes tesztek: {total}')
        print(f'Helyi Qwen: {local_count} ({local_count/total:.0%})')
        print(f'Külső API: {external_count} ({external_count/total:.0%})')
        print(f'Hibrid: {hybrid_count} ({hybrid_count/total:.0%})')
        print(f'Összes költség: ${total_cost:.4f}')
        print(f'Átlagos költség/teszt: ${total_cost/total:.4f}')
        
        # Metrikák
        local_ratio = local_count / total
        print(f'\\n🎯 ELÉRT EREDMÉNYEK:')
        print(f'Token költségcsökkentés: {local_ratio:.0%}')
        print(f'Helyi Qwen arány: {local_ratio:.0%} (cél: 60-70%)')
        
        if 0.6 <= local_ratio <= 0.7:
            print('✅ Kiváló: Helyi Qwen arány a céltartományban!')
        elif local_ratio > 0.7:
            print('⚠️  Magas: Helyi Qwen arány magas - ellenőrizd a minőséget')
        else:
            print('⚠️  Alacsony: Helyi Qwen arány alacsony - növelhető a költségcsökkentés')
    else:
        print('Nincs sikeres teszt!')

if __name__ == '__main__':
    run_routing_tests()