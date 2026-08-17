from django.db import models

from mcp_server.server.toolset.queries import ModelQueryToolset


class SimpleModel(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name



class SimpleModelToolFromTestApp(ModelQueryToolset):
    model = SimpleModel

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.order_by("name")
