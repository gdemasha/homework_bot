# Бот-ассистент

Стек: Telegram Bot Api, logging, requests, time

## Описание

Telegram-бот, который обращается к API сервису Практикум.Домашка и узнает статус домашней работы пользователя: взята ли домашка в ревью, проверена ли она, а если проверена — то принял её ревьюер или вернул на доработку.

### Что делает бот: 
- раз в 10 минут опрашивает API сервис Практикум.Домашка и проверяет статус отправленной на ревью домашней работы;
- при обновлении статуса анализирует ответ API и отправляет соответствующее уведомление в Telegram;
- логирует свою работу и сообщает о важных проблемах сообщением в Telegram.
