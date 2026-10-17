# Session: cpu_gpu_stress_test_v1.1.7_multi_gpu
*Időbélyeg: 2026-09-20T11:49:47.812819*

# Session: cpu_gpu_stress_test_v1.1.7_multi_gpu
*Időbélyeg: 2026-09-20*

## CPU & GPU Stress Test v1.1.7 — Multi-GPU + Preset bővítés — BEFEJEZVE

### Új funkciók (v1.1.6 → v1.1.7):

1. **GPU enumeráció hardver szinten** (`enumerate_gpus()` metódus)
   - `nvidia-smi --query-gpu=index,name,uuid,pci.bus_id,pci.device_id,memory.total,driver_version --format=csv,noheader,nounits`
   - Visszatér: GPU dict lista [{index, name, uuid, pci_bus_id, pci_device_id, vram, driver}]
   - Timeout 10s, hibakezelés (TimeoutExpired, FileNotFoundError, ValueError)

2. **GPU választó QComboBox** (`gpu_selector_combo`)
   - Dinamikusan feltöltve a felismert GPU-kkal
   - Formátum: `[index] Név (VRAM MiB) — PCI bus ID`
   - Induláskor lefuttatja az enumerációt

3. **Teszt nehézségi fok (preset) választó** — 2 → 4 preset
   - Basic (MSAA 0 — alap terhelés)
   - Medium (MSAA 2 — közepes terhelés)
   - High (MSAA 4 — erős terhelés)
   - Extreme (MSAA 8 — maximális terhelés)

4. **QProcessEnvironment GPU specifikus beállítás**
   - `CUDA_VISIBLE_DEVICES=<index>` — CUDA számítás a kiválasztott GPU-n
   - `__NV_PRIME_RENDER_OFFLOAD=1` — PRIME offload
   - `__GLX_VENDOR_LIBRARY_NAME=nvidia` — NVIDIA GLX

5. **Konzol kimenet bővítve**
   - GPU: [index] Név
   - Preset: Név (MSAA x) | Fullscreen
   - Env: CUDA_VISIBLE_DEVICES, __NV_PRIME_RENDER_OFFLOAD

### Hardverazonosítók (AGENTS.md):
- **GPU 0**: Quadro P4000 — PCI 02:00.0 — 10de:1bb1 — 8192 MiB — GPU-5c9224fc...
- **GPU 1**: Quadro P2000 — PCI 03:00.0 — 10de:1c30 — 5120 MiB — GPU-01093e11...
- **CPU**: Intel Xeon E5-2673 v4 (20 mag/40 szál)
- **RAM**: 64 GB DDR4
- **OS**: MX Linux 23 (Debian 12 bookworm), KDE Plasma X11
- **Driver**: 580.178.04 (NVIDIA proprietary)

### Deb csomag:
- `/home/Jules/HardverMonitor_dev/mx-cpu-gpu-stress-test_1.1.7_all.deb`
- Telepítve: `sudo dpkg -i` (1.1.6 → 1.1.7)
- Build tree: `/home/Jules/HardverMonitor_dev/build_deb/mx-cpu-gpu-stress-test_1.1.7_all/`

### Fájlok:
- `/home/Jules/HardverMonitor_dev/AGENTS.md` — hardverazonosítók (GPU + CPU + rendszer)
- `/home/Jules/HardverMonitor_dev/build_deb/mx-cpu-gpu-stress-test_1.1.7_all/usr/bin/jules_cpu_stress_test.py` — forrás

### Tesztek:
- Python szintaktika: ✅ OK
- GPU enumeráció: ✅ mindkét GPU felismerve (P4000, P2000)
- Preset parsing: ✅ 4 preset (Basic/Medium/High/Extreme)
- QProcessEnvironment: ✅ 3 env változó beállítva
- Deb telepítés: ✅ 1.1.6 → 1.1.7

### Megjegyzés:
- Két azonos driverű NVIDIA GPU esetén az OpenGL renderelést a kijelzőhöz csatlakozó GPU végzi
- A `CUDA_VISIBLE_DEVICES` a CUDA-alapú monitorozást (nvidia-smi) irányítja
- A Heaven benchmark renderelő GPU-ja a rendszer PRIME konfigurációjától függ