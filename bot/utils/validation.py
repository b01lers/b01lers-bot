import hmac
import logging
import urllib
from typing import Optional

import requests

import aiohttp
from bs4 import BeautifulSoup

import hashlib

from discord.ext import commands

from bot import SECRET


def generate_hash(email: str) -> str:
    """Generate safe hash for specified email address."""
    return hmac.new(SECRET, email.encode("utf-8"), hashlib.sha512).hexdigest()


async def get_student_name_from_email_from_directory(
    email: str,
) -> tuple[Optional[str], Optional[str]]:
    """
    Get a student's name from their email address.

    Returns:
        Name: name of the student.
        Error String: an error string that explains why it failed.
    """

    url = "https://www.purdue.edu/directory/Advanced"
    # URL Encode before proceeding
    data = (
        f"SearchString={email.replace('@', '%40')}&SelectedSearchTypeId=0&UsingParam=Search+by+Email&CampusParam=All+Campuses"
        "&DepartmentParam=All+Departments&SchoolParam=All+Schools"
    )
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data, headers=headers) as rest_rsp:
            raw_html = await rest_rsp.text()

    response_document = BeautifulSoup(raw_html, features="html.parser")
    results_element = response_document.find("section", attrs={"id": "results"})

    if not results_element:
        return None, "An error occurred while parsing the Purdue Directory website."

    name_element = results_element.find("h2", class_="cn-name")

    if name_element:
        return name_element.text.title(), None

    return None, "You are not in the directory"
