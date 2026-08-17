from django.conf import settings
from faker import Faker

fake = Faker()

def pytest_configure(config):
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            SECRET_KEY=fake.uuid4(),
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.admin',
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'django.contrib.messages',
                'django.contrib.staticfiles',
                'drf_spectacular',
                'mcp_server',
            ],
            AUTH_USER_MODEL='auth.User',
            ROOT_URLCONF='testapp.urls',
            DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
            REST_FRAMEWORK={
                'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
                'DEFAULT_AUTHENTICATION_CLASSES': [
                    'rest_framework_simplejwt.authentication.JWTAuthentication',
                    'rest_framework.authentication.TokenAuthentication',
                ],
            },
            SIMPLE_JWT={
                'AUTH_HEADER_TYPES': ['Token']
            },
            GRAPHENE={
                'SCHEMA': 'mystore.schema.schema'  # 👈 adjust to your schema path
            },
            STATIC_URL='/static/',
        )
