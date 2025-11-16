from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config import settings

router = APIRouter()

class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    phone: str = None
    subject: str
    message: str

@router.post("/send")
def send_contact_email(contact: ContactMessage):
    """
    Envía un correo electrónico de contacto
    """
    try:
        # Configuracion del correo
        sender_email = settings.SMTP_USER
        receiver_email = settings.CONTACT_EMAIL  # Email donde recibirás los mensajes
        password = settings.SMTP_PASSWORD
        
        # Crear el mensaje
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Contacto Web: {contact.subject}"
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Reply-To"] = contact.email
        
        # Crear el cuerpo del mensaje en HTML
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
        
        # Adjuntar el HTML al mensaje
        part = MIMEText(html, "html")
        msg.attach(part)
        
        # Enviar el correo
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        
        return {"message": "Correo enviado exitosamente"}
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al enviar el correo. Por favor intenta de nuevo más tarde."
        )
