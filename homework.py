import os
import time
import requests
import logging
import sys
import telegram

from dotenv import load_dotenv
from http import HTTPStatus

from exceptions import TokenError, RequestError


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
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)


def check_tokens():
    """Проверка доступности переменных окружения."""
    env_vars = [
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID
    ]

    for variable in env_vars:
        if not variable:
            message = 'TokenError: переменная окружения недоступна'
            logger.critical(message)
            raise TokenError(message)
    return True


def send_message(bot, message):
    """отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('Сообщение успешно отправлено')
    except Exception as error:
        logger.error(f'Ошибка отправки сообщения: {error}')


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        if response.status_code == HTTPStatus.OK:
            logger.debug('Успешный запрос к эндпоинту API-сервиса. '
                         f'Статус-код ответа {response.status_code}')
            return response.json()
    except Exception as error:
        logger.error(f'Ошибка при запросе к серверу API: {error}')

    if response.status_code != HTTPStatus.OK:
        message = ('Ошибка при запросе к серверу API. '
                   f'Статус-код ответа {response.status_code}')
        logger.warning(message)
        raise RequestError(message)


def check_response(response):
    """Проверяет ответ API на соответствие документации из урока."""
    if not isinstance(response, dict):
        logger.warning('Ошибка данных')
        raise TypeError
    homework_list = response.get('homeworks')
    if not isinstance(homework_list, list):
        logger.warning('Ошибка данных')
        raise TypeError
    if 'homeworks' in response:
        if len(homework_list) > 0:
            homework = homework_list[0]
            if 'homework_name' and 'status' in homework:
                if homework['status'] in HOMEWORK_VERDICTS:
                    logger.info('Получено обновление')
                    return homework
                else:
                    message = 'Ошибка данных - неизвестный статус'
                    logger.error(message)
                    raise KeyError(message)
            else:
                message = ('Ошибка данных - в словаре нет ключа '
                           '"homework_name" или "status"')
                logger.error(message)
                raise KeyError(message)
        else:
            logger.debug('Обновление отсутствует')
    else:
        message = 'Ошибка данных - в словаре нет ключа "homeworks"'
        logger.error(message)
        raise KeyError(message)


def parse_status(homework):
    """Извлекает статус домашней работы из ответа API."""
    if homework['status'] in HOMEWORK_VERDICTS:
        if 'homework_name' in homework:
            homework_name = homework['homework_name']
            status = homework['status']
            verdict = HOMEWORK_VERDICTS[status]
            message = (f'Изменился статус проверки работы "{homework_name}". '
                       f'{verdict}')
            logger.debug(message)
            return message
        else:
            message = ('Ошибка данных - в словаре нет ключа '
                       '"homework_name"')
            logger.error(message)
            raise KeyError(message)
    else:
        message = 'Ошибка данных - неизвестный статус'
        logger.error(message)
        raise KeyError(message)


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time()) - 3 * 24 * 3600
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
    main()
