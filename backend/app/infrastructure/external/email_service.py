"""
Servicio de envio de correos electronicos.
Usa SMTP_SSL puerto 465 para compatibilidad con Docker.
"""
from flask import current_app
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import os

mail = Mail()


def get_serializer():
    return URLSafeTimedSerializer(os.getenv('SECRET_KEY', 'dev_secret'))


def generar_token_verificacion(correo: str) -> str:
    """Genera token firmado para verificar el correo."""
    serializer = get_serializer()
    return serializer.dumps(correo, salt='verificacion-correo')


def verificar_token(token: str, expiracion_segundos: int = 3600):
    """Verifica token y retorna el correo si es valido."""
    serializer = get_serializer()
    try:
        correo = serializer.loads(
            token,
            salt='verificacion-correo',
            max_age=expiracion_segundos
        )
        return correo
    except Exception:
        return None


def enviar_correo_verificacion(correo: str, nombre: str, token: str) -> bool:
    """
    Envia correo de verificacion con template HTML profesional.
    Usa SSL en puerto 465 para funcionar dentro de Docker.
    """
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:4200')
    enlace = f"{frontend_url}/verificar-correo/{token}"

    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verifica tu cuenta en AgroCycle</title>
    </head>
    <body style="margin:0; padding:0; background-color:#f4f7f4; font-family: Arial, sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f7f4; padding:40px 0;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0"
                           style="background-color:#ffffff; border-radius:12px; overflow:hidden;
                                  box-shadow:0 4px 20px rgba(0,0,0,0.08);">

                        <!-- HEADER -->
                        <tr>
                            <td style="background-color:#1B4332; padding:35px 40px; text-align:center;">
                                <div style="display:inline-block; background-color:#2D6A4F;
                                            border-radius:50%; width:72px; height:72px;
                                            text-align:center; margin-bottom:16px;">
                                    <svg width="38" height="38" viewBox="0 0 24 24" fill="none"
                                         xmlns="http://www.w3.org/2000/svg"
                                         style="margin-top:17px;">
                                        <path d="M12 22V12M12 12C12 12 7 10 5 5C9 4 13 7 12 12Z
                                                 M12 12C12 12 17 10 19 5C15 4 11 7 12 12Z"
                                              stroke="#D8F3DC" stroke-width="1.8"
                                              stroke-linecap="round" stroke-linejoin="round"/>
                                        <path d="M5 20C7 18 10 17 12 17C14 17 17 18 19 20"
                                              stroke="#D8F3DC" stroke-width="1.8"
                                              stroke-linecap="round"/>
                                    </svg>
                                </div>
                                <h1 style="color:#ffffff; margin:0 0 6px 0; font-size:28px;
                                           font-weight:bold; letter-spacing:1px;">AgroCycle</h1>
                                <p style="color:#D8F3DC; margin:0; font-size:14px;">
                                    Decisiones informadas, cosechas mas productivas
                                </p>
                            </td>
                        </tr>

                        <!-- BANNER -->
                        <tr>
                            <td style="background:linear-gradient(135deg, #2D6A4F 0%, #1B4332 100%);
                                       padding:35px 40px; text-align:center;">
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td width="33%" style="text-align:center; padding:0 10px;">
                                            <svg width="44" height="44" viewBox="0 0 24 24" fill="none"
                                                 xmlns="http://www.w3.org/2000/svg">
                                                <path d="M9 3L3 6V21L9 18L15 21L21 18V3L15 6L9 3Z"
                                                      stroke="#D8F3DC" stroke-width="1.8"
                                                      stroke-linecap="round" stroke-linejoin="round"/>
                                                <path d="M9 3V18M15 6V21"
                                                      stroke="#D8F3DC" stroke-width="1.8"
                                                      stroke-linecap="round"/>
                                            </svg>
                                            <p style="color:#D8F3DC; font-size:13px;
                                                      margin:10px 0 0 0; font-weight:bold;">
                                                Mapas interactivos
                                            </p>
                                        </td>
                                        <td width="33%" style="text-align:center; padding:0 10px;">
                                            <svg width="44" height="44" viewBox="0 0 24 24" fill="none"
                                                 xmlns="http://www.w3.org/2000/svg">
                                                <path d="M20 17.58A5 5 0 0018 8h-1.26A8 8 0 104 15.25"
                                                      stroke="#D8F3DC" stroke-width="1.8"
                                                      stroke-linecap="round" stroke-linejoin="round"/>
                                                <path d="M8 19v2M12 17v4M16 19v2"
                                                      stroke="#D8F3DC" stroke-width="1.8"
                                                      stroke-linecap="round"/>
                                            </svg>
                                            <p style="color:#D8F3DC; font-size:13px;
                                                      margin:10px 0 0 0; font-weight:bold;">
                                                Clima en tiempo real
                                            </p>
                                        </td>
                                        <td width="33%" style="text-align:center; padding:0 10px;">
                                            <svg width="44" height="44" viewBox="0 0 24 24" fill="none"
                                                 xmlns="http://www.w3.org/2000/svg">
                                                <path d="M18 20V10M12 20V4M6 20V14"
                                                      stroke="#D8F3DC" stroke-width="1.8"
                                                      stroke-linecap="round" stroke-linejoin="round"/>
                                            </svg>
                                            <p style="color:#D8F3DC; font-size:13px;
                                                      margin:10px 0 0 0; font-weight:bold;">
                                                Estimacion de cosecha
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <!-- BIENVENIDA -->
                        <tr>
                            <td style="padding:45px 50px 25px 50px; text-align:center;">
                                <h2 style="color:#1B4332; font-size:24px; margin:0 0 16px 0;">
                                    Bienvenido, {nombre}
                                </h2>
                                <p style="color:#555555; font-size:16px; line-height:1.8; margin:0;">
                                    Tu cuenta en AgroCycle ha sido creada exitosamente.
                                    Para comenzar a gestionar tus temporadas agricolas
                                    necesitas <strong style="color:#1B4332;">verificar tu
                                    correo electronico</strong>.
                                </p>
                            </td>
                        </tr>

                        <!-- BOTON -->
                        <tr>
                            <td style="padding:20px 50px 45px 50px; text-align:center;">
                                <a href="{enlace}"
                                   style="display:inline-block; background-color:#1B4332;
                                          color:#ffffff; padding:18px 50px; border-radius:8px;
                                          text-decoration:none; font-size:17px; font-weight:bold;">
                                    Verificar mi cuenta
                                </a>
                                <p style="color:#999999; font-size:13px; margin:18px 0 0 0;">
                                    Este enlace expira en <strong>1 hora</strong>
                                </p>
                            </td>
                        </tr>

                        <!-- FUNCIONALIDADES -->
                        <tr>
                            <td style="padding:30px 40px 40px 40px; background-color:#f9fdf9;
                                       border-top:2px solid #D8F3DC;">
                                <p style="color:#1B4332; font-size:15px; font-weight:bold;
                                          text-align:center; margin:0 0 25px 0;">
                                    Con AgroCycle podras:
                                </p>
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td width="50%" style="padding:0 10px 20px 10px; vertical-align:top;">
                                            <table cellpadding="0" cellspacing="0">
                                                <tr>
                                                    <td width="30" style="vertical-align:top; padding-top:2px;">
                                                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
                                                             xmlns="http://www.w3.org/2000/svg">
                                                            <circle cx="12" cy="12" r="10"
                                                                    stroke="#1B4332" stroke-width="1.8"/>
                                                            <path d="M9 11l3 3 3-3"
                                                                  stroke="#1B4332" stroke-width="1.8"
                                                                  stroke-linecap="round"
                                                                  stroke-linejoin="round"/>
                                                        </svg>
                                                    </td>
                                                    <td style="padding-left:10px;">
                                                        <p style="color:#1B4332; font-size:13px;
                                                                  font-weight:bold; margin:0 0 3px 0;">
                                                            Control de gastos e ingresos
                                                        </p>
                                                        <p style="color:#777; font-size:12px; margin:0;">
                                                            Registra tu inversion y calcula
                                                            la rentabilidad de cada temporada
                                                        </p>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                        <td width="50%" style="padding:0 10px 20px 10px; vertical-align:top;">
                                            <table cellpadding="0" cellspacing="0">
                                                <tr>
                                                    <td width="30" style="vertical-align:top; padding-top:2px;">
                                                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
                                                             xmlns="http://www.w3.org/2000/svg">
                                                            <rect x="3" y="4" width="18" height="18"
                                                                  rx="2" stroke="#1B4332" stroke-width="1.8"/>
                                                            <path d="M16 2v4M8 2v4M3 10h18"
                                                                  stroke="#1B4332" stroke-width="1.8"
                                                                  stroke-linecap="round"/>
                                                        </svg>
                                                    </td>
                                                    <td style="padding-left:10px;">
                                                        <p style="color:#1B4332; font-size:13px;
                                                                  font-weight:bold; margin:0 0 3px 0;">
                                                            Seguimiento fenologico
                                                        </p>
                                                        <p style="color:#777; font-size:12px; margin:0;">
                                                            Conoce la etapa de tu maiz
                                                            dia a dia hasta la cosecha
                                                        </p>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td width="50%" style="padding:0 10px 10px 10px; vertical-align:top;">
                                            <table cellpadding="0" cellspacing="0">
                                                <tr>
                                                    <td width="30" style="vertical-align:top; padding-top:2px;">
                                                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
                                                             xmlns="http://www.w3.org/2000/svg">
                                                            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z"
                                                                  stroke="#1B4332" stroke-width="1.8"
                                                                  stroke-linecap="round"
                                                                  stroke-linejoin="round"/>
                                                            <path d="M14 2v6h6M16 13H8M16 17H8"
                                                                  stroke="#1B4332" stroke-width="1.8"
                                                                  stroke-linecap="round"/>
                                                        </svg>
                                                    </td>
                                                    <td style="padding-left:10px;">
                                                        <p style="color:#1B4332; font-size:13px;
                                                                  font-weight:bold; margin:0 0 3px 0;">
                                                            Reportes tecnicos en PDF
                                                        </p>
                                                        <p style="color:#777; font-size:12px; margin:0;">
                                                            Documentos profesionales firmados
                                                            por tu agronomo
                                                        </p>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                        <td width="50%" style="padding:0 10px 10px 10px; vertical-align:top;">
                                            <table cellpadding="0" cellspacing="0">
                                                <tr>
                                                    <td width="30" style="vertical-align:top; padding-top:2px;">
                                                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
                                                             xmlns="http://www.w3.org/2000/svg">
                                                            <circle cx="12" cy="8" r="4"
                                                                    stroke="#1B4332" stroke-width="1.8"/>
                                                            <path d="M6 20v-1a6 6 0 0112 0v1"
                                                                  stroke="#1B4332" stroke-width="1.8"
                                                                  stroke-linecap="round"/>
                                                        </svg>
                                                    </td>
                                                    <td style="padding-left:10px;">
                                                        <p style="color:#1B4332; font-size:13px;
                                                                  font-weight:bold; margin:0 0 3px 0;">
                                                            Modulo del agronomo
                                                        </p>
                                                        <p style="color:#777; font-size:12px; margin:0;">
                                                            Tu tecnico puede seguir tu cultivo
                                                            y darte recomendaciones
                                                        </p>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <!-- ENLACE ALTERNATIVO -->
                        <tr>
                            <td style="padding:22px 50px; background-color:#fff8e7;
                                       border-top:1px solid #f0e6c8;">
                                <p style="color:#856404; font-size:13px; margin:0; text-align:center;">
                                    Si el boton no funciona, copia este enlace en tu navegador:
                                </p>
                                <p style="word-break:break-all; color:#1B4332; font-size:12px;
                                          text-align:center; margin:8px 0 0 0;">
                                    {enlace}
                                </p>
                            </td>
                        </tr>

                        <!-- FOOTER -->
                        <tr>
                            <td style="background-color:#1B4332; padding:28px 40px; text-align:center;">
                                <p style="color:#D8F3DC; font-size:13px; margin:0 0 8px 0;">
                                    Si no creaste esta cuenta, puedes ignorar este correo.
                                </p>
                                <p style="color:#52b788; font-size:12px; margin:0;">
                                    2026 AgroCycle — Universidad Nacional de Loja, Ecuador
                                </p>
                                <p style="color:#52b788; font-size:11px; margin:8px 0 0 0;">
                                    Este correo fue enviado automaticamente,
                                    por favor no respondas a este mensaje.
                                </p>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    try:
        mensaje = Message(
            subject="Verifica tu cuenta en AgroCycle",
            recipients=[correo],
            html=html
        )
        mail.send(mensaje)
        current_app.logger.info(f"Correo de verificacion enviado a {correo}")
        return True
    except Exception as e:
        current_app.logger.error(f"Error enviando correo a {correo}: {str(e)}")
        return False

def enviar_correo(
    destinatario: str,
    asunto: str,
    html: str,
) -> bool:
    """
    Función genérica para enviar cualquier correo HTML.
    Reutilizable para recuperación de contraseña, notificaciones, etc.

    Args:
        destinatario: correo del destinatario
        asunto: asunto del correo
        html: contenido HTML del correo

    Returns:
        True si se envió, False si hubo error
    """
    try:
        msg = Message(
            subject=asunto,
            recipients=[destinatario],
            html=html,
        )
        mail.send(msg)
        return True
    except Exception as e:
        import logging
        logging.error(f'Error enviando correo a {destinatario}: {str(e)}')
        return False