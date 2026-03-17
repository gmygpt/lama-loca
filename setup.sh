#!/bin/bash
# =============================================================
# Study AI Assistant — скрипт установки
# Максимально мощная локальная ИИ-система
# =============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║       📚 Study AI Assistant — Установка                 ║"
echo "║       Максимально мощная локальная ИИ-система           ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# 1. Python
echo "→ Проверка Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден! Установите Python 3.9+"
    exit 1
fi
PYVER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "  Python $PYVER ✓"

# 2. Виртуальное окружение
echo ""
echo "→ Виртуальное окружение..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  Создано ✓"
else
    echo "  Уже существует ✓"
fi
source venv/bin/activate

# 3. pip
echo ""
echo "→ Обновление pip..."
pip install --upgrade pip -q

# 4. Зависимости
echo ""
echo "→ Установка зависимостей (может занять 5-10 минут)..."
pip install -r requirements.txt -q 2>&1 | tail -5
echo "  Зависимости установлены ✓"

# 5. Директории
mkdir -p books output data models

# 6. Модель
echo ""
echo "→ Проверка LLM модели..."
MODEL_DIR="models"
MODEL_FILE="$MODEL_DIR/model.gguf"

if [ ! -f "$MODEL_FILE" ]; then
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║  ⚠️  Модель LLM не найдена!                             ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    echo "  Рекомендуемые модели (от лучшей к быстрой):"
    echo ""
    echo "  1) 🏆 Qwen2.5-32B Q4_K_M (~20 GB) — МАКСИМАЛЬНОЕ качество"
    echo "     Нужно 24+ GB RAM"
    echo ""
    echo "  2) ⭐ Qwen2.5-14B Q4_K_M (~9 GB) — ОТЛИЧНОЕ качество"
    echo "     Нужно 12+ GB RAM"
    echo ""
    echo "  3) 👍 Qwen2.5-7B Q4_K_M (~5 GB) — ХОРОШЕЕ качество"
    echo "     Нужно 8+ GB RAM"
    echo ""
    echo "  4) Qwen2.5-3B Q4_K_M (~2.5 GB) — базовое"
    echo "     Нужно 4+ GB RAM"
    echo ""

    # Определяем доступную RAM
    TOTAL_RAM_MB=$(free -m 2>/dev/null | awk '/^Mem:/{print $2}' || echo "0")
    TOTAL_RAM_GB=$((TOTAL_RAM_MB / 1024))
    echo "  💾 Доступно RAM: ${TOTAL_RAM_GB} GB"
    echo ""

    if [ "$TOTAL_RAM_GB" -ge 24 ]; then
        RECOMMENDED="32B"
        RECOMMENDED_FILE="qwen2.5-32b-instruct-q4_k_m.gguf"
        RECOMMENDED_REPO="Qwen/Qwen2.5-32B-Instruct-GGUF"
    elif [ "$TOTAL_RAM_GB" -ge 12 ]; then
        RECOMMENDED="14B"
        RECOMMENDED_FILE="qwen2.5-14b-instruct-q4_k_m.gguf"
        RECOMMENDED_REPO="Qwen/Qwen2.5-14B-Instruct-GGUF"
    elif [ "$TOTAL_RAM_GB" -ge 8 ]; then
        RECOMMENDED="7B"
        RECOMMENDED_FILE="qwen2.5-7b-instruct-q4_k_m.gguf"
        RECOMMENDED_REPO="Qwen/Qwen2.5-7B-Instruct-GGUF"
    else
        RECOMMENDED="3B"
        RECOMMENDED_FILE="qwen2.5-3b-instruct-q4_k_m.gguf"
        RECOMMENDED_REPO="Qwen/Qwen2.5-3B-Instruct-GGUF"
    fi

    echo "  🎯 Рекомендация для вашей системы: ${RECOMMENDED}"
    echo ""
    read -p "  Скачать рекомендуемую модель ($RECOMMENDED)? (y/n): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "  Скачивание Qwen2.5-${RECOMMENDED}-Instruct Q4_K_M..."
        echo "  Это может занять некоторое время..."
        pip install huggingface-hub -q
        huggingface-cli download "$RECOMMENDED_REPO" \
            "$RECOMMENDED_FILE" \
            --local-dir "$MODEL_DIR" \
            --local-dir-use-symlinks False

        if [ -f "$MODEL_DIR/$RECOMMENDED_FILE" ]; then
            mv "$MODEL_DIR/$RECOMMENDED_FILE" "$MODEL_FILE"
            echo "  ✅ Модель скачана и установлена!"
        fi
    else
        echo "  ⚠️ Скачайте модель позже перед использованием"
        echo "  Сохраните файл .gguf как: $SCRIPT_DIR/models/model.gguf"
    fi
else
    SIZE=$(du -h "$MODEL_FILE" | cut -f1)
    echo "  Модель найдена: $MODEL_FILE ($SIZE) ✓"
fi

# 7. Готово
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ✅ Установка завершена!                                ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "  Запуск:"
echo ""
echo "    source venv/bin/activate"
echo "    python main.py"
echo ""
echo "  Откроется GUI в браузере: http://localhost:7860"
echo ""
echo "  1. Загрузите книги через интерфейс (вкладка «Книги»)"
echo "  2. Нажмите «Индексировать»"
echo "  3. Создавайте документы, презентации, или задавайте вопросы!"
echo ""
