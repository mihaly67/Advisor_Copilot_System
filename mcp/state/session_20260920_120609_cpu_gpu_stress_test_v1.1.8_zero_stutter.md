# Session: cpu_gpu_stress_test_v1.1.8_zero_stutter
*Időbélyeg: 2026-09-20T12:06:09.708424*

# Session: cpu_gpu_stress_test_v1.1.8_zero_stutter
*Időbélyeg: 2026-09-20*

## CPU & GPU Stress Test v1.1.8 — PRIME offload buffer stuttering javítás — BEFEJEZVE

### Probléma (v1.1.7):
- Felhasználó jelentette: "Minden minimumra állítva a kép 2 másodpercre megáll, de magas az FPS"
- Diagnózis: **PRIME offload buffer másolás**
  - P4000 (GPU 0, display_active=Disabled) renderelte a benchmark-ot
  - P2000 (GPU 1, display_active=Enabled, X server ezen fut) jelenítette meg
  - A `__NV_PRIME_RENDER_OFFLOAD=1` miatt a renderelt képkockákat a P4000 VRAM-jából a P2000 VRAM-jába kellett másolni
  - Ez a másolás okozta a 2 másodperces stutteringet magas FPS mellett

### Megoldás (v1.1.8):
1. **PRIME offload eltávolítása**
   - `__NV_PRIME_RENDER_OFFLOAD=1` → ELTÁVOLÍTVA (csak kommentben szerepel)
   - `__GLX_VENDOR_LIBRARY_NAME=nvidia` → ELTÁVOLÍTVA
   - Ezek Intel+NVIDIA hibrid rendszerekhez valók, nem két NVIDIA GPU-hoz!

2. **VSync kikapcsolása driver szinten**
   - `__GL_SYNC_TO_VBLANK=0` — SyncToVBlank kikapcsolása (korábban 1 volt)
   - `__GL_MAX_FRAME_ALLOWED=0` — FPS limit feloldása

3. **Megjelenítő GPU detektálás** (`detect_display_gpu()` metódus)
   - `glxinfo` OpenGL renderer string alapján
   - A GUI-ban a GPU lista címkézve: `[Megjelenítő GPU]` vagy `[Renderelő GPU]`
   - A felhasználó látja melyik GPU-n fog renderelődni a benchmark

4. **CUDA_VISIBLE_DEVICES megmarad**
   - Csak CUDA monitorozás (nvidia-smi) céljából
   - Az OpenGL renderelő GPU-t nem befolyásolja

### Env változók (v1.1.8):
- `CUDA_VISIBLE_DEVICES=<index>` — CUDA monitorozás
- `__GL_SYNC_TO_VBLANK=0` — driver VSync OFF (zero stutter)
- `__GL_MAX_FRAME_ALLOWED=0` — FPS limit feloldva

### Hardver tények:
- GPU 0 (P4000): display_active=Disabled, nincs kijelző csatlakoztatva
- GPU 1 (P2000): display_active=Enabled, X server ezen fut
- OpenGL renderer: Quadro P2000/PCIe/SSE2
- NVIDIA SyncToVBlank: 1 volt (most a benchmark-ban 0-ra állítva)

### Deb csomag:
- `/home/Jules/HardverMonitor_dev/mx-cpu-gpu-stress-test_1.1.8_all.deb`
- Depends: python3, python3-pyqt5, mesa-utils (glxinfo függőség)
- Telepítve: 1.1.7 → 1.1.8

### Megjegyzés:
- Ha a P4000-et akarod stressz-tesztelni OpenGL-lel, a kijelzőt a P4000-re kell kötni
- A CUDA_VISIBLE_DEVICES csak a CUDA-alapú monitorozást irányítja, nem az OpenGL renderelést