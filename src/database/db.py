from tortoise.models import Model
from tortoise import fields


class Worker(Model):
    id = fields.IntField(pk=True)
    token = fields.CharField(max_length=2048)

    # Only approved servers can be used
    approved = fields.BooleanField(default=True)

    # Whether we fully trust the server
    trusted = fields.BooleanField(default=False)

    # Creation date
    created = fields.DatetimeField(auto_now=True)

    nickname = fields.CharField(max_length=255, default='')
