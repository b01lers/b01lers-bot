from bot import utils
from bot.database.models import Point, Transaction

from peewee import fn

from bot.utils.messages import get_epoch_timestamp

"""Points Related"""


def get_highest_points() -> int:
    """Get the current highest points stored in the database."""
    return Point.select(fn.MAX(Point.points)).scalar() or 0


def get_points_by_discord(uid: int) -> int:
    """Get the points of the specified Discord user."""
    discord_user, _ = Point.get_or_create(uid=uid)
    return discord_user.points


def set_points_by_discord(uid: int, points: int) -> None:
    """Set the points of the specified Discord user."""
    discord_user, _ = Point.get_or_create(uid=uid)
    discord_user.points = points
    discord_user.save()


def add_points_to_user(uid: int, points: int) -> None:
    """Add points to the specified Discord user."""
    discord_user, _ = Point.get_or_create(uid=uid)
    discord_user.points += points
    discord_user.save()


def get_top_scorers(num: int) -> list[Point]:
    """Get top scorers in the server."""
    return Point.select().order_by(Point.points.desc()).limit(num).execute()


"""Transaction Related"""


def add_transaction(
    uid: int,
    ptype: tuple[str, any],
    points: int,
    description: any = "",
    timestamp: int = get_epoch_timestamp(),
) -> None:
    """Create a transaction."""
    Transaction.create(
        uid=uid,
        type=ptype[0],
        subtype=ptype[1],
        point_delta=points,
        description=description,
        timestamp=timestamp,
    )


def get_all_user_points_changes(uid: int, ptype: tuple[str, any]) -> int:
    """Get a user's total points change."""
    return (
        Transaction.select(fn.SUM(Transaction.point_delta)).where(
            (Transaction.uid == uid)
            & (Transaction.type == ptype[0])
            & (Transaction.subtype == ptype[1])
        )
        or 0
    )


def get_recent_user_points_changes(uid: int, ptype: tuple[str, any], time: int):
    """Get a user's points change in specified past seconds."""
    return (
        Transaction.select(fn.SUM(Transaction.point_delta)).where(
            (Transaction.uid == uid)
            & (Transaction.type == ptype[0])
            & (Transaction.subtype == ptype[1])
            & (Transaction.timestamp > (get_epoch_timestamp() - time))
        )
        or 0
    )


def get_transaction_count_by_uid_and_type(uid: int, ptype: tuple[str, any]) -> int:
    return (
        Transaction.select(fn.COUNT(Transaction.tid))
        .where(
            (Transaction.uid == uid)
            & (Transaction.type == ptype[0])
            & (Transaction.subtype == ptype[1])
        )
        .count()
    )


def get_user_yeets_on_message(uid: int, subtype: str) -> list[Transaction]:
    return Transaction.get_or_none(type="yeet", uid=uid, subtype=subtype)
