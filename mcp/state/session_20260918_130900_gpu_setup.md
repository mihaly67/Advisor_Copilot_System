# Session: GPU izoláció és Qwen futtatókörnyezet

*Időbélyeg: 2026-09-18 13:09 (setup kezdete)*

## Hardver
- **GPU 0**: Quadro P4000 (UUID `GPU-5c9224fc-aadf-0efa-403a-bbb0745c46e4`), 8192 MiB VRAM, compute capability 6.1 (Pascal)
- **GPU 1**: Quadro P2000 (UUID `GPU-01093e11-5c00-eacc-0d34-cfb7226ede49`), 5120 MiB VRAM, compute capability 6.1
- CPU: Xeon, 40 logikai mag, 31GB RAM + 19GB swap

## P4000 kényszerítés / P2000 elzárás módszere
- **Környezeti változó**: `export CUDA_VISIBLE_DEVICES=0` (a fizikai PCI sorrend miatt a 0 = P4000)
- **Ellenőrzés**: `torch.cuda.device_count()` 1-et kell mutasson, `torch.cuda.get_device_name(0)` "Quadro P4000"-et
- **Biztosított működés**: PyTorch 2.1.2+cu118 és llama-cpp-python 0.3.35 (prebuilt CUDA 11.8 wheel) is csak a P4000-et látja
- **UUID-alapú finomhangolás** (opcionális): `CUDA_VISIBLE_DEVICES=GPU-5c9224fc-aadf-0efa-403a-bbb0745c46e4`

## A hibás GPU-allokáció okozta korábbi problémák
A korábbi `advanced_rag_search.py` a `LLM_GPU = 0` és `EMBEDDING_GPU = 0` konfigurációval rendelkezett,
de a Qwen mégis a P2000-en (GPU 1) jelent meg ~700MB VRAM-mal. Ez azért történt, mert a `torch.cuda.set_device()`
csak az alapértelmezett eszközt állítja, nem zárja el a másikat. A `CUDA_VISIBLE_DEVICES=0` környezeti változó
biztos, hogy a P2000 egyáltalán nem látható a folyamat számára.

## Javított RAG kereső (`/home/Jules/RAG_epito_ismeretek/advanced_rag_search.py`)
- Hozzáadva: `MAX_ITERATIONS = 10` iteráció-számláló gátló (nehogy loopba essen)
- Hozzáadva: `TIMEOUT_SECONDS = 120` SIGALRM-alapú timeout minden műveletre
- Hozzáadva: `USE_GPU_FORCE = True` GPU kényszerítés verifikációval
- A `generate_advanced_response._iteration_count` statikus számláló figyeli az ismétlődő hívásokat
- Ha a Qwen folyamat fut (lock aktív), a main() KeyboardInterrupt/Exception esetén `torch.cuda.empty_cache()`-t hív
