# slack-message-formatting

An agent skill for writing and posting Slack messages that render correctly. Works with Claude Code and Codex.

Slack does not use standard markdown. It uses mrkdwn, and the bold syntax depends on how you post: `*bold*` through the Web API or a webhook, `**bold**` through connectors that convert CommonMark. Agents often get this wrong, so bold turns into italics and lists collapse into one line. This skill makes the agent pick the posting route first, then write in that route's syntax.

## What it covers

- Bold, italic, links and lists for each posting route (Web API, incoming webhook, Slack MCP servers, the Slack connector in Claude)
- Real nested lists with Block Kit `rich_text`, plus a converter script
- Mentions, channel links and dates by ID, and escaping
- Block Kit for headings, tables and buttons
- How to keep messages short and clear: who does what to whom, 10 lines or less, no file paths or internal names
- A checklist to run before sending

## Install

Claude Code:

```
mkdir -p ~/.claude/skills
git clone https://github.com/kojikojikojikoji/slack-message-formatting ~/.claude/skills/slack-message-formatting
```

Codex reads `~/.agents/skills/`:

```
mkdir -p ~/.agents/skills
ln -s ~/.claude/skills/slack-message-formatting ~/.agents/skills/
```

## Usage

Ask the agent to post or format a Slack message, for example "Post this update to #release" or "Format this for Slack". The skill loads on its own.

The scripts need Python 3.9 or later and have no dependencies:

```
python3 scripts/lint_slack_text.py < message.txt        # find markdown that will not render
python3 scripts/lint_slack_text.py --fix < message.txt  # print a converted version
python3 scripts/rich_text_blocks.py < body.txt          # rich_text blocks JSON
python3 scripts/rich_text_blocks.py --text < body.txt   # plain fallback for `text`
```

The scripts do not call Slack. Sending is up to you or your agent.

## License

MIT

## Credits

Parts of this skill are based on [sirkitree/slack-markdown-formatter](https://github.com/sirkitree/slack-markdown-formatter) (MIT License) and the community skills `slack-advanced-formatting` and `slack-block-kit-ui`.
