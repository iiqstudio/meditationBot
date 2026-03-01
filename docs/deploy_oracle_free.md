# Деплой на Oracle Cloud Always Free (VPS + systemd)

Эта схема делает бота постоянным: он работает на сервере, даже когда ваш компьютер выключен.

## 1) Подготовка Oracle Free VPS
1. Создайте VM в Oracle Cloud (Ubuntu 22.04/24.04).
2. Откройте SSH доступ и подключитесь:
   ```bash
   ssh ubuntu@<VM_PUBLIC_IP>
   ```

## 2) Первичный bootstrap на сервере
Выполните на сервере (под root):
```bash
sudo mkdir -p /opt/meditation-bot/app
sudo chown -R ubuntu:ubuntu /opt/meditation-bot
```

С локальной машины загрузите код в `/opt/meditation-bot/app`:
```bash
./scripts/deploy_to_vps.sh ubuntu@<VM_PUBLIC_IP> /opt/meditation-bot/app --sync-only
```

После первой заливки на сервере:
```bash
cd /opt/meditation-bot/app
sudo bash deploy/vps/bootstrap_ubuntu.sh
```

## 3) Production .env на сервере
1. На сервере создайте файл `/opt/meditation-bot/shared/.env`:
   ```bash
   sudo cp /opt/meditation-bot/app/deploy/vps/.env.production.example /opt/meditation-bot/shared/.env
   sudo nano /opt/meditation-bot/shared/.env
   ```
2. Заполните `BOT_TOKEN` и остальные параметры.

## 4) Обновление приложения и установка systemd
На сервере:
```bash
cd /opt/meditation-bot/app
bash deploy/vps/update_app.sh
sudo bash /opt/meditation-bot/app/deploy/vps/install_systemd_service.sh
```

По умолчанию сервис запускается от пользователя `ubuntu`.
Если нужен другой пользователь, запускайте скрипты с `APP_USER=<name>`.

Проверка:
```bash
sudo systemctl status meditation-bot --no-pager
sudo journalctl -u meditation-bot -f
```

## 5) Дальнейшие обновления (заливка)
После изменений локально запускайте:
```bash
./scripts/deploy_to_vps.sh ubuntu@<VM_PUBLIC_IP> /opt/meditation-bot/app
```

## Полезно
- Рестарт сервиса:
  ```bash
  sudo systemctl restart meditation-bot
  ```
- Автозапуск после reboot уже включен (`systemctl enable`).
- База SQLite хранится в `/opt/meditation-bot/shared/data/meditation.db`.
