import lightgbm as lgb
import numpy as np
import time

X = np.random.rand(1000, 10)
y = np.random.randint(0, 3, 1000)

print("Testing GPU mode...")
try:
    clf = lgb.LGBMClassifier(
        n_estimators=10,
        device='gpu',
        gpu_platform_id=0,
        gpu_device_id=0,
        n_jobs=1,
        verbose=-1
    )
    t0 = time.time()
    clf.fit(X, y)
    t1 = time.time()
    print(f"GPU OK! Time: {t1-t0:.3f}s")
except Exception as e:
    print(f"GPU FAILED: {e}")
    print("Falling back to CPU...")
    clf = lgb.LGBMClassifier(n_estimators=10, n_jobs=1, verbose=-1)
    t0 = time.time()
    clf.fit(X, y)
    t1 = time.time()
    print(f"CPU OK! Time: {t1-t0:.3f}s")
