from peewee import SqliteDatabase

DATABASE = SqliteDatabase("data/b01lers-bot.db")
DATABASE.connect()

# TODO: Make this more elegant
import bot.database.models

DATABASE.create_tables(
    [
        models.Approval,
        models.Bootcamp,
        models.Link,
        models.Member,
        models.Point,
        models.Transaction,
    ]
)

__all__ = ["approval", "bootcamp", "members", "points", "models"]
