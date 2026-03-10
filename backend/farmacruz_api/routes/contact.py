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

from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Request
from pydantic import BaseModel, EmailStr, Field
import logging

from core.config import settings, TURNSTILE_SECRET_KEY
from utils.email_utils import send_email_background

router = APIRouter()
logger = logging.getLogger(__name__)


class ContactMessage(BaseModel):
    # Schema para mensaje de contacto con validacion de longitud
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(None, max_length=30)
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=5000)

""" POST /send - Enviar mensaje de contacto """
@router.post("/send")
def send_contact_email(contact: ContactMessage, request: Request, background_tasks: BackgroundTasks):
    
    # Validar Cloudflare Turnstile (si está configurado)
    if TURNSTILE_SECRET_KEY:
        import httpx
        captcha_token = request.headers.get("X-Turnstile-Token", "")
        
        if not captcha_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verificación CAPTCHA requerida"
            )
        
        try:
            response = httpx.post(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                data={
                    "secret": TURNSTILE_SECRET_KEY,
                    "response": captcha_token
                },
                timeout=10.0
            )
            
            # Si Cloudflare responde un error 500 o rate limit, dejamos pasar
            if response.status_code != 200:
                logger.warning(f"Turnstile API falló en contacto con status {response.status_code}. Permitiendo envío por fallback.")
                pass
            else:
                result = response.json()
                if not result.get("success"):
                    logger.warning(f"Turnstile rechazó el token de contacto: {result.get('error-codes')}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Verificación CAPTCHA fallida. Intenta de nuevo."
                    )
        except httpx.RequestError as e:
            # Si Turnstile está caído/timeout, dejamos que el formulario pase
            logger.warning(f"Error de red contactando Turnstile en contacto: {str(e)}. Permitiendo envío por fallback.")
            pass
    
    try:
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
        
        logger.info(f"Encolando envío de email de contacto de {contact.name} ({contact.email})")
        
        # Enviar email de forma asíncrona real con BackgroundTasks
        background_tasks.add_task(
            send_email_background,
            to_email=settings.CONTACT_EMAIL,
            subject=f"Contacto Web: {contact.subject}",
            html_body=html_body,
            reply_to=contact.email
        )
        
        logger.info(f"Email encolado para {settings.CONTACT_EMAIL}")
        
        return {"message": "Mensaje enviado exitosamente"}
        
    except Exception as e:
        logger.error(f"Error enviando email de contacto: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al enviar el mensaje: {str(e)}"
        )
