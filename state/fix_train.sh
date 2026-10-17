#!/usr/bin/env bash
# V10 tanitas wrapper
cd /data/dev/projects/z-ai-copilot

# Eloszor megjavijuk a train scriptet
python3 << 'PYEOF'
lines = open('src/train_lgbm_v2.py').readlines()
new_lines = []
for i, line in enumerate(lines):
    # 1. DATA_PATH sort atirjuk default-ta
    if "DATA_PATH = os.path.join(BASE, 'Master_csv', 'processed'," in line:
        new_lines.append("DATA_PATH_DEFAULT = os.path.join(BASE, 'Master_csv', 'processed',\n")
        # kovetkezo sort is beolvassuk es egybeolvasztjuk
        continue
    # 2. Ha ez az "adaptive.csv" folyosato sor es nem DATA_PATH_DEFAULT utan van
    if "labeled_dollar_bars_adaptive.csv')" in line and i > 0 and 'DATA_PATH_DEFAULT' not in new_lines[-1] if new_lines else True:
        if new_lines and 'DATA_PATH_DEFAULT' not in new_lines[-1]:
            new_lines.append(line)
            continue
    # 3. Ha mar lejartuk DATA_PATH_DEFAULT-ot, hozzafuzzuk a csv-t
    if new_lines and 'DATA_PATH_DEFAULT' in new_lines[-1] and "labeled_dollar_bars_adaptive.csv')" in line:
        # egybeolvasszuk
        new_lines[-1] = "DATA_PATH_DEFAULT = os.path.join(BASE, 'Master_csv', 'processed', 'labeled_dollar_bars_adaptive.csv')\n"
        continue
    new_lines.append(line)

open('src/train_lgbm_v2.py', 'w').writelines(new_lines)
print('STEP1 DONE')
PYEOF

# Ellenorzes
python3 -c "import ast; ast.parse(open('src/train_lgbm_v2.py').read()); print('SYNTAX OK')"
