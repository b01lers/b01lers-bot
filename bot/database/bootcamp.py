from bot.database.models import Bootcamp


def get_team_by_email(email: str) -> Bootcamp:
    """Get a team by email."""
    return Bootcamp.get_or_none(
        (Bootcamp.register_email == email)
        | (Bootcamp.teammate_one == email)
        | (Bootcamp.teammate_two == email)
        | (Bootcamp.teammate_three == email)
    )


def get_team_by_leader_email(email: str) -> Bootcamp:
    """Get a team by leader email."""
    return Bootcamp.get_or_none(register_email=email)


def get_all_teams() -> [Bootcamp]:
    """Get all teams which registered for the bootcamp."""
    return Bootcamp.select().execute()


# def get_ctf_registration(email: str):
#     c.execute(GET_CTF_REGISTRATION, (email,))


def update_ctf_team(
    leader_email: str, tm1: str, tm2: str, tm3: str, leader: str
) -> None:
    """Update a bootcamp team."""
    Bootcamp.update(
        register_email=leader, teammate_one=tm1, teammate_two=tm2, teammate_three=tm3
    ).where(Bootcamp.register_email == leader_email).execute()


def update_ctf_team_entry(
    entry: Bootcamp, leader_email: str, tm1: str, tm2: str, tm3: str
) -> None:
    """Update a bootcamp team entry."""
    entry.register_email = leader_email
    entry.teammate_one = tm1
    entry.teammate_two = tm2
    entry.teammate_three = tm3
    entry.save()


def add_team(leader: str, tm1: str = "", tm2: str = "", tm3: str = "") -> None:
    """Add a new team for bootcamp."""
    Bootcamp(
        register_email=leader, teammate_one=tm1, teammate_two=tm2, teammate_three=tm3
    ).save()


def reset_teams() -> None:
    """Reset bootcamp table."""
    Bootcamp.truncate_table()
