from rest_framework.views import APIView


class BaseApiViewTool:
    """A base class for API views that can be 
    registered as toolset methods in the MCP server.
    
    Args:
        view_class (type): The API view class to register.
    """

    view: type[APIView] = None

    def __init__(self, view_class: type[APIView], **kwargs):
        self.view = view_class.as_view(**kwargs)


class DrfListViewTool(BaseApiViewTool):
    pass 


class DrfCreateViewTool(BaseApiViewTool):
    pass


class DrfRetrieveViewTool(BaseApiViewTool):
    pass


class DrfUpdateViewTool(BaseApiViewTool):
    pass


class DrfDeleteViewTool(BaseApiViewTool):
    pass
