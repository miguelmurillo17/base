"""Configuración común a todos los entornos.

Los valores secretos o que cambian entre entornos se leen de variables de entorno. Si existe
un archivo .env en la raíz del proyecto, sus valores se cargan en cualquier entorno, sin
reemplazar las variables ya definidas. En desarrollo es la forma habitual de definirlas; en
producción se definen en el entorno del servicio y el archivo .env no se despliega.
"""

from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.utils.csp import CSP
from dotenv import load_dotenv

from config.entorno import entorno, entorno_booleano, entorno_entero, entorno_opcion

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = entorno("DJANGO_SECRET_KEY")

DEBUG = False

NOMBRE_SITIO = entorno("NOMBRE_SITIO", por_defecto="Sitio")

INSTALLED_APPS = [
    # Sitio de administración cuyo acceso pasa siempre por django-allauth (config/apps.py).
    "config.apps.AdministracionConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Lo cargan las plantillas de llaves de acceso de django-allauth.
    "django.contrib.humanize",
    # Plantillas de los widgets para el renderizador de formularios del proyecto.
    "django.forms",
    "allauth",
    "allauth.account",
    "allauth.mfa",
    "apps.cuentas",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Toda vista exige sesión iniciada salvo las marcadas con @login_not_required.
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.csp",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "config.contexto.exponer_datos_sitio",
            ],
        },
    },
]

FORM_RENDERER = "config.formularios.RenderizadorFormularios"

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": entorno("POSTGRES_DB"),
        "USER": entorno("POSTGRES_USER"),
        "PASSWORD": entorno("POSTGRES_PASSWORD"),
        "HOST": entorno("POSTGRES_HOST", por_defecto="127.0.0.1"),
        "PORT": entorno("POSTGRES_PORT", por_defecto="5432"),
        # Sin este límite, un servidor inaccesible bloquea cada comando por minutos.
        "OPTIONS": {"connect_timeout": 10},
    },
}

# Caché compartida por todos los procesos. La usan los límites de intentos de django-allauth
# y el registro de códigos de verificación ya usados, que no funcionan con una caché local
# por proceso. La tabla se crea con "manage.py createcachetable".
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "cache_compartida",
        # Con el límite por defecto de 300 entradas, Django descarta entradas vigentes y los
        # contadores de intentos se reinician antes de tiempo.
        "OPTIONS": {"MAX_ENTRIES": 100_000},
    },
}

AUTH_USER_MODEL = "cuentas.Usuario"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        "OPTIONS": {"user_attributes": ("correo", "nombre", "apellidos")},
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "account_login"
LOGIN_REDIRECT_URL = "inicio"

LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Mazatlan"
USE_I18N = True
USE_TZ = True
# Traducciones propias, con prioridad sobre las de Django y las bibliotecas.
LOCALE_PATHS = [BASE_DIR / "locale"]

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Política de seguridad de contenido: solo recursos propios. Los scripts y estilos en
# línea necesitan el atributo nonce que entrega el procesador de contexto csp. img-src
# admite data: porque django-allauth genera el código QR de la aplicación de
# autenticación como una imagen data:.
SECURE_CSP = {
    "default-src": [CSP.SELF],
    "script-src": [CSP.SELF, CSP.NONCE],
    "style-src": [CSP.SELF, CSP.NONCE],
    "img-src": [CSP.SELF, "data:"],
    "font-src": [CSP.SELF],
    "connect-src": [CSP.SELF],
    "object-src": [CSP.NONE],
    "base-uri": [CSP.SELF],
    "form-action": [CSP.SELF],
    "frame-ancestors": [CSP.NONE],
}

# Los registros van a la salida de errores estándar, donde los recoge el gestor de servicios
# o el contenedor. Los errores del servidor se envían además por correo a ADMINS cuando
# DEBUG está desactivado, como en la configuración por defecto de Django; el filtro de
# config/errores.py oculta en esos informes las contraseñas y los códigos.
DEFAULT_EXCEPTION_REPORTER_FILTER = "config.errores.FiltroInformesErrores"
NIVEL_REGISTRO = entorno("DJANGO_LOG_LEVEL", por_defecto="INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "sin_depuracion": {"()": "django.utils.log.RequireDebugFalse"},
    },
    "formatters": {
        "sencillo": {"format": "{asctime} {levelname} {name}: {message}", "style": "{"},
    },
    "handlers": {
        "consola": {"class": "logging.StreamHandler", "formatter": "sencillo"},
        "correo_administradores": {
            "class": "django.utils.log.AdminEmailHandler",
            "level": "ERROR",
            "filters": ["sin_depuracion"],
        },
    },
    "root": {"handlers": ["consola"], "level": NIVEL_REGISTRO},
    "loggers": {
        "django": {
            "handlers": ["consola", "correo_administradores"],
            "level": NIVEL_REGISTRO,
            "propagate": False,
        },
    },
}

# --- Cuentas de usuario (django-allauth) ---
#
# Cada función opcional se activa con una variable de entorno; el valor por defecto es el
# más seguro. Las variables están descritas en .env.example.

CUENTAS_REGISTRO_ABIERTO = entorno_booleano("CUENTAS_REGISTRO_ABIERTO", por_defecto=False)
CUENTAS_VERIFICACION_CORREO = entorno_opcion(
    "CUENTAS_VERIFICACION_CORREO",
    ("obligatoria", "opcional", "ninguna"),
    por_defecto="obligatoria",
)
CUENTAS_DOBLE_FACTOR_ACTIVO = entorno_booleano(
    "CUENTAS_DOBLE_FACTOR_ACTIVO",
    por_defecto=True,
)
CUENTAS_ADMINISTRACION_EXIGE_DOBLE_FACTOR = entorno_booleano(
    "CUENTAS_ADMINISTRACION_EXIGE_DOBLE_FACTOR",
    por_defecto=True,
)
CUENTAS_LLAVES_ACCESO_ACTIVAS = entorno_booleano(
    "CUENTAS_LLAVES_ACCESO_ACTIVAS",
    por_defecto=False,
)

if not CUENTAS_DOBLE_FACTOR_ACTIVO and (
    CUENTAS_ADMINISTRACION_EXIGE_DOBLE_FACTOR or CUENTAS_LLAVES_ACCESO_ACTIVAS
):
    raise ImproperlyConfigured(
        "CUENTAS_ADMINISTRACION_EXIGE_DOBLE_FACTOR y CUENTAS_LLAVES_ACCESO_ACTIVAS requieren "
        "CUENTAS_DOBLE_FACTOR_ACTIVO=true."
    )

ACCOUNT_ADAPTER = "apps.cuentas.adaptadores.AdaptadorCuentas"
ACCOUNT_FORMS = {
    "login": "apps.cuentas.forms.FormularioInicioSesion",
    "reset_password": "apps.cuentas.forms.FormularioRestablecerContrasena",
}
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USER_MODEL_EMAIL_FIELD = "correo"
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = {
    "obligatoria": "mandatory",
    "opcional": "optional",
    "ninguna": "none",
}[CUENTAS_VERIFICACION_CORREO]
# La verificación del correo y el restablecimiento de contraseña se hacen por enlace:
# funcionan desde cualquier dispositivo y las rutas no dependen del modo de verificación.
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED = False
ACCOUNT_PASSWORD_RESET_BY_CODE_ENABLED = False
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
# Al pedir el restablecimiento de la contraseña de una dirección sin cuenta también se
# envía un correo, para que la respuesta tarde lo mismo que con una dirección registrada.
# El enlace de registro solo aparece cuando el registro está abierto
# (templates/account/email/unknown_account_message.txt).
ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS = True
# Una sola dirección por cuenta; la nueva se verifica antes de reemplazar a la anterior.
ACCOUNT_CHANGE_EMAIL = True
ACCOUNT_REAUTHENTICATION_REQUIRED = True
ACCOUNT_EMAIL_NOTIFICATIONS = True
ACCOUNT_EMAIL_SUBJECT_PREFIX = f"[{NOMBRE_SITIO}] "
ACCOUNT_LOGOUT_REDIRECT_URL = "account_login"

# Dirección IP real para los límites de intentos. Sin proxy inverso es REMOTE_ADDR.
ALLAUTH_TRUSTED_PROXY_COUNT = entorno_entero("CUENTAS_PROXIES_DE_CONFIANZA", por_defecto=0)
ALLAUTH_TRUSTED_CLIENT_IP_HEADER = entorno("CUENTAS_ENCABEZADO_IP_CLIENTE", por_defecto=None)

MFA_ADAPTER = "apps.cuentas.adaptadores.AdaptadorDobleFactor"
MFA_SUPPORTED_TYPES = []
if CUENTAS_DOBLE_FACTOR_ACTIVO:
    MFA_SUPPORTED_TYPES = ["totp", "recovery_codes"]
    if CUENTAS_LLAVES_ACCESO_ACTIVAS:
        MFA_SUPPORTED_TYPES.append("webauthn")
MFA_PASSKEY_LOGIN_ENABLED = CUENTAS_LLAVES_ACCESO_ACTIVAS
MFA_TOTP_ISSUER = NOMBRE_SITIO
