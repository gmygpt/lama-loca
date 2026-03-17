#!/usr/bin/env python3
"""
Study AI Assistant — GUI приложение на Gradio
Красивый интерфейс для работы с локальной ИИ-моделью
"""
import sys
import os
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gradio as gr
import config
from src.llm_engine import LLMEngine
from src.knowledge_base import KnowledgeBase
from src.document_generator import DocumentGenerator
from src.presentation_generator import PresentationGenerator

# ======================================================================
# Глобальные объекты
# ======================================================================
llm: LLMEngine = None
kb: KnowledgeBase = None
doc_gen = DocumentGenerator()
pres_gen = PresentationGenerator()
_init_lock = threading.Lock()


def init_kb():
    global kb
    if kb is None:
        kb = KnowledgeBase()
    return kb


def init_llm():
    global llm
    if llm is None:
        llm = LLMEngine()
        llm.load()
    return llm


# ======================================================================
# Обработчики GUI
# ======================================================================

def on_index_books():
    """Индексация всех книг"""
    try:
        k = init_kb()
        result = k.index_all_books()
        stats = k.stats()
        summary = (
            f"{result}\n\n"
            f"📊 Статистика:\n"
            f"  Книг: {stats['total_books']}\n"
            f"  Фрагментов: {stats['total_chunks']}\n"
        )
        if stats['books']:
            summary += "  Книги: " + ", ".join(stats['books'])
        return summary
    except Exception as e:
        return f"❌ Ошибка: {e}"


def on_add_book(files):
    """Добавить загруженные книги"""
    if not files:
        return "Выберите файлы для загрузки"

    try:
        k = init_kb()
        results = []

        for file in files:
            # Копируем в books/
            filename = os.path.basename(file.name if hasattr(file, 'name') else file)
            dest = os.path.join(config.BOOKS_DIR, filename)

            if hasattr(file, 'name'):
                import shutil
                shutil.copy2(file.name, dest)
            else:
                import shutil
                shutil.copy2(file, dest)

            result = k.add_book(dest)
            results.append(result)

        stats = k.stats()
        return "\n".join(results) + f"\n\n📊 Всего: {stats['total_books']} книг, {stats['total_chunks']} фрагментов"
    except Exception as e:
        return f"❌ Ошибка: {e}"


def on_clear_kb():
    """Очистить базу знаний"""
    try:
        k = init_kb()
        return k.clear()
    except Exception as e:
        return f"❌ Ошибка: {e}"


def on_get_stats():
    """Получить статистику"""
    try:
        k = init_kb()
        stats = k.stats()
        text = (
            f"📚 Книг проиндексировано: {stats['total_books']}\n"
            f"📄 Фрагментов текста: {stats['total_chunks']}\n"
        )
        if stats['books']:
            text += "\n📖 Книги:\n"
            for b in stats['books']:
                text += f"  • {b}\n"
        else:
            text += "\n⚠️ Книги не добавлены. Загрузите книги через вкладку «Книги»."
        return text
    except Exception as e:
        return f"❌ Ошибка: {e}"


def generate_document(topic: str, doc_type: str, fmt: str):
    """Генерация документа любого типа"""
    if not topic.strip():
        return "Введите тему", None

    try:
        k = init_kb()
        l = init_llm()

        # Выбираем шаблон
        type_map = {
            "Отчёт": "report",
            "Конспект": "summary",
            "Эссе": "essay",
            "Анализ": "analysis",
            "Подготовка к экзамену": "exam_prep",
        }
        template_key = type_map.get(doc_type, "report")
        template = config.PROMPTS[template_key]

        # Поиск контекста
        context = k.search(topic)

        # Генерация
        text = l.generate_with_context(template, topic, context)

        # Сохранение
        fmt_map = {"Оба (DOCX + MD)": "both", "DOCX": "docx", "Markdown": "md"}
        out_fmt = fmt_map.get(fmt, "both")

        doc_type_ru = {
            "Отчёт": "отчёт", "Конспект": "конспект", "Эссе": "эссе",
            "Анализ": "анализ", "Подготовка к экзамену": "экзамен"
        }

        files = doc_gen.generate(text, topic, doc_type_ru.get(doc_type, "документ"), out_fmt)

        file_list = "\n".join([f"📁 {os.path.basename(f)}" for f in files])
        return text, f"✅ Сохранено:\n{file_list}\n\nПапка: {config.OUTPUT_DIR}"

    except FileNotFoundError as e:
        return str(e), "❌ Модель не найдена. Скачайте модель (см. вкладку «Настройки»)"
    except Exception as e:
        return f"❌ Ошибка: {e}", f"❌ {e}"


def generate_presentation(topic: str):
    """Генерация презентации"""
    if not topic.strip():
        return "Введите тему", None

    try:
        k = init_kb()
        l = init_llm()

        context = k.search(topic)
        text = l.generate_with_context(config.PROMPTS["presentation"], topic, context)
        filepath = pres_gen.generate(text, topic)

        return text, f"✅ Презентация сохранена:\n📁 {os.path.basename(filepath)}\n\nПапка: {config.OUTPUT_DIR}"

    except FileNotFoundError as e:
        return str(e), "❌ Модель не найдена"
    except Exception as e:
        return f"❌ Ошибка: {e}", f"❌ {e}"


def chat_respond(message: str, history: list):
    """Интерактивный чат"""
    if not message.strip():
        return "", history

    try:
        k = init_kb()
        l = init_llm()

        context = k.search(message)
        template = config.PROMPTS["qa"]

        # Потоковая генерация
        response = ""
        for token in l.generate_with_context(template, message, context, stream=True):
            response += token
            yield history + [[message, response]]

    except FileNotFoundError:
        yield history + [[message, "❌ Модель не найдена. Скачайте модель и укажите путь в config.py"]]
    except Exception as e:
        yield history + [[message, f"❌ Ошибка: {e}"]]


def get_model_info():
    """Информация о модели"""
    model_exists = os.path.exists(config.LLM_MODEL_PATH)
    model_size = ""
    if model_exists:
        size_bytes = os.path.getsize(config.LLM_MODEL_PATH)
        size_gb = size_bytes / (1024 ** 3)
        model_size = f"{size_gb:.1f} GB"

    info = f"""## Состояние системы

### LLM Модель
- **Путь**: `{config.LLM_MODEL_PATH}`
- **Статус**: {"✅ Найдена" if model_exists else "❌ Не найдена"}
{f"- **Размер**: {model_size}" if model_size else ""}
- **Контекст**: {config.LLM_CONTEXT_SIZE} токенов
- **GPU слои**: {config.LLM_GPU_LAYERS} (-1 = все на GPU)
- **Температура**: {config.LLM_TEMPERATURE}

### Эмбеддинги
- **Модель**: `{config.EMBEDDING_MODEL}`

### Реранкер
- **Модель**: `{config.RERANKER_MODEL}`
- **Активен**: {"✅ Да" if config.USE_RERANKER else "❌ Нет"}

### Директории
- **Книги**: `{config.BOOKS_DIR}`
- **Результаты**: `{config.OUTPUT_DIR}`
- **Модели**: `{config.MODELS_DIR}`

---

## Как скачать модель

### Рекомендуемые модели (от лучшей к быстрой):

| Модель | RAM | Качество |
|--------|-----|----------|
| **Qwen2.5-32B-Instruct Q4_K_M** | 20+ GB | 🏆 Максимум |
| **Qwen2.5-14B-Instruct Q4_K_M** | 10+ GB | ⭐ Отличное |
| **Qwen2.5-7B-Instruct Q4_K_M** | 6+ GB | 👍 Хорошее |
| **Qwen2.5-3B-Instruct Q4_K_M** | 4+ GB | Базовое |

### Команда для скачивания (пример для 14B):
```
pip install huggingface-hub
huggingface-cli download Qwen/Qwen2.5-14B-Instruct-GGUF \\
    qwen2.5-14b-instruct-q4_k_m.gguf \\
    --local-dir models/ \\
    --local-dir-use-symlinks False
mv models/qwen2.5-14b-instruct-q4_k_m.gguf models/model.gguf
```

💡 Чем больше модель, тем выше качество. Для качества уровня GPT-4 рекомендуется 32B или 14B.
"""
    return info


def list_output_files():
    """Список файлов в output/"""
    files = []
    if os.path.exists(config.OUTPUT_DIR):
        for f in sorted(os.listdir(config.OUTPUT_DIR), reverse=True):
            path = os.path.join(config.OUTPUT_DIR, f)
            size = os.path.getsize(path)
            size_str = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f} MB"
            files.append(f"📄 {f} ({size_str})")
    if not files:
        return "Пока нет созданных документов"
    return "\n".join(files)


def get_output_files_for_download():
    """Получить файлы для скачивания"""
    files = []
    if os.path.exists(config.OUTPUT_DIR):
        for f in sorted(os.listdir(config.OUTPUT_DIR), reverse=True):
            files.append(os.path.join(config.OUTPUT_DIR, f))
    return files


# ======================================================================
# GUI
# ======================================================================

def create_gui():
    """Создать интерфейс Gradio"""

    custom_css = """
    .gradio-container {
        max-width: 1200px !important;
    }
    .main-title {
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5em !important;
        font-weight: bold;
        margin-bottom: 0.2em;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.1em;
        margin-bottom: 1em;
    }
    """

    with gr.Blocks(
        title="Study AI Assistant",
        theme=gr.themes.Soft(
            primary_hue="indigo",
            secondary_hue="purple",
            neutral_hue="slate",
        ),
        css=custom_css,
    ) as app:

        gr.HTML("""
        <div style="text-align: center; padding: 20px 0;">
            <h1 class="main-title">📚 Study AI Assistant</h1>
            <p class="subtitle">Локальный ИИ-ассистент для учёбы — учится по вашим книгам</p>
        </div>
        """)

        with gr.Tabs() as tabs:

            # ========== ТАБ 1: ЧАТ ==========
            with gr.TabItem("💬 Чат", id="chat"):
                gr.Markdown("### Задайте вопрос по вашим книгам")
                chatbot = gr.Chatbot(
                    height=500,
                    show_label=False,
                    avatar_images=(None, "https://em-content.zobj.net/source/twitter/376/robot_1f916.png"),
                    bubble_full_width=False,
                )
                with gr.Row():
                    chat_input = gr.Textbox(
                        placeholder="Введите вопрос по вашим книгам...",
                        show_label=False,
                        scale=9,
                        container=False,
                    )
                    chat_send = gr.Button("Отправить", variant="primary", scale=1)

                chat_clear = gr.Button("🗑️ Очистить чат", size="sm")

                chat_send.click(
                    chat_respond,
                    inputs=[chat_input, chatbot],
                    outputs=[chatbot],
                ).then(lambda: "", outputs=[chat_input])

                chat_input.submit(
                    chat_respond,
                    inputs=[chat_input, chatbot],
                    outputs=[chatbot],
                ).then(lambda: "", outputs=[chat_input])

                chat_clear.click(lambda: [], outputs=[chatbot])

            # ========== ТАБ 2: ДОКУМЕНТЫ ==========
            with gr.TabItem("📝 Документы", id="docs"):
                gr.Markdown("### Создание учебных документов")

                with gr.Row():
                    doc_topic = gr.Textbox(
                        label="Тема",
                        placeholder="Введите тему документа...",
                        scale=3,
                    )
                    doc_type = gr.Dropdown(
                        choices=["Отчёт", "Конспект", "Эссе", "Анализ", "Подготовка к экзамену"],
                        value="Отчёт",
                        label="Тип документа",
                        scale=1,
                    )
                    doc_format = gr.Dropdown(
                        choices=["Оба (DOCX + MD)", "DOCX", "Markdown"],
                        value="Оба (DOCX + MD)",
                        label="Формат",
                        scale=1,
                    )

                doc_generate_btn = gr.Button("🚀 Создать документ", variant="primary", size="lg")

                with gr.Row():
                    doc_output = gr.Textbox(
                        label="Сгенерированный текст",
                        lines=20,
                        show_copy_button=True,
                    )

                doc_status = gr.Textbox(label="Статус", lines=3)

                doc_generate_btn.click(
                    generate_document,
                    inputs=[doc_topic, doc_type, doc_format],
                    outputs=[doc_output, doc_status],
                )

            # ========== ТАБ 3: ПРЕЗЕНТАЦИИ ==========
            with gr.TabItem("📊 Презентации", id="pres"):
                gr.Markdown("### Создание презентаций PowerPoint")

                pres_topic = gr.Textbox(
                    label="Тема презентации",
                    placeholder="Введите тему...",
                )
                pres_generate_btn = gr.Button("🚀 Создать презентацию", variant="primary", size="lg")

                with gr.Row():
                    pres_output = gr.Textbox(
                        label="Структура презентации",
                        lines=20,
                        show_copy_button=True,
                    )
                pres_status = gr.Textbox(label="Статус", lines=3)

                pres_generate_btn.click(
                    generate_presentation,
                    inputs=[pres_topic],
                    outputs=[pres_output, pres_status],
                )

            # ========== ТАБ 4: КНИГИ ==========
            with gr.TabItem("📖 Книги", id="books"):
                gr.Markdown("### Управление базой знаний")

                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("#### Загрузить книги")
                        book_upload = gr.File(
                            label="Выберите файлы",
                            file_count="multiple",
                            file_types=[".pdf", ".txt", ".epub", ".docx", ".md", ".fb2", ".html"],
                        )
                        book_upload_btn = gr.Button("📥 Загрузить и индексировать", variant="primary")

                    with gr.Column(scale=1):
                        gr.Markdown("#### Действия")
                        book_index_btn = gr.Button("🔄 Индексировать папку books/", variant="secondary")
                        book_stats_btn = gr.Button("📊 Статистика")
                        book_clear_btn = gr.Button("🗑️ Очистить базу", variant="stop")

                book_output = gr.Textbox(label="Результат", lines=10)

                book_upload_btn.click(on_add_book, inputs=[book_upload], outputs=[book_output])
                book_index_btn.click(on_index_books, outputs=[book_output])
                book_stats_btn.click(on_get_stats, outputs=[book_output])
                book_clear_btn.click(on_clear_kb, outputs=[book_output])

            # ========== ТАБ 5: ФАЙЛЫ ==========
            with gr.TabItem("📁 Файлы", id="files"):
                gr.Markdown("### Созданные документы")
                files_refresh_btn = gr.Button("🔄 Обновить список")
                files_list = gr.Textbox(label="Файлы", lines=15, value=list_output_files)
                files_refresh_btn.click(list_output_files, outputs=[files_list])

                gr.Markdown(f"📂 Папка с файлами: `{config.OUTPUT_DIR}`")

            # ========== ТАБ 6: НАСТРОЙКИ ==========
            with gr.TabItem("⚙️ Настройки", id="settings"):
                settings_info = gr.Markdown(value=get_model_info)
                settings_refresh = gr.Button("🔄 Обновить информацию")
                settings_refresh.click(get_model_info, outputs=[settings_info])

    return app


# ======================================================================
# Entry point
# ======================================================================

if __name__ == "__main__":
    os.makedirs(config.BOOKS_DIR, exist_ok=True)
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    os.makedirs(config.MODELS_DIR, exist_ok=True)
    os.makedirs(config.DATA_DIR, exist_ok=True)

    print("=" * 60)
    print("  📚 Study AI Assistant")
    print("  Запуск GUI-интерфейса...")
    print("=" * 60)

    app = create_gui()
    app.launch(
        server_port=config.GUI_PORT,
        share=config.GUI_SHARE,
        inbrowser=True,
        show_api=False,
    )
