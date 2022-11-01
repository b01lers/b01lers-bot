from bot.database.models import SelfGrantRole


def insert_single_role(role_id: int, label: str, color: str, emoji: str) -> None:
    """Insert a single role to the table."""
    SelfGrantRole.create(role_id=role_id, label=label, color=color, emoji=emoji)


def update_single_role(role_id: int, label: str, color: str, emoji: str) -> None:
    """Update a single role to the table."""
    SelfGrantRole.update(role_id=role_id, label=label, color=color, emoji=emoji).execute()


def get_all_roles() -> list[SelfGrantRole]:
    """Get all available self-grant roles."""
    return SelfGrantRole.select().execute()


def get_roles_count() -> int:
    """Get the total count of available self-grant roles."""
    return SelfGrantRole.select().count()
