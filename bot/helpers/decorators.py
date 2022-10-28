import logging
from typing import Callable, Union, TypeVar

from discord.ext.commands import Context, check, CheckFailure

from bot import client

T = TypeVar("T")


class OfficerOnly(CheckFailure):
    """Exception raised when an operation does not work outside of private
    message contexts.

    This inherits from :exc:`CheckFailure`
    """

    def __init__(self, message: Union[str, None] = None) -> None:
        super().__init__(message or "This command can only be used by a officer.")


def officer_only() -> Callable[[T], T]:
    """A :func:`.check` that indicates this command can only be used by a officer.

    This check raises a special exception, :exc:`.PrivateMessageOnly`
    that is inherited from :exc:`.CheckFailure`.

    .. versionadded:: 1.1
    """
    async def predicate(ctx: Context) -> bool:
        if not await client.is_officer(ctx.author.id):
            raise OfficerOnly()
        return True

    return check(predicate)
