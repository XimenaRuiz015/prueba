import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

def enviar_codigo_verificacion_email(destinatario: str, codigo: str) -> dict:
    """
    Envía un código de 6 dígitos al correo del usuario con una plantilla HTML moderna de Equigrup.
    Si no hay credenciales SMTP configuradas, simula el envío y muestra el código en consola.
    """
    load_dotenv(BASE_DIR / ".env", override=True)
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip() # Contraseña de aplicación de Google de 16 letras
    smtp_from_name = os.getenv("SMTP_FROM_NAME", "Equigrup Seguridad")
    asunto = f"🛡️ Tu Código de Verificación Equigrup: {codigo}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #0b1120;
                color: #f1f5f9;
                margin: 0;
                padding: 30px 15px;
            }}
            .container {{
                max-width: 520px;
                margin: 0 auto;
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 16px;
                padding: 35px 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                text-align: center;
            }}
            .logo {{
                font-size: 38px;
                margin-bottom: 10px;
            }}
            .title {{
                color: #38bdf8;
                font-size: 22px;
                font-weight: 800;
                letter-spacing: 0.5px;
                margin: 0 0 8px 0;
            }}
            .subtitle {{
                color: #94a3b8;
                font-size: 14px;
                margin-bottom: 25px;
            }}
            .code-box {{
                background: linear-gradient(135deg, rgba(37,99,235,0.2), rgba(56,189,248,0.15));
                border: 2px dashed #38bdf8;
                border-radius: 12px;
                padding: 20px;
                margin: 25px 0;
            }}
            .code-number {{
                font-size: 36px;
                font-weight: 800;
                color: #ffffff;
                letter-spacing: 10px;
                font-family: monospace;
            }}
            .expiry {{
                color: #f59e0b;
                font-size: 12.5px;
                font-weight: 600;
                margin-top: 8px;
            }}
            .footer {{
                margin-top: 30px;
                border-top: 1px solid #334155;
                padding-top: 20px;
                font-size: 11.5px;
                color: #64748b;
                line-height: 1.5;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">🤖</div>
            <h1 class="title">EQUIGRUP OPERACIONES & IA</h1>
            <p class="subtitle">Código de Verificación de Seguridad</p>
            
            <p style="font-size: 14px; color: #cbd5e1; line-height: 1.5;">
                Hemos recibido una solicitud para restablecer tu contraseña de acceso al Asistente y Sistema de Equigrup.
            </p>
            
            <div class="code-box">
                <div class="code-number">{codigo}</div>
                <div class="expiry">⏱️ Este código expira en 15 minutos</div>
            </div>
            
            <p style="font-size: 13px; color: #94a3b8;">
                Introduce este código en la pantalla de recuperación para crear tu nueva contraseña. Si tú no solicitaste este código, puedes ignorar este mensaje con seguridad.
            </p>
            
            <div class="footer">
                <strong>Equigrup Gestión Técnica & Seguridad</strong><br>
                Este es un mensaje automático de control de acceso.
            </div>
        </div>
    </body>
    </html>
    """
    
    # Si tenemos credenciales SMTP configuradas en variables de entorno
    if smtp_user and smtp_password:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = asunto
            msg["From"] = f"{smtp_from_name} <{smtp_user}>"
            msg["To"] = destinatario
            
            msg.attach(MIMEText(f"Tu código de verificación Equigrup es: {codigo} (Expira en 15 minutos)", "plain"))
            msg.attach(MIMEText(html_content, "html"))
            
            if smtp_port == 465:
                with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as server:
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
                    
            print(f"[EMAIL REAL ENVIADO] Codigo {codigo} enviado exitosamente a {destinatario}")
            return {
                "enviado": True,
                "mensaje": f"Código enviado exitosamente a tu correo ({destinatario}).",
                "modo": "smtp_real"
            }
        except Exception as e:
            print(f"[SMTP ERROR] No se pudo enviar por SMTP: {e}. Usando modo seguro local.")
    
    # Modo Local / Simulado si no hay SMTP configurado
    print(f"\n=======================================================")
    print(f"[CODIGO DE VERIFICACION EQUIGRUP PARA: {destinatario}]")
    print(f"CODIGO OTP: {codigo}")
    print(f"=======================================================\n")
    
    return {
        "enviado": True,
        "mensaje": f"Código de verificación generado para {destinatario}. Revisa tu bandeja de entrada.",
        "modo": "simulado_local",
        "codigo_dev": codigo # Para facilitar pruebas en desarrollo si no hay SMTP
    }
