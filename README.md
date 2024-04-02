# Бот-ассистент

Стек: Telegram Bot Api, logging, requests, time

## Описание

Telegram-бот, который обращается к API сервису Практикум.Домашка и узнает статус домашней работы пользователя: взята ли домашка в ревью, проверена ли она, а если проверена — то принял её ревьюер или вернул на доработку.

### Что делает бот: 
- раз в 10 минут опрашивает API сервис Практикум.Домашка и проверяет статус отправленной на ревью домашней работы;
- при обновлении статуса анализирует ответ API и отправляет соответствующее уведомление в Telegram;
- логирует свою работу и сообщает о важных проблемах сообщением в Telegram.

## Установка

1. Клонировать репозиторий и перейти в него в командной строке:
```
git clone git@github.com:gdemasha/homework_bot.git
cd homework_bot
```
2. Cоздать и активировать виртуальное окружение:
```
# Для MacOS и Linux
python3 -m venv venv
source venv/bin/activate

# Для Windows
python -m venv venv && . venv/Scripts/activate
```
3. Создать файл .env и наполнить его данными:
```
<ИМЯ_ТОКЕНА_ВАШЕГО_ЭНДПОИНТА>=<токен>
TELEGRAM_TOKEN=<токен_вашего_бота_в_тг>
TELEGRAM_CHAT_ID=<id_пользователя_бота>
```
4. Установить зависимости из файла requirements.txt:
```
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```
5. Запустить через терминал:
```
# В linux/macOS
python3 homework.py

# В Windows
python homework.py
```

