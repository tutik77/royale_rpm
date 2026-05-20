# Royale Helper

**Royale Helper** — это веб-приложение на Django для игроков Clash Royale. Приложение анализирует текущую мету, собирает популярные колоды с RoyaleAPI и StatsRoyale, а затем подбирает оптимальные колоды под конкретный аккаунт игрока на основе его коллекции карт и их уровней.

Введите свой игровой тег — и система покажет, какие метовые колоды вы можете собрать прямо сейчас, а какие станут доступны после апгрейда имеющихся карт.

---

## Features

- 🃏 **База метовых колод** — автоматический импорт популярных колод с RoyaleAPI и StatsRoyale
- 🔍 **Поиск по тегу игрока** — интеграция с официальным Clash Royale API для получения профиля
- 📊 **Персональные рекомендации** — подбор колод на основе открытых карт и их уровней
- ⚡ **Расчёт потенциала** — симуляция апгрейда карт для оценки будущей силы колоды
- 🎨 **Современный UI** — тёмная игровая тема с адаптивным дизайном
- 🛠️ **Management-команды** — CLI для импорта карт и колод

---

## Tech Stack

| Категория | Технологии |
|-----------|------------|
| **Backend** | Python 3.12+, Django 5.2 |
| **Database** | SQLite (по умолчанию) |
| **External APIs** | [Clash Royale API](https://developer.clashroyale.com/) |
| **Web Scraping** | BeautifulSoup4, Requests |
| **Frontend** | Django Templates, CSS3 (custom dark theme) |
| **Package Manager** | uv / pip |

---

## Installation

### 1. Клонирование репозитория

```bash
git clone https://github.com/your-username/royale-helper.git
cd royale-helper
```

### 2. Создание виртуального окружения

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -e .
# или через uv
uv sync
```

### 4. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
CLASH_ROYALE_API_TOKEN=your_api_token_here
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=true
```

> 🔑 Токен API можно получить на [developer.clashroyale.com](https://developer.clashroyale.com/)

### 5. Применение миграций

```bash
cd royale_helper
python manage.py migrate
```

### 6. Импорт данных

```bash
# Импорт карт из официального API
python manage.py import_cards

# Импорт колод (один из вариантов)
python manage.py import_statsroyale_decks
python manage.py import_royaleapi_decks
```

### 7. Создание суперпользователя (опционально)

```bash
python manage.py createsuperuser
```

### 8. Запуск сервера

```bash
python manage.py runserver
```

Откройте http://127.0.0.1:8000/ в браузере.

---

## Screenshots

<!-- Добавьте скриншоты вашего приложения -->
![1 страница](screenshots\image.png)
![2 страница](screenshots\image1.png)
![3 страница](screenshots\image2.png)
---

## API Endpoints

Приложение не предоставляет REST API, но использует следующие внешние сервисы:

### Clash Royale API (Official)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| GET | `/v1/cards` | Получение списка всех карт |
| GET | `/v1/players/{tag}` | Получение профиля игрока по тегу |

### Web Scraping Sources

| Источник | URL | Данные |
|----------|-----|--------|
| RoyaleAPI | `royaleapi.com/decks/popular` | Популярные колоды с винрейтом |
| StatsRoyale | `statsroyale.com/decks/popular` | Колоды Path of Legends |

---

## Architecture

![Архитектура проекта](screenshots\architecture.png)


### Data Flow

1. **Runtime (User Request)**:  
   `Browser` → `Views` → `Services` → `Clash Royale API` (get player profile)  
   `Services` → `Models` → `SQLite` (read decks, calculate recommendations)

2. **Data Import (Admin CLI)**:  
   `import_cards` → `Clash Royale API` → `SQLite` (populate cards)  
   `import_*_decks` → `Web Scraping` → `SQLite` (populate meta decks)

### Project Structure

```
royale_helper/
├── app/                          # Main Django application
│   ├── management/commands/      # CLI commands for data import
│   ├── services/                 # Business logic layer
│   │   ├── clash_royale.py       # API client
│   │   ├── deck_recommendation.py# Recommendation engine
│   │   └── deck_signature.py     # Deck deduplication
│   ├── templates/app/            # HTML templates
│   ├── static/app/               # CSS, images
│   ├── models.py                 # Data models
│   └── views.py                  # HTTP handlers
├── royale_helper/                # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── manage.py
```

---

## Management Commands

| Команда | Описание |
|---------|----------|
| `import_cards` | Импорт всех карт из Clash Royale API |
| `import_royaleapi_decks` | Импорт популярных колод с RoyaleAPI |
| `import_statsroyale_decks` | Импорт колод со StatsRoyale |
| `repopulate_db` | Полная очистка и переимпорт данных |

---

## License

MIT License. See [LICENSE](LICENSE) for details.

