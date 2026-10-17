#!/bin/bash
# Candle + YantrikDB Rust integráció build script
# Cél: pure-Rust kognitív AI stack (ML inferencia + memória)
set -e

CANDLE_DIR="/data/Brain/candle"
BUILD_DIR="/data/mcp_server/rust_stack"
BIN_DIR="$BUILD_DIR/bin"

echo "🦀 Rust Cognitive AI Stack Build"
echo "================================="

# 1. Check Rust
if ! command -v cargo &>/dev/null; then
    echo "❌ Rust/Cargo not found. Install: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    exit 1
fi
echo "✅ Rust: $(rustc --version)"

# 2. Check CUDA
if nvidia-smi &>/dev/null; then
    echo "✅ CUDA available — building with GPU support"
    CARGO_FEATURES="--features cuda"
else
    echo "⚠️  No CUDA — CPU-only build"
    CARGO_FEATURES=""
fi

# 3. Build candle-transformers (with GLM4 support)
echo ""
echo "📦 Building candle-transformers (GLM4 inference)..."
mkdir -p "$BIN_DIR"
cd "$CANDLE_DIR"

# Build the GLM4 example as a standalone binary
cargo build --release -p candle-examples --example glm4 $CARGO_FEATURES 2>&1 | tail -5
cp target/release/examples/glm4 "$BIN_DIR/candle-glm4" 2>/dev/null && \
    echo "✅ candle-glm4 → $BIN_DIR/candle-glm4" || \
    echo "⚠️  glm4 build failed (may need specific features)"

# Build whisper for speech-to-text
cargo build --release -p candle-examples --example whisper $CARGO_FEATURES 2>&1 | tail -3
cp target/release/examples/whisper "$BIN_DIR/candle-whisper" 2>/dev/null && \
    echo "✅ candle-whisper → $BIN_DIR/candle-whisper" || \
    echo "⚠️  whisper build skipped"

echo ""
echo "🧠 Rust Stack Summary:"
echo "  candle-glm4:    $(ls -la "$BIN_DIR/candle-glm4" 2>/dev/null | awk '{print $5, "bytes"}' || echo 'not built')"
echo "  candle-whisper:  $(ls -la "$BIN_DIR/candle-whisper" 2>/dev/null | awk '{print $5, "bytes"}' || echo 'not built')"
echo "  yantrikdb:       $(ls -la /usr/local/lib/libyantrikdb* 2>/dev/null | awk '{print $5, "bytes"}' || echo 'via Python')"
echo ""
echo "Usage:"
echo "  $BIN_DIR/candle-glm4 --model-id THUDM/GLM-4-9B-0414 --prompt 'Hello'"
echo "  $BIN_DIR/candle-whisper --model-id openai/whisper-tiny --input audio.wav"
