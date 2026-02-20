"""
Routes para Formularios de Contacto

Endpoint para envio de emails de contacto:
- POST /send - Enviar mensaje de contacto

Sistema de Email:
- Usa SMTP configurado en settings
- Formato HTML con diseño profesional
- Reply-To apunta al email del remitente
- Validacion de email con EmailStr

No requiere autenticacion (publico).
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, EmailStr

from core.config import settings
from utils.email_utils import send_email_background

router = APIRouter()


class ContactMessage(BaseModel):
    # Schema para mensaje de contacto
    name: str
    email: EmailStr
    phone: str = None
    subject: str
    message: str

""" POST /send - Enviar mensaje de contacto """
@router.post("/send")
def send_contact_email(contact: ContactMessage, background_tasks: BackgroundTasks):
    
    # === CREAR CUERPO HTML ESPECÍFICO DE CONTACTO ===
    html_body = f"""
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
    
    # Añade la tarea de enviar correo a la cola pasándole los argumentos genéricos
    background_tasks.add_task(
        send_email_background,
        to_email=settings.CONTACT_EMAIL, # Destino (Admin)
        subject=f"Contacto Web: {contact.subject}",
        html_body=html_body,
        reply_to=contact.email # Cliente
    )
    
    return {"message": "Correo encolado para envío exitosamente"}

