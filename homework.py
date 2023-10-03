import logging
import os
import sys
import time
from sys import stdout

import requests
import telegram
from dotenv import load_dotenv

from exceptions import NoEnvVarError, UnexpectedStatusCode


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

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=stdout)
logger.addHandler(handler)

formatter = logging.Formatter(
    '%(asctime)s, %(levelname)s, %(message)s'
)
handler.setFormatter(formatter)


def check_tokens():
    """Checks the accessibility of the environmental variables."""
    message = 'Отсутствуют обязательные переменные окружения'
    if (
        PRACTICUM_TOKEN
        or TELEGRAM_TOKEN
        or TELEGRAM_CHAT_ID
    ) is None:
        logging.critical(message)
        raise NoEnvVarError(message)


def send_message(bot, message):
    """Sends a message to Telegram chat."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug('Сообщение успешно отправлено!')
    except telegram.TelegramError as error:
        logging.error(f'Сбой при отправке сообщения:{error}')


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
    if response.status_code != 200:
        logging.error('Неожиданный статус запроса')
        raise UnexpectedStatusCode(
            'Неожиданный статус запроса:' + str(response.status_code)
        )

    response = response.json()
    return response


def check_response(response):
    """Checks an API answer for compliance with the documentation."""
    if type(response) != dict:
        error_message = (
            f'API структура данных не соответствует ожиданиям: '
            f'получен тип {type(response)} вместо словаря'
        )
        logging.error(error_message)
        raise TypeError(error_message)
    if type(response.get('homeworks')) != list:
        error_message = (
            f'Тип данных ключа не соответствует ожиданиям: '
            f'получен тип {type(response.get("homeworks"))} '
            f'вместо списка'
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
    if response.get('status') != (
        'reviewing' or 'approved' or 'rejected'
    ):
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

    for verdict in HOMEWORK_VERDICTS:
        if status == 'approved':
            verdict = HOMEWORK_VERDICTS['approved']
        elif status == 'reviewing':
            verdict = HOMEWORK_VERDICTS['reviewing']
        elif status == 'rejected':
            verdict = HOMEWORK_VERDICTS['rejected']
        else:
            error_message = 'Отсутствует верный статус работы'
            logging.error(error_message)
            raise KeyError(error_message)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Base logic of the bot functioning."""
    try:
        check_tokens()
    except NoEnvVarError:
        sys.exit()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(timestamp)
            current_date = check_response(response)
            homeworks = response.get('homeworks')
            homework = homeworks[0]
            message = parse_status(homework)
            send_message(bot, message)
        except (
            NoEnvVarError,
            telegram.TelegramError,
            requests.exceptions.HTTPError,
            requests.exceptions.RequestException,
            UnexpectedStatusCode,
            KeyError,
            TypeError,
            Exception,
        ) as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)
            timestamp = current_date


if __name__ == '__main__':
    main()
