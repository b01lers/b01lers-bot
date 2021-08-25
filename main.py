from bot import commands  # registers commands #
from bot import DISCORD_TOKEN, backup, client

backup.backup_db()
client.run(DISCORD_TOKEN)
