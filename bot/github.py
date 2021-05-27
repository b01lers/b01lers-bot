from github import Github

from bot.constants import *

gh = Github(GITHUB_TOKEN)
writeup_repo = gh.get_organization("b01lers").get_repo("b01lers-library")


def create_competition_branch():
    pass


def download_zip():
    pass


def upload_file():
    pass


def commit_zip():
    pass


def pull_competition_branch():
    pass
