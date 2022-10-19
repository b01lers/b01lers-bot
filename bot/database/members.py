from typing import Union

from bot.database.models import Member


def get_member_by_email(email: str) -> Member:
    """Get a member object by their email."""
    return Member.get_or_none(email=email)


def get_member_by_discord(discord_id: Union[int, str]) -> Member:
    """Get a member object by their Discord id."""
    return Member.get_or_none(alias=discord_id)


def add_member(
    name: str, alias: Union[int, str], email: str, token: str, validated: int
) -> None:
    """Add a member."""
    Member.create(name=name, alias=alias, email=email, token=token, validated=validated)


def verify_member(discord_id: Union[int, str]) -> None:
    """Set a member's validation status to validated."""
    Member.update({Member.validated: 1}).where(Member.alias == discord_id).execute()
