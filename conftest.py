import pytest
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
                'rest_framework',
                'rest_framework_simplejwt',
                'drf_spectacular',
                'mcp_server',
                'tests.testapp',
            ],
            AUTH_USER_MODEL='auth.User',
            ROOT_URLCONF='tests.urls',
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



@pytest.fixture
def model_query_toolset():
    from mcp_server.server.toolset.mixins import ModelQueryToolset
    from tests.testapp.models import SimpleModel

    class SimpleQueryToolset(ModelQueryToolset):
        model = SimpleModel

        def simple_method(self, arg1:int , arg2: int):
            return [arg1, arg2]
        
    return SimpleQueryToolset


@pytest.fixture
def methods_toolset():
    from mcp_server.server.toolset.mixins import McpMethodsToolset

    class SimpleMethodToolset(McpMethodsToolset):
        def simple_method(self, arg1:int , arg2: int):
            return [arg1, arg2]
        
    return SimpleMethodToolset


@pytest.fixture
def async_methods_toolset():
    from mcp_server.server.toolset.mixins import McpMethodsToolset

    class SimpleMethodsToolset(McpMethodsToolset):
        async def simple_method(self, arg1:int , arg2: int):
            return [arg1, arg2]
        
    return SimpleMethodsToolset


@pytest.fixture
def http_request():
    from django.test import RequestFactory
    return RequestFactory().get('/')


@pytest.fixture
def model_instance():
    from tests.testapp.models import SimpleModel
    return SimpleModel.objects.create(name="Test 1")


@pytest.fixture
def model_type():
    from tests.testapp.models import SimpleModel
    return SimpleModel


@pytest.fixture
def model_qs():
    from tests.testapp.models import SimpleModel
    SimpleModel.objects.create(name="Test 1")
    return  SimpleModel.objects.all()
