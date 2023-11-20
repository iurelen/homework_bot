import os
import time
import requests
import logging
import sys
import telegram

from dotenv import load_dotenv
from http import HTTPStatus

from exceptions import RequestError


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
# если убрать эту строку - бот прекрасно работает, но тесты не проходят:
# NameError: name 'logger' is not defined
# Не пойму, что сделать


def check_tokens():
    """Проверка доступности переменных окружения."""
    env_vars = [
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID
    ]

    return all(env_vars)


def send_message(bot, message):
    """отправляет сообщение в Telegram чат."""
    try:
        logger.debug(f'Отправка сообщения в Telegram. Текст: {message}')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logger.error(f'Ошибка отправки сообщения: {error}')
    else:
        logger.info('Сообщение успешно отправлено')


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    payload = {'from_date': timestamp}
    try:
        logger.debug('Запрос к API-сервису {ENDPOINT}.')
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except Exception as error:
        logger.error(f'Ошибка при запросе к серверу API: {error}')
    else:
        logger.debug('Запрос к эндпоинту API-сервиса выполнен. '
                     f'Статус-код ответа {response.status_code}')
        if response.status_code != HTTPStatus.OK:
            message = ('Ошибка при запросе к серверу API с параметрами '
                       f'{HEADERS} и {payload}. '
                       f'Статус-код ответа {response.status_code}')
            logger.warning(message)
            raise RequestError(message)
        return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации из урока."""
    if not isinstance(response, dict):
        raise TypeError('Ошибка данных - отсутствует словарь')

    homework_list = response.get('homeworks')

    if not isinstance(homework_list, list):
        raise TypeError('Ошибка данных - отсутствует список')

    if 'homeworks' not in response:
        raise KeyError('Ошибка данных - в словаре нет ключа "homeworks"')

    if len(homework_list) > 0:
        homework = homework_list[0]
        logger.info('Получено обновление')
        return homework
    else:
        logger.debug('Обновление отсутствует')


def parse_status(homework):
    """Извлекает статус домашней работы из ответа API."""
    if 'homework_name' not in homework:
        raise KeyError('Ошибка данных - в словаре нет ключа "homework_name"')

    if 'status' not in homework:
        raise KeyError('Ошибка данных - в словаре нет ключа "status"')

    if homework['status'] not in HOMEWORK_VERDICTS:
        raise KeyError('Ошибка данных - неизвестный статус')

    homework_name = homework.get('homework_name')
    status = homework.get('status')
    verdict = HOMEWORK_VERDICTS.get(status)
    message = (f'Изменился статус проверки работы "{homework_name}". '
               f'{verdict}')

    logger.debug(message)
    return message


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Переменная окружения недоступна')
        sys.exit()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_sent_message = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            timestamp = response.get('current_date')
            homework = check_response(response)
            if homework:
                message = parse_status(homework)
                if last_sent_message != message:
                    send_message(bot, message)
                    last_sent_message = message
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if last_sent_message != message:
                send_message(bot, message)
                last_sent_message = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(handler)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    main()
