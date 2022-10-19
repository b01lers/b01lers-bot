from typing import Union

from bot.database.models import Link


def purge_links() -> None:
    """Truncate links table."""
    Link.truncate_table()


def get_links_by_channel_id(channel_id: int) -> list[Link]:
    """Get all links in a channel."""
    return Link.select().where(Link.cid == channel_id).execute()


def insert_single_link(channel_id: int, url: str) -> None:
    """Insert a single link to the table."""
    Link.create(cid=channel_id, url=url)


def batch_insert_links(links: list[tuple[Union[int, str], str]]) -> None:
    """Batch insert links.

    Link: {"cid": cid, "url": url}
    """
    Link.insert_many(links, fields=[Link.cid, Link.link]).on_conflict(
        action="IGNORE"
    ).execute()
