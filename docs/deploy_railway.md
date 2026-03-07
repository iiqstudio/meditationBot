# Деплой на Railway (тестовый бесплатный вариант)

## Важно
- Railway free-режим подходит для теста, но не гарантирует постоянный 24/7 прод.
- SQLite на Railway обычно хранится на эфемерном диске: после redeploy/restart данные могут потеряться.

## 1) Подготовь репозиторий
1. Создай GitHub-репозиторий и запушь проект.
2. Убедись, что в репозитории есть:
   - `railway.json`
   - `Procfile`

## 2) Создай сервис в Railway
1. Открой Railway и создай новый проект.
2. Выбери `Deploy from GitHub repo`.
3. Подключи репозиторий с этим ботом.

## 3) Заполни Variables в Railway
В сервисе открой `Variables` и добавь:

- `BOT_TOKEN` = токен бота
- `ALLOWED_USERNAMES` = `anastasiyaanastasia,ilayarr`
- `ADMIN_USERNAMES` = `ilayarr`
- `USER_LABELS_BY_USERNAME` = `anastasiyaanastasia:Настя,ilayarr:Илья`
- `TIMEZONE` = `Europe/Moscow`
- `DB_PATH` = `/tmp/meditation.db`
- `REPORT_SCOPE` = `global`
- `AUTO_REPORT_PERIOD` = `week`
- `AUTO_REPORT_WEEKDAY` = `0`
- `AUTO_REPORT_TIME` = `08:00`
- `AUTO_REPORT_MONTHLY_ENABLED` = `true`
- `AUTO_REPORT_MONTHLY_TIME` = `08:00`
- `ALLOW_NEGATIVE_ENTRIES` = `false`
- `MAX_ENTRY_MINUTES` = `180`

## 4) Запуск
1. Нажми `Deploy`.
2. Открой `Logs` и проверь строку:
   - `Bot startup complete...`

## 5) Проверка
1. Напиши боту `/start`.
2. Отправь `+5` с каждого аккаунта.
3. Проверь `/week`, `/month`, `/year`.

## 6) Обновления
После изменений локально:
1. Пуш в GitHub.
2. Railway автоматически сделает redeploy (или запусти вручную).

## Рекомендация для постоянной работы
Когда протестируешь, лучше перейти на VPS/платный always-on сервис и вынести хранение из SQLite в постоянное хранилище.
