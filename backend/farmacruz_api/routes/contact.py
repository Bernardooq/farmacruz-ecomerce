"""
Routes para Formularios de Contacto

Endpoint para envío de emails de contacto:
- POST /send - Enviar mensaje de contacto

Sistema de Email:
- Usa SMTP configurado en settings
- Formato HTML con diseño profesional
- Reply-To apunta al email del remitente
- Validación de email con EmailStr

No requiere autenticación (público).
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from core.config import settings

router = APIRouter()


class ContactMessage(BaseModel):
    """
    Schema para mensaje de contacto
    
    Campos requeridos:
    - name: Nombre del remitente
    - email: Email del remitente (validado)
    - subject: Asunto del mensaje
    - message: Contenido del mensaje
    
    Campos opcionales:
    - phone: Teléfono del remitente
    """
    name: str
    email: EmailStr
    phone: str = None
    subject: str
    message: str


@router.post("/send")
def send_contact_email(contact: ContactMessage):
    """
    Envía un email de contacto al administrador
    
    El email se envía usando SMTP configurado en settings:
    - SMTP_HOST: Servidor SMTP
    - SMTP_PORT: Puerto SMTP
    - SMTP_USER: Usuario de autenticación
    - SMTP_PASSWORD: Contraseña
    - CONTACT_EMAIL: Destinatario (admin)
    
    El email incluye:
    - Nombre, email y teléfono del remitente
    - Asunto y mensaje
    - Reply-To para responder fácilmente
    - Formato HTML profesional
    
    Permisos: Público (no requiere autenticación)
    
    Returns:
        Mensaje de éxito
    
    Raises:
        500: Error al enviar el email (SMTP, configuración, etc.)
    """
    try:
        # === CONFIGURACIÓN DEL EMAIL ===
        sender_email = settings.SMTP_USER
        receiver_email = settings.CONTACT_EMAIL  # Admin email
        password = settings.SMTP_PASSWORD
        
        # === CREAR MENSAJE ===
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Contacto Web: {contact.subject}"
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Reply-To"] = contact.email  # Para responder directamente al cliente
        
        # === CREAR CUERPO HTML ===
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
              <h2 style="color: #63c1a5; border-bottom: 2px solid #63c1a5; padding-bottom: 10px;">
                Nuevo Mensaje de Contacto
              </h2>
              
              <div style="margin: 20px 0;">
                <p><strong>Nombre:</strong> {contact.name}</p>
                <p><strong>Email:</strong> <a href="mailto:{contact.email}">{contact.email}</a></p>
                {f'<p><strong>Teléfono:</strong> {contact.phone}</p>' if contact.phone else ''}
                <p><strong>Asunto:</strong> {contact.subject}</p>
              </div>
              
              <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #555;">Mensaje:</h3>
                <p style="white-space: pre-wrap;">{contact.message}</p>
              </div>
              
              <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
              
              <p style="font-size: 12px; color: #888;">
                Este mensaje fue enviado desde el formulario de contacto de Farmacruz.
              </p>
            </div>
          </body>
        </html>
        """
        
        # === ADJUNTAR HTML ===
        part = MIMEText(html, "html")
        msg.attach(part)
        
        # === ENVIAR EMAIL ===
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()  # Habilitar TLS
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        
        return {"message": "Correo enviado exitosamente"}
        
    except smtplib.SMTPException as e:
        # Error específico de SMTP
        print(f"SMTP Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al enviar el correo. Verifica la configuración SMTP."
        )
    except Exception as e:
        # Cualquier otro error
        print(f"Error sending email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al enviar el correo. Por favor intenta de nuevo más tarde."
        )
