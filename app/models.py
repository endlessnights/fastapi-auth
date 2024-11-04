# app/models.py

from tortoise import fields, models
from datetime import datetime


class Group(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=50, unique=True)
    users: fields.ManyToManyRelation["User"] = fields.ManyToManyField(
        "models.User", related_name="groups", through="user_group"
    )

    def __str__(self):
        return self.name


class User(models.Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=50, unique=True)
    email = fields.CharField(max_length=100, unique=True, null=True)
    full_name = fields.CharField(max_length=100, null=True)
    hashed_password = fields.CharField(max_length=128)
    is_active = fields.BooleanField(default=True)
    registration_date = fields.DatetimeField(default=datetime.utcnow)
    groups: fields.ManyToManyRelation[Group]

    def __str__(self):
        return self.username

    class PydanticMeta:
        exclude = ['hashed_password']
