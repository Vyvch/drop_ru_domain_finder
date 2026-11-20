# Freeing Domains Project (DropRadar)

Сервис для отслеживания, анализа и проверки истории освобождающихся доменов.

## 🚀 Функциональность

- **Поиск и фильтрация доменов:**
  - Получение списка освобождающихся доменов (`.ru`, `.su`, `.рф`).
  - Фильтрация по регулярным выражениям (Google RE2) через API (`/api/domains?regex=...`).
  - Оценка доменов и выбор лучших (`evaluate_top_domains`).
- **Интеграция с Wayback Machine:**
  - Получение архивной истории доменов по API (`/api/wayback?domain=...`).
  - Кэширование и асинхронная загрузка снепшотов.
- **Интеграция с Whois через MCP:**
  - MCP-клиент и сервер для проверки регистрационных данных (`mcp_whois.py`, `mcp_client.py`).
- **Web UI & CLI:**
  - Веб-интерфейс на базе Jinja2-шаблонов (`templates/index.html`).
  - Консольная утилита (`cli.py`).

## 🛠 Стек технологий

- Python 3.10+
- FastAPI & Uvicorn
- Pydantic v2
- BeautifulSoup4, Requests
- Google RE2
- Pytest (140+ unit/integration тестов)

## 📦 Установка и запуск

1. **Клонирование и установка зависимостей:**
   ```bash
   git clone <URL_РЕПОЗИТОРИЯ>
   cd domains_project
   pip install -r requirements.txt
   ```

2. **Запуск веб-сервера:**
   ```bash
   uvicorn api:app --reload --port 8000
   ```
   Документация Swagger доступна по адресу: `http://127.0.0.1:8000/docs`

3. **Запуск CLI:**
   ```bash
   python cli.py list
   python cli.py top
   ```

4. **Запуск тестов:**
   ```bash
   pytest tests/
   ```
