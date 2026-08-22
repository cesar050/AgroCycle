"""
Caso de uso: Recuperar contraseña olvidada.

Flujo:
1. Usuario ingresa su correo
2. Sistema genera token seguro con expiración de 1 hora
3. Envía enlace al correo con el token
4. Usuario hace clic en el enlace → va al frontend
5. Frontend llama al endpoint de reset con el nuevo password

Por seguridad, si el correo no existe el sistema responde
igual que si existiera — evita enumerar usuarios válidos.
"""
import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.infrastructure.external.email_service import enviar_correo
from app.infrastructure.logging.logger import log_caso_de_uso


class RecuperarPasswordUseCase:

    def __init__(self, db: Session):
        self.db = db

    @log_caso_de_uso('Recuperar Password')
    def ejecutar(self, correo: str, frontend_url: str) -> tuple:
        """
        Genera token de recuperación y envía el correo.

        Args:
            correo: correo del usuario que olvidó su contraseña
            frontend_url: URL base del frontend para construir el enlace

        Returns:
            tuple (dict, int) — siempre responde igual por seguridad
        """
        # Buscar usuario — si no existe respondemos igual por seguridad
        usuario = self._buscar_usuario(correo)

        if usuario:
            # Generar token seguro de 48 caracteres
            token = secrets.token_urlsafe(36)
            expira = datetime.utcnow() + timedelta(hours=1)

            # Guardar token en BD
            self.db.execute(
                text("""
                    UPDATE usuarios
                    SET reset_password_token  = :token,
                        reset_password_expira = :expira
                    WHERE id = CAST(:usuario_id AS uuid)
                """),
                {
                    'token': token,
                    'expira': expira,
                    'usuario_id': usuario['id'],
                }
            )
            self.db.commit()

            # Enviar correo con el enlace
            enlace = f"{frontend_url}/auth/reset-password/{token}"
            self._enviar_correo_recuperacion(
                correo=correo,
                nombre=usuario['nombre'],
                enlace=enlace,
            )

        # Siempre responde igual — no revela si el correo existe
        return {
            'mensaje': 'Si el correo está registrado recibirás un enlace '
                       'de recuperación en los próximos minutos. '
                       'Revisa también tu carpeta de spam.'
        }, 200

    def _buscar_usuario(self, correo: str) -> dict:
        """Busca usuario por correo. Retorna None si no existe."""
        row = self.db.execute(
            text("""
                SELECT id, nombre, apellido, correo, activo
                FROM usuarios
                WHERE correo = :correo
                  AND activo = TRUE
            """),
            {'correo': correo.lower().strip()}
        ).fetchone()

        if not row:
            return None

        return {
            'id': str(row.id),
            'nombre': f"{row.nombre} {row.apellido}",
            'correo': row.correo,
        }

    def _enviar_correo_recuperacion(
        self, correo: str, nombre: str, enlace: str
    ) -> None:
        """Envía el correo HTML de recuperación de contraseña."""
        asunto = 'AgroCycle — Recuperación de contraseña'

        html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head><meta charset="UTF-8"></head>
        <body style="margin:0;padding:0;background:#F8F7F2;
                     font-family:Arial,sans-serif;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td align="center" style="padding:40px 20px;">
                <table width="580" cellpadding="0" cellspacing="0"
                       style="background:#FFFFFF;border-radius:12px;
                              overflow:hidden;box-shadow:0 4px 16px
                              rgba(0,0,0,0.08);">

                  <!-- Header -->
                  <tr>
                    <td style="background:#1B4332;padding:32px 40px;
                               text-align:center;">
                      <h1 style="margin:0;color:#FFFFFF;font-size:22px;
                                 font-weight:700;letter-spacing:-0.02em;">
                        AgroCycle
                      </h1>
                      <p style="margin:4px 0 0;color:rgba(255,255,255,0.7);
                                font-size:13px;">
                        Decisiones informadas, cosechas más productivas
                      </p>
                    </td>
                  </tr>

                  <!-- Contenido -->
                  <tr>
                    <td style="padding:40px;">
                      <h2 style="margin:0 0 16px;color:#1A1A1A;
                                 font-size:20px;font-weight:700;">
                        Hola, {nombre}
                      </h2>
                      <p style="margin:0 0 16px;color:#5C5C5C;
                                font-size:15px;line-height:1.7;">
                        Recibimos una solicitud para restablecer la contraseña
                        de tu cuenta en AgroCycle.
                      </p>
                      <p style="margin:0 0 32px;color:#5C5C5C;
                                font-size:15px;line-height:1.7;">
                        Haz clic en el botón de abajo para crear una nueva
                        contraseña. Este enlace es válido por
                        <strong>1 hora</strong>.
                      </p>

                      <!-- Botón -->
                      <table width="100%" cellpadding="0" cellspacing="0">
                        <tr>
                          <td align="center">
                            <a href="{enlace}"
                               style="display:inline-block;padding:14px 36px;
                                      background:#C8602A;color:#FFFFFF;
                                      font-size:15px;font-weight:700;
                                      text-decoration:none;border-radius:8px;
                                      letter-spacing:0.01em;">
                              Restablecer contraseña
                            </a>
                          </td>
                        </tr>
                      </table>

                      <!-- Enlace alternativo -->
                      <p style="margin:32px 0 0;color:#9A9A9A;
                                font-size:12px;line-height:1.6;">
                        Si el botón no funciona, copia y pega este enlace
                        en tu navegador:
                      </p>
                      <p style="margin:4px 0 0;word-break:break-all;
                                color:#2D6A4F;font-size:12px;">
                        {enlace}
                      </p>

                      <!-- Aviso de seguridad -->
                      <div style="margin-top:32px;padding:16px;
                                  background:#FAF7F2;border-radius:8px;
                                  border-left:3px solid #E9A020;">
                        <p style="margin:0;color:#5C5C5C;font-size:13px;
                                  line-height:1.6;">
                          Si no solicitaste este cambio, ignora este correo.
                          Tu contraseña no cambiará. Por seguridad, este
                          enlace expirará automáticamente en 1 hora.
                        </p>
                      </div>
                    </td>
                  </tr>

                  <!-- Footer -->
                  <tr>
                    <td style="background:#F8F7F2;padding:24px 40px;
                               text-align:center;border-top:1px solid #E2DDD6;">
                      <p style="margin:0;color:#9A9A9A;font-size:12px;
                                line-height:1.6;">
                        AgroCycle — Universidad Nacional de Loja<br>
                        Bosque Seco del Sur del Ecuador
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

        enviar_correo(
            destinatario=correo,
            asunto=asunto,
            html=html,
        )