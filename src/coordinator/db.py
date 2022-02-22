from tortoise.models import Model
from tortoise import fields


class Server(Model):
    id = fields.IntField(pk=True)
    token = fields.CharField(max_length=2048)

    # Only approved servers can be used
    approved = fields.BooleanField(default=False)

    # Whether we fully trust the server
    trusted = fields.BooleanField(default=False)

    # Creation date
    created = fields.DatetimeField()

    nickname = fields.CharField(max_length=255)
