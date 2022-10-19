import json
from typing import Union

from bot.database.models import Approval


def create_approval_and_return_id(data: str) -> int:
    """Add a new approval."""
    # TODO: Data passed in is actually a json...
    return Approval.create(description=data).aid


def get_approval_by_id(aid: Union[str, int]) -> Approval:
    """Get an existing approval or None."""
    return Approval.get_or_none(aid=aid)


def update_approve_message(aid: Union[str, int], msg_id: Union[str, int]) -> None:
    """Update approval message by id."""
    Approval.update({Approval.approve_message: msg_id}).where(
        Approval.aid == aid
    ).execute()


def accept_request(aid: Union[str, int]) -> None:
    """Accept a specified request."""
    Approval.update({Approval.approved: 1}).where(Approval.aid == aid).execute()


def reject_request(aid: Union[str, int]) -> None:
    """Reject a specified request."""
    Approval.update({Approval.approved: -1}).where(Approval.aid == aid).execute()
