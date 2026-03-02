# Meditation Tracker Bot

Telegram-бот для учета минут медитации в формате `+5`, `+15` или `10`.

## Возможности
- Принимает сообщения с числом минут и сохраняет запись.
- Считает суммы по каждому участнику за день/неделю/месяц.
- Команды отчетов:
  - `/day`
  - `/week`
  - `/month`
- Внизу чата есть кнопки быстрых действий:
  - `+5`, `+10`, `+15`, `+30`
  - `/day`, `/week`, `/month`
- Автоматически отправляет отчет по расписанию:
  - день / неделя / месяц (через `AUTO_REPORT_PERIOD`)
  - время отправки (`AUTO_REPORT_TIME`)
  - день недели для weekly (`AUTO_REPORT_WEEKDAY`, `0=понедельник`)
  - опционально дополнительный monthly-отчет 1-го числа
    (`AUTO_REPORT_MONTHLY_ENABLED`, `AUTO_REPORT_MONTHLY_TIME`)

## Быстрый старт
1. Создай виртуальное окружение и установи зависимости:
   - `make install`
2. Подготовь конфиг:
   - `cp .env.example .env`
   - Заполни `BOT_TOKEN`, доступы и имена пользователей.
3. Запусти бота:
   - `make run`

## Формат ввода
- `+15` -> добавить 15 минут.
- `10` -> добавить 10 минут.
- `-5` -> работает только если `ALLOW_NEGATIVE_ENTRIES=true`.

## Переменные окружения
Смотри `.env.example`.

Для сценария двух людей в личных чатах с ботом используй:
- `REPORT_SCOPE=global`

## Важно по доступам
Можно ограничить доступ:
- по `ALLOWED_USER_IDS`
- по `ALLOWED_USERNAMES`
- или сразу по обоим (достаточно совпасть по одному из правил)

## Структура проекта
- `src/bot/main.py` - запуск бота и планировщик отчетов.
- `src/bot/config.py` - загрузка настроек.
- `src/bot/db/repository.py` - SQLite слой.
- `src/bot/services/tracker.py` - бизнес-логика подсчетов.
- `src/bot/handlers/` - Telegram handlers.
- `scripts/init_db.py` - ручная инициализация БД.

## Деплой 24/7 (VPS)
- Для теста на бесплатном VPS (Oracle Always Free) используй:
  `docs/deploy_oracle_free.md`
- Файлы деплоя:
  - `deploy/vps/bootstrap_ubuntu.sh`
  - `deploy/vps/update_app.sh`
  - `deploy/vps/install_systemd_service.sh`
  - `deploy/systemd/meditation-bot.service`
  - `scripts/deploy_to_vps.sh`

## Деплой на Railway (тест)
- Быстрый тестовый деплой через GitHub:
  `docs/deploy_railway.md`
- Файлы Railway:
  - `railway.json`
  - `Procfile`
