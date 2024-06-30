# Телеграм бот-ассистент для отслеживания статуса работы на внешнем сервисе

![python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
![API](https://img.shields.io/badge/API-3b3b3b?style=for-the-badge&logoColor=white)
![JSON](https://img.shields.io/badge/JSON-03ac13?style=for-the-badge&logoColor=white)

Этот проект представляет собой Telegram-бота, который автоматически проверяет статус работы на внешнем сервисе. Бот периодически опрашивает API сервиса и уведомляет пользователя о заданных событиях.

## Основные функции бота:
- **Автоматический мониторинг**: Бот опрашивает API каждые 10 минут для получения актуальной информации о статусе работы.
- **Уведомления**: При изменении статуса в JSON-ответе бот отправляет уведомление в Telegram указанному пользователю. Уведомления включают информацию о текущем статусе работы.
- **Логирование**: Бот ведет журнал своей работы, фиксируя ключевые моменты и проблемы. В случае важных проблем бот также отправляет уведомление в Telegram.