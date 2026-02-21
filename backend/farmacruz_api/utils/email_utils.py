"""
Utilidades para envío de Correos Electrónicos
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

from core.config import settings

# Configurar logging
logger = logging.getLogger(__name__)

def send_email_background(to_email: str, subject: str, html_body: str, reply_to: str = None):
    """
    Función genérica para enviar emails en segundo plano.
    
    :param to_email: Correo destinatario
    :param subject: Asunto del correo
    :param html_body: Cuerpo del correo en HTML
    :param reply_to: Correo para responder iterativo al contacto (opcional)
    """
    try:
        # === VALIDAR CONFIGURACIÓN ===
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.error("SMTP_USER o SMTP_PASSWORD no están configurados en .env")
            raise ValueError("Configuración SMTP incompleta")
        
        if not settings.CONTACT_EMAIL:
            logger.error("CONTACT_EMAIL no está configurado en .env")
            raise ValueError("CONTACT_EMAIL no configurado")
        
        logger.info(f"Intentando enviar email a {to_email}")
        logger.info(f"SMTP Host: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
        logger.info(f"SMTP User: {settings.SMTP_USER}")
        
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
        logger.info("Conectando al servidor SMTP...")
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            logger.info("Iniciando TLS...")
            server.starttls()  # Habilitar TLS
            
            logger.info("Autenticando...")
            server.login(sender_email, password)
            
            logger.info("Enviando mensaje...")
            server.sendmail(sender_email, to_email, msg.as_string())
            
        logger.info(f"✅ Email enviado exitosamente a {to_email}")
        print(f"✅ Email enviado exitosamente a {to_email}")
        
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"❌ Error de autenticación SMTP: {str(e)}"
        logger.error(error_msg)
        print(error_msg)
        raise
        
    except smtplib.SMTPException as e:
        error_msg = f"❌ Error SMTP: {str(e)}"
        logger.error(error_msg)
        print(error_msg)
        raise
        
    except Exception as e:
        error_msg = f"❌ Error enviando email a {to_email}: {str(e)}"
        logger.error(error_msg)
        print(error_msg)
        raise

