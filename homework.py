import http
import json
import logging
import os
import sys
import time
from sys import stdout

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (
    ChatIDIsDigitException,
    InvalidJSonException,
    NoEnvVarException,
    SendMessageException,
    UnexpectedStatusCodeException,
)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Checks the accessibility of the environmental variables."""
    env_vars = (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,)
    if not all((var for var in env_vars)):
        raise NoEnvVarException(
            'Отсутствуют обязательные переменные окружения'
        )

    # Если присвоить TELEGRAM_CHAT_ID в .env нечисловое значение,
    # проверка на токены все равно проходит,
    # поэтому отдельно проверяю числовой идентификатор

    if not TELEGRAM_CHAT_ID.isdigit():
        raise ChatIDIsDigitException('Идентификатор должен быть числовым.')


def send_message(bot, message):
    """Sends a message to the Telegram chat."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except telegram.TelegramError as error:
        error_massage = f'Сбой при отправке сообщения:{error}'
        logging.error(error_massage)
        raise SendMessageException from error(error_massage)

    logging.debug('Сообщение успешно отправлено!')


def get_api_answer(timestamp):
    """Requests the endpoint of the API-server."""
    payload = {'from_date': timestamp}

    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        response.raise_for_status()

    except requests.exceptions.HTTPError as error:
        logging.error(f'Эндпоинт недоступен:{error}')

    except requests.exceptions.RequestException as error:
        logging.error(f'Сбои при запросе к эндпоинту: {error}')

    if response.status_code != http.HTTPStatus.OK:
        status_code = response.status_code
        error_message = f'Неожиданный статус запроса: {status_code}'
        logging.error(error_message)
        raise UnexpectedStatusCodeException(error_message)

    try:
        return response.json()
    except json.JSONDecodeError as error:
        error_message = f'Невалидный JSON: {error}'
        logging.error(error_message)
        InvalidJSonException(error_message)


def check_response(response):
    """Checks an API answer for compliance with the documentation."""
    if not isinstance(response, dict):
        type_of_the_response = type(response)
        error_message = (
            'API структура данных не соответствует ожиданиям: '
            f'получен тип {type_of_the_response} вместо словаря'
        )
        logging.error(error_message)
        raise TypeError(error_message)

    if not (
        response.get('homeworks')
        and response.get('current_date')
    ):
        error_message = (
            'Отсутствуют ожидаемые ключи "homeworks" и "current_date"'
        )
        logging.error(error_message)
        raise KeyError(error_message)

    if not isinstance(response.get('homeworks'), list):
        type_of_homeworks_response = type(response.get('homeworks'))
        error_message = (
            'Тип данных ключа не соответствует ожиданиям: '
            f'получен тип {type_of_homeworks_response} '
            'вместо списка'
        )
        logging.error(error_message)
        raise TypeError(error_message)

    if ('reviewing' or 'approved' or 'rejected') not in response:
        logging.error('Неожиданный статус домашней работы')

    return response.get('current_date')


def parse_status(homework):
    """
    Extracts a status from the information about a homework.
    Returns a corresponding verdict.
    """
    homework_name = homework.get('homework_name')
    status = homework.get('status')

    if not (homework_name and status):
        error_message = 'Отсутствуют ключи "homework_name" и "status"'
        logging.error(error_message)
        raise KeyError(error_message)

    if status in HOMEWORK_VERDICTS:
        verdict = HOMEWORK_VERDICTS[status]
    else:
        error_message = 'Отсутствует верный статус работы'
        logging.error(error_message)
        raise KeyError(error_message)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Base logic of the bot functioning."""
    try:
        check_tokens()
    except NoEnvVarException:
        logging.critical('Отсутствуют обязательные переменные окружения')
        sys.exit()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(timestamp)
            current_timestamp = check_response(response)
            homeworks = response.get('homeworks')
            homework = homeworks[0]
            message = parse_status(homework)
            send_message(bot, message)
        except SendMessageException:
            pass
        except Exception as error:
            error_message = f'Сбой в работе программы: {error}'
            logging.error(error_message)
            send_message(bot, error_message)
        finally:
            time.sleep(RETRY_PERIOD)
            timestamp = current_timestamp


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(stream=stdout)
    logger.addHandler(handler)

    formatter = logging.Formatter(
        '%(asctime)s, %(levelname)s, %(message)s'
    )
    handler.setFormatter(formatter)

    main()
