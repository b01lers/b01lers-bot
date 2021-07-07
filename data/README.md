# data/

This folder should be populated with four files:

- b01lers-bot.db
- bot.log
- config.json
- config.secret

Before running the bot, make sure these files exist.

## data/b01lers-bot.db, data/bot.log

These files store the database and logs, respectively, for the bot. If it's your first time running the bot, initialize these files to be empty.

## data/config.json

This file stores ID's of the server, channels, and categories that this bot operates on. The file should look like:

```
{
    "discord": {
        "guild": ##################,
        "update-channel": ##################,
        "approval-channel": ##################,
        "ctf-category": ##################,
        "archive-category": ##################
    },
    "files": {
        "database-path": "/xxxx/xxxx/b01lers-bot.db",
        "backup-path": "/xxxx/xxxx/b01lers-bot-{0}.db"
    }
}
```

Populate the file with their respective values.

- `guild` - The server ID.
- `update-channel` - The bot sends updates in this channel, such as when a member verifies, when the bot runs into an error, etc.
- `approval-channel` - Some commands require officer approval. The bot sends to-be-approved messages in this channel.
- `ctf-category` - The category named "live ctfs".
- `archive-category` - The category in which archived ctfs are stored.

## data/config.secret

This file stores sensitive data, such as secret keys. The file should look like:

```
{
    "mailgun": {
        "enabled": true,
        "key": "XXXXX",
        "url": "XXXXX"
    },
    "security": {
        "secret": "XXXXX",
        "secret-pub": "XXXXX",
        "discord-token": "XXXXX",
        "github-token": "XXXXX"
    }
}
```

### `mailgun`

We use mailgun to send our members emails for verification.

### `secret` and `secret-pub`

Used for generating verification tokens.

### `discord-token`

The secret token for the bot! You can find this in Discord's developer console.

### `github-token`

Used to access GitHub, in a future update. It's unused for now.