from tortoise.models import Model
from tortoise import fields


class Server(Model):
    id = fields.IntField(pk=True)
    token = fields.CharField(max_length=255)
    trusted = fields.BooleanField(default=False)
