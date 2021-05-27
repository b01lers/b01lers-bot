from bot import client, DISCORD_TOKEN
from bot import commands  # registers commands #
from bot import backup

backup.backup_db()
client.run(DISCORD_TOKEN)
