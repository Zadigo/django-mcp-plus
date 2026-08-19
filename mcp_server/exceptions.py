from rest_framework.views import APIView


class ViewClassSubclassError(Exception):
    def __init__(self, view_class: type[APIView], expected: type[APIView]):
        message = f'{view_class.__name__} must be a subclass of {expected.__name__}'
        super().__init__(message)
