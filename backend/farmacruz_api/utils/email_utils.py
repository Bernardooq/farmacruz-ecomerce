"""
Utilidades para envío de Correos Electrónicos
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from core.config import settings

def send_email_background(to_email: str, subject: str, html_body: str, reply_to: str = None):
    """
    Función genérica para enviar emails en segundo plano.
    
    :param to_email: Correo destinatario
    :param subject: Asunto del correo
    :param html_body: Cuerpo del correo en HTML
    :param reply_to: Correo para responder iterativo al contacto (opcional)
    """
    try:
        # === CONFIGURACION DEL EMAIL ===
        sender_email = settings.SMTP_USER
        password = settings.SMTP_PASSWORD
        
        # === CREAR MENSAJE ===
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = to_email
        
        if reply_to:
            msg["Reply-To"] = reply_to  # Para responder directamente a un cliente (ej. forms)
            
        # === ADJUNTAR HTML ===
        part = MIMEText(html_body, "html")
        msg.attach(part)
        
        # === ENVIAR EMAIL ===
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()  # Habilitar TLS
            server.login(sender_email, password)
            server.sendmail(sender_email, to_email, msg.as_string())
            
        print(f"Email enviado exitosamente a {to_email}")
        
    except Exception as e:
        print(f"Error enviando email a {to_email}: {str(e)}")
