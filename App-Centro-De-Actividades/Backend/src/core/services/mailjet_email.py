import html
import secrets
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from flask import current_app

TEMPORARY_PASSWORD_ALPHABET = 'abcdefghijklmnopqrstuvwxyz0123456789'
TEMPORARY_PASSWORD_LENGTH = 8


class EmailDeliveryError(Exception):
    pass


def generate_temporary_password(length=TEMPORARY_PASSWORD_LENGTH):
    return ''.join(
        secrets.choice(TEMPORARY_PASSWORD_ALPHABET) for _ in range(length)
    )


def send_employee_access_email(*, recipient_email, recipient_name, temporary_password):
    mail_settings = _load_mailjet_settings()
    login_url = current_app.config.get('FRONTEND_LOGIN_URL') or 'http://localhost:5173/login'
    subject = 'Tu acceso temporal a Centro de Actividades'
    text_part = _build_employee_access_text(
        recipient_name=recipient_name,
        temporary_password=temporary_password,
        login_url=login_url,
    )
    html_part = _build_employee_access_html(
        recipient_name=recipient_name,
        temporary_password=temporary_password,
        login_url=login_url,
    )

    message = EmailMessage()
    message['Subject'] = subject
    message['From'] = formataddr(
        (mail_settings['sender_name'], mail_settings['sender_email'])
    )
    message['To'] = recipient_email
    message['Reply-To'] = mail_settings['sender_email']
    message.set_content(text_part)
    message.add_alternative(html_part, subtype='html')

    try:
        # 🚀 CAMBIO: Usamos SMTP_SSL para conectar de forma segura por el puerto 465
        with smtplib.SMTP_SSL(
            mail_settings['host'],
            mail_settings['port'],
            timeout=mail_settings['timeout'],
            context=ssl.create_default_context()
        ) as smtp:
            smtp.ehlo()
            smtp.login(mail_settings['api_key'], mail_settings['secret_key'])
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as error:
        # Podés agregar un print(f"Error real: {error}") temporalmente en tus logs de Render para trackearlo mejor
        print("Error al enviar email con Mailjet:", error)
        raise EmailDeliveryError(
            'No se pudo enviar el email con la contraseña temporal del empleado.'
        ) from error


def _load_mailjet_settings():
    api_key = current_app.config.get('MAILJET_API_KEY', '').strip()
    secret_key = current_app.config.get('MAILJET_SECRET_KEY', '').strip()
    sender_name = current_app.config.get(
        'MAILJET_SENDER_NAME', 'Centro de Actividades'
    ).strip()
    sender_email = _resolve_sender_email()

    if not api_key or not secret_key or not sender_email:
        raise EmailDeliveryError(
            'Falta configurar Mailjet para enviar el email con la contraseña temporal.'
        )

    return {
        'host': current_app.config.get('MAILJET_SMTP_HOST', 'in-v3.mailjet.com'),
        'port': current_app.config.get('MAILJET_SMTP_PORT', 587),
        'timeout': current_app.config.get('MAILJET_SMTP_TIMEOUT', 15),
        'api_key': api_key,
        'secret_key': secret_key,
        'sender_email': sender_email,
        'sender_name': sender_name or 'Centro de Actividades',
    }


def _resolve_sender_email():
    sender_email = current_app.config.get('MAILJET_SENDER_EMAIL', '').strip()
    if sender_email:
        return sender_email

    sender_domain = current_app.config.get('MAILJET_SENDER_DOMAIN', '').strip()
    sender_local_part = current_app.config.get(
        'MAILJET_SENDER_LOCAL_PART', 'no-reply'
    ).strip()

    if not sender_domain:
        return ''

    local_part = sender_local_part or 'no-reply'
    return f'{local_part}@{sender_domain}'


def _build_employee_access_text(*, recipient_name, temporary_password, login_url):
    return (
        f'Hola {recipient_name},\n\n'
        'Te damos la bienvenida a Centro de Actividades. '
        'Un administrador te registró como empleado y por eso te compartimos tu contraseña temporal.\n\n'
        f'Contraseña temporal: {temporary_password}\n\n'
        'Podés iniciar sesión desde este enlace:\n'
        f'{login_url}\n\n'
        'Una vez dentro, te recomendamos cambiar la contraseña lo antes posible.'
    )


def _build_employee_access_html(*, recipient_name, temporary_password, login_url):
    safe_name = html.escape(recipient_name)
    safe_password = html.escape(temporary_password)
    safe_login_url = html.escape(login_url, quote=True)

    return f"""
<!DOCTYPE html>
<html lang=\"es\">
  <body style=\"margin:0;padding:0;background-color:#ececec;color:#4e4e4e;font-family:'Trebuchet MS','Segoe UI',sans-serif;\">
    <table role=\"presentation\" width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"background-color:#ececec;padding:24px 12px;\">
      <tr>
        <td align=\"center\">
          <table role=\"presentation\" width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"max-width:620px;background-color:#ffffff;border:1px solid #b8b8b8;border-radius:20px;overflow:hidden;\">
            <tr>
              <td style=\"padding:32px 32px 20px;background-color:#f3f3f3;border-bottom:1px solid #d6d6d6;\">
                <p style=\"margin:0 0 10px;font-size:13px;letter-spacing:1.2px;text-transform:uppercase;color:#666666;\">Centro de Actividades</p>
                <h1 style=\"margin:0;font-size:34px;line-height:1.05;font-weight:500;color:#111111;\">Tu acceso temporal ya está listo</h1>
              </td>
            </tr>
            <tr>
              <td style=\"padding:28px 32px 32px;\">
                <p style=\"margin:0 0 14px;font-size:17px;line-height:1.6;\">Hola {safe_name},</p>
                <p style=\"margin:0 0 14px;font-size:17px;line-height:1.6;\">Un administrador te registró como empleado en Centro de Actividades. Te enviamos esta contraseña temporal para que puedas ingresar por primera vez al sistema.</p>
                <div style=\"margin:24px 0;padding:18px 20px;border:1px solid #2f2f2f;border-radius:16px;background-color:#f3f3f3;\">
                  <p style=\"margin:0 0 8px;font-size:14px;color:#666666;\">Contraseña temporal</p>
                  <p style=\"margin:0;font-size:28px;line-height:1.2;letter-spacing:2px;font-weight:600;color:#111111;font-family:'Segoe UI',Tahoma,sans-serif;\">{safe_password}</p>
                </div>
                <p style=\"margin:0 0 24px;font-size:16px;line-height:1.6;\">Cuando ingreses, te recomendamos cambiarla lo antes posible para mantener segura tu cuenta.</p>
                <table role=\"presentation\" cellspacing=\"0\" cellpadding=\"0\">
                  <tr>
                    <td align=\"center\" bgcolor=\"#d6d6d6\" style=\"border:2px solid #2f2f2f;border-radius:14px;\">
                      <a href=\"{safe_login_url}\" style=\"display:inline-block;padding:15px 28px;font-size:16px;font-weight:600;line-height:1.2;color:#111111;text-decoration:none;\">Ir al login</a>
                    </td>
                  </tr>
                </table>
                <p style=\"margin:24px 0 0;font-size:14px;line-height:1.6;color:#666666;\">Si no esperabas este mensaje, podés ignorarlo y contactarte con la administración.</p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip()
