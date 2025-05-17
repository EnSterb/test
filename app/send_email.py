import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv
import os

load_dotenv(dotenv_path='.env')

mail_from = os.getenv("GMAIL")
mail_password = os.getenv("GMAILPASSWORD")

def send_email(email_from, email_password, email_to, subject, body, is_html=False):
    msg = MIMEMultipart()
    msg['From'] = email_from
    msg['To'] = email_to
    msg['Subject'] = subject

    # Выбор типа содержимого: plain text или HTML
    content_type = 'html' if is_html else 'plain'
    msg.attach(MIMEText(body, content_type))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(email_from, email_password)

        server.sendmail(email_from, email_to, msg.as_string())
        server.quit()

        print("Email sent!")
    except Exception as e:
        print(e)


def send_password_reset_email(email: str, reset_link: str):
    subject = "Запрос на сброс пароля"

    html_body = f"""
    <html>
        <body>
            <p>Вы запросили сброс пароля.</p>
            <p>Пожалуйста, перейдите по ссылке ниже, чтобы сбросить пароль:</p>
            <p><a href="{reset_link}">Нажмите здесь, чтобы сбросить пароль</a></p>
            <p>Эта ссылка будет действительна в течение 30 минут.</p>
            <p>Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.</p>
        </body>
    </html>
    """

    send_email(
        email_from=os.getenv("GMAIL"),
        email_password=os.getenv("GMAILPASSWORD"),
        email_to=email,
        subject=subject,
        body=html_body,
        is_html=True
    )
