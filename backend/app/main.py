"""
Punto de entrada de la aplicación Flask de AgroCycle.
Integra seguridad completa: headers HTTP, CORS restrictivo,
rate limiting con Redis y manejo global de errores.
"""
from flask import Flask
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

load_dotenv()


def create_app():
    app = Flask(__name__)

    # ----------------------------------------------------------------
    # Configuración general
    # ----------------------------------------------------------------
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_secret')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev_jwt_secret')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(
        os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 900)
    )
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['FLASK_ENV'] = os.getenv('FLASK_ENV', 'development')

    # ----------------------------------------------------------------
    # Configuración de correo
    # ----------------------------------------------------------------
    app.config['MAIL_SERVER']         = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT']           = int(os.getenv('MAIL_PORT', 465))
    app.config['MAIL_USE_TLS']        = False
    app.config['MAIL_USE_SSL']        = True
    app.config['MAIL_USERNAME']       = os.getenv('MAIL_USERNAME', '')
    app.config['MAIL_PASSWORD']       = os.getenv('MAIL_PASSWORD', '')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', '')

    # ----------------------------------------------------------------
    # Seguridad — orden importante:
    # 1. CORS antes de JWT para que OPTIONS funcione
    # 2. Headers después de CORS
    # 3. Rate limiter después de headers
    # 4. Error handlers al final
    # ----------------------------------------------------------------
    from app.infrastructure.security.cors import configurar_cors
    configurar_cors(app)

    from app.infrastructure.security.headers import configurar_headers_seguridad
    configurar_headers_seguridad(app)

    from app.infrastructure.security.rate_limiter import limiter
    limiter.init_app(app)

    from app.infrastructure.security.error_handlers import registrar_error_handlers
    registrar_error_handlers(app)

    # ----------------------------------------------------------------
    # JWT
    # ----------------------------------------------------------------
    JWTManager(app)

    # ----------------------------------------------------------------
    # Correo
    # ----------------------------------------------------------------
    from app.infrastructure.external.email_service import mail
    mail.init_app(app)

    # ----------------------------------------------------------------
    # Modelos SQLAlchemy — en orden de dependencia
    # ----------------------------------------------------------------
    from app.infrastructure import models

    # ----------------------------------------------------------------
    # Blueprints
    # ----------------------------------------------------------------
    from app.interfaces.api.routes.auth_routes import auth_bp
    from app.interfaces.api.routes.admin_routes import admin_bp
    from app.interfaces.api.routes.fincas_routes import fincas_bp
    from app.interfaces.api.routes.lotes_parcelas_routes import lotes_parcelas_bp
    from app.interfaces.api.routes.temporadas_routes import temporadas_bp
    from app.interfaces.api.routes.climatico_routes import climatico_bp
    from app.interfaces.api.routes.actividades_routes import actividades_bp
    from app.interfaces.api.routes.estimacion_routes import estimacion_bp
    from app.interfaces.api.routes.financiero_routes import financiero_bp
    from app.interfaces.api.routes.agronomo_routes import agronomo_bp
    from app.interfaces.api.routes.reportes_routes import reportes_bp

    app.register_blueprint(auth_bp,           url_prefix='/api/v1/auth')
    app.register_blueprint(admin_bp,          url_prefix='/api/v1/admin')
    app.register_blueprint(fincas_bp,         url_prefix='/api/v1/fincas')
    app.register_blueprint(lotes_parcelas_bp, url_prefix='/api/v1')
    app.register_blueprint(temporadas_bp,     url_prefix='/api/v1/temporadas')
    app.register_blueprint(climatico_bp,      url_prefix='/api/v1/climatico')
    app.register_blueprint(actividades_bp,    url_prefix='/api/v1/actividades')
    app.register_blueprint(estimacion_bp,     url_prefix='/api/v1/estimacion')
    app.register_blueprint(financiero_bp,     url_prefix='/api/v1/financiero')
    app.register_blueprint(agronomo_bp,       url_prefix='/api/v1/agronomo')
    app.register_blueprint(reportes_bp,       url_prefix='/api/v1/reportes')

    # ----------------------------------------------------------------
    # Health check — sin autenticación ni rate limit
    # ----------------------------------------------------------------
    @app.route('/api/v1/health')
    def health():
        return {
            'status': 'ok',
            'sistema': 'AgroCycle',
            'version': '1.0.0',
            'entorno': app.config.get('FLASK_ENV'),
        }

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)