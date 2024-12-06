import asyncio
from pathlib import Path

import aiosmtplib
from email.message import EmailMessage
from loguru import logger

import config

async def send_email(subject: str, to_email: str, file_path: Path = None, text: str = None):
    log = logger.bind(email=to_email, subject=subject, file_path=file_path, text=text)
    log.info("Отправка письма...")
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = config.smtp_user  # Замените на свой email
    msg['To'] = to_email

    # Добавление текста письма
    if text is not None:
        msg.set_content(text)
    if file_path is not None:
        # Открытие и добавление Excel файла как вложения
        with open(file_path, 'rb') as f:
            file_data = f.read()
            msg.add_attachment(file_data,
                               maintype='application',
                               subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                               filename=file_path.name)

    # Отправка письма
    try:
        async with aiosmtplib.SMTP(hostname=config.smtp_host, port=config.smtp_port, use_tls=True) as smtp:
            await smtp.login(config.smtp_user, config.smtp_pass)
            await smtp.send_message(msg)
            log.info("Письмо успешно отправлено!")
    except Exception as e:
        log.exception(f"Ошибка отправки письма: {e}")
