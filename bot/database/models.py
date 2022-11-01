from peewee import *

from bot import utils
from bot.database import DATABASE
from bot.utils.messages import get_epoch_timestamp


class BaseModel(Model):
    """Represents a abstract base model of custom models."""

    class Meta:
        database = DATABASE


class Member(BaseModel):
    """Represents model of a club member."""

    class Meta:
        db_table = "members"

    name = TextField()
    alias = TextField()
    email = TextField(primary_key=True)
    token = TextField()
    validated = IntegerField()


class Point(BaseModel):
    """Represents model of participation points."""

    class Meta:
        db_table = "points"

    uid = TextField(primary_key=True)
    points = IntegerField(default=0)


class Link(BaseModel):
    """Represents model of URL sent in server."""

    class Meta:
        db_table = "links"

    lid = IntegerField(primary_key=True)
    cid = IntegerField()
    link = TextField()


class Bootcamp(BaseModel):
    """Represents a team that registered for the Bootcamp CTF."""

    # TODO: Rename?
    class Meta:
        db_table = "bootcamp"

    register_email = TextField()
    teammate_one = TextField()
    teammate_two = TextField()
    teammate_three = TextField()


class Approval(BaseModel):
    """Represents a request made in Discord channel."""

    class Meta:
        db_table = "approvals"

    aid = IntegerField(primary_key=True)
    type = TextField(default="solve")
    description = TextField(default="")
    approved = IntegerField(default=0)
    approve_message = TextField(default="")


class Transaction(BaseModel):
    """Represents a transaction of points."""

    class Meta:
        db_table = "transactions"

    tid = IntegerField(primary_key=True)
    uid = TextField(unique=False)
    type = TextField()
    subtype = TextField()
    description = TextField()
    point_delta = IntegerField()
    timestamp = TimestampField(default=get_epoch_timestamp())


class SelfGrantRole(BaseModel):
    """Represents a self-grant role."""

    class Meta:
        db_table = "self_grant_roles"

    role_id = IntegerField(unique=True)
    label = TextField()
    color = TextField()
    emoji = TextField(null=True)
