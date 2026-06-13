import os
from dotenv import load_dotenv
from flask import Flask
from src.core.services.mailjet_email import send_password_recovery_email

load_dotenv('.env')

app = Flask(__name__)
app.config['MAILJET_API_KEY'] = os.environ.get('MAILJET_API_KEY')
app.config['MAILJET_SECRET_KEY'] = os.environ.get('MAILJET_SECRET_KEY')
app.config['MAILJET_SENDER_DOMAIN'] = os.environ.get('MAILJET_SENDER_DOMAIN')
app.config['MAILJET_SENDER_LOCAL_PART'] = os.environ.get('MAILJET_SENDER_LOCAL_PART')
app.config['MAILJET_SENDER_EMAIL'] = os.environ.get('MAILJET_SENDER_EMAIL')
app.config['MAILJET_SENDER_NAME'] = os.environ.get('MAILJET_SENDER_NAME')

with app.app_context():
    try:
        send_password_recovery_email(
            recipient_email='test@example.com',
            recipient_name='Test User',
            token='test-token'
        )
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")
