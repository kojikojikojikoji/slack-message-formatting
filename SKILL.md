---
name: slack-message-formatting
description: >-
  Reference for writing and posting Slack messages: formatting (mrkdwn and Block Kit) and how to send them.
  Works with Claude Code and Codex. Slack does not use standard markdown. It uses "mrkdwn", and the bold
  syntax is reversed depending on the route (`*bold*` vs `**bold**`). So decide the posting route first,
  then write the text. Use this skill when the user says "post this to Slack", "send it on Slack",
  "format this for Slack", "write a Slack message", "use Block Kit", "add a mention or channel link",
  or whenever you post to Slack by any route (chat.postMessage, a Slack MCP server, the Slack connector,
  or an incoming webhook). Whether you may send at all is decided by the user, not by this skill.
license: MIT
metadata:
  short-description: Slack message formatting and posting (mrkdwn, Block Kit, bold syntax by route)
---

# Slack Message Formatting (mrkdwn, Block Kit, posting routes)

Decide two things in this order. First, which route you will post through. Second, write the text in that route's syntax. If you skip the first step, bold text turns into italics and lists collapse into one line.

## 0. Decide the route first (this changes the bold syntax)

### Some MCP servers convert markdown by default. Set the content type explicitly.

Community Slack MCP servers (for example `slack-mcp-server`) often take a `content_type` argument on their "add message" tool, and the default is `text/markdown`. If you leave it out, the text is parsed as CommonMark and converted to mrkdwn before sending. Native mrkdwn written into that path breaks.

What goes wrong when `content_type` is left out and you write native mrkdwn:

- `*bold*` is read as CommonMark italics. The message shows `_bold_` with the underscores visible.
- Lines that start with `•` and are separated by single line breaks are joined into one paragraph. The list becomes one long line.

Pick one of the two styles below and do not mix them.

| Style | `content_type` | Bold | Italic | List | Link |
|---|---|---|---|---|---|
| A. Native mrkdwn (recommended) | set `"text/plain"` | `*bold*` | `_italic_` | `•` at line start + line break | `<URL|label>` |
| B. CommonMark | `"text/markdown"` (default) | `**bold**` | `*italic*` | `- ` at line start | `[label](URL)` |

Use A by default. Sections 1 to 3 assume native mrkdwn, which is what Slack itself reads. With no conversion step in between, there is less to go wrong.

### Routes at a glance

| Route | Syntax | Usable from Codex? |
|---|---|---|
| Community Slack MCP server with `content_type:"text/plain"` | Native mrkdwn (`*bold*`) | Yes |
| Community Slack MCP server with no `content_type` | CommonMark (`**bold**`), converted before sending | Yes |
| The Slack connector in Claude (claude.ai Slack MCP, `slack_send_message` and similar) | CommonMark (`**bold**`) | No (Claude only) |
| Raw `chat.postMessage` or an incoming webhook (curl) | Native mrkdwn (`*bold*`) | Yes |

- From Codex, the Claude Slack connector is not available. Use an MCP server or curl, with `content_type:"text/plain"` and native mrkdwn.
- When unsure, do not use emphasis at all. A plain message reads fine. Do not risk broken formatting just for decoration.

### 0-1. Decide whose name the message goes out under

Decide this before the syntax.

- A user token (xoxp, or a browser session token) posts as the user. Use it when the message should come from the user personally.
- A bot token (xoxb) and app connectors post as the app. Slack may show an app label next to the name. Do not use them for messages that should read as the user's own words. Reading and searching through them is fine.

If the message goes out as the user, do not leave traces of an assistant in the text:

- No signatures such as "Sent with ..." or "Generated with ..." at the end.
- Do not refer to yourself as an AI in the body. Write in the user's voice.
- State what you checked as fact. If you have not checked something, ask the user before sending instead of hedging.

## 1. Native mrkdwn syntax (differences from standard markdown)

| Element | Standard markdown | Slack mrkdwn | Notes |
|---|---|---|---|
| Bold | `**bold**` | `*bold*` | One asterisk |
| Italic | `*italic*` | `_italic_` | Underscore |
| Strikethrough | `~~text~~` | `~text~` | One tilde |
| Inline code | `` `code` `` | `` `code` `` | Same |
| Code block | ` ```lang ` | ` ``` ` (language is ignored) | No syntax highlighting |
| Quote | `> quote` | `> quote` / `>>> multi-line` | `>>>` quotes every line after it |
| Line break | Two trailing spaces, etc. | `\n` (a real newline) | With curl, put real newlines inside `--data-urlencode` |

Links: standard `[text](url)` becomes `<https://example.com|label>` in mrkdwn. A bare URL, or `<https://example.com>`, is linked automatically.

Lists: Slack's docs say there is no special list syntax for text posted by apps ([Slack docs](https://docs.slack.dev/messaging/formatting-message-text/)). Build lists with characters and line breaks.

- Native mrkdwn (`content_type:"text/plain"`): put `•` (U+2022) at the start of each line and separate lines with `\n`. Number ordered lists yourself with `1.`.
- CommonMark (the `text/markdown` default): use `- `, not `•`. Lines starting with `•` and separated by single line breaks are joined into one paragraph (see section 0).

Line breaks: Slack's spec is "insert `\n`". In native mrkdwn a single newline is a line break. In the CommonMark route a single newline disappears when paragraphs are joined. To keep lines apart there, add a blank line or use list syntax. This difference causes most broken messages.

## 2. Slack-specific embeds (by ID)

| Purpose | Syntax |
|---|---|
| Mention a user | `<@U012AB3CD>` (use the ID; `<@username>` is unreliable) |
| Link a channel | `<#C012AB3CD>` or `<#C012AB3CD|channel-name>` |
| Mention a user group | `<!subteam^S012AB3CD>` |
| Notify everyone | `<!here>` / `<!channel>` / `<!everyone>` (use sparingly) |
| Date in the reader's time zone | `<!date^1392734382^{date_short} {time}|Feb 18, 2014 9:39 AM>` |
| Emoji | Shortcodes such as `:tada:`. Unicode emoji also work |

Date tokens: `{date_num}` `{date}` `{date_short}` `{date_long}` `{time}` `{time_secs}`. The part after `^` is the format. The part after `|` is the fallback for clients that cannot render it, and it is required.

Escaping: replace raw `&`, `<` and `>` in the text with `&amp;`, `&lt;` and `&gt;`, so they do not clash with `<...>` mentions and links.

## 3-0. Use a rich_text block for lists of three or more items, nested lists, or bold

A list built by hand with `•` and line breaks does not render as a real list in Slack. There is no indent and no nesting, and long items look cramped.

For structured messages (reports, requests, automated posts), send a Block Kit `rich_text` block. It renders the same way as a list a person types in the Slack editor. Nesting comes from `indent` on `rich_text_list`, and bold comes from `style.bold`.

- Convert with `scripts/rich_text_blocks.py`. It turns a simple syntax (`# heading`, `- item`, `  - child item`, `1. item`, `*bold*`, `<URL|label>`, `<@U...>`) into rich_text JSON.
- With an MCP server's "add message" tool, pass the JSON string as `blocks` and the plain fallback (from `--text`) as `text`. `content_type` is ignored when `blocks` is set.
- Automated posts from your own programs work the same way. Add `blocks` to `chat.postMessage`. Do not stop at mrkdwn text with `*bold*`.
- Keep each item to one line (about 80 characters as a guide). Move long explanations to a child item (indent 1), or drop them. Do not start an item with a bracketed label such as "[Risk]". Use one bold word instead (*Risk*).
- Steps: write the text in the simple syntax, run `python3 scripts/rich_text_blocks.py < body.txt` for the JSON and `--text` for the fallback, send both `blocks` and `text`, then open the message permalink and check how it rendered.
- Observed rendering: bold, first-level bullets (●), second-level bullets (○) and links render as expected. `style:"ordered"` was drawn with ● and no numbers. When you need numbers, write "1." yourself inside a bullet item.
- Send to a DM with yourself first to check the rendering, then post to the real channel.

```
# Please fill in the order date on open deals
- *Revenue on the finance dashboard* now counts deals by order date, not by creation date
- *87 deals worth $350,400* have no order date, so they are missing from the total
  - Most deals: Alice 50, Bob 12, Carol 8
  - Largest amounts: Carol $116,000, Dave $100,100, Bob $64,700
- <https://crm.example.com/deals?missing=order_date|Open the list of deals>
If you can fill them in by Friday, Monday's automatic report will show the right numbers.
```

## 3. What mrkdwn cannot do: use Block Kit

These do not work in mrkdwn: `#` headings, tables, HTML, nested emphasis (`*bold _italic_*`), `![alt](url)` images, footnotes and `[ ]` task lists.

When you need them, or need a dashboard-like layout or buttons, use Block Kit (a `blocks` array). Each text object is `type:"mrkdwn"` (section 1 syntax applies) or `type:"plain_text"`.

```json
{
  "blocks": [
    {"type":"header","text":{"type":"plain_text","text":"Deploy finished"}},
    {"type":"section","text":{"type":"mrkdwn","text":"*v2.3.1* is live in production :white_check_mark:"}},
    {"type":"section","fields":[
      {"type":"mrkdwn","text":"*Environment*\nProduction"},
      {"type":"mrkdwn","text":"*Duration*\n4m 12s"}
    ]},
    {"type":"divider"},
    {"type":"context","elements":[{"type":"mrkdwn","text":"<https://example.com/log|View the log>"}]}
  ]
}
```

- `header` takes plain_text only. `section.fields` holds up to 10 items in two columns. Use it in place of a table.
- Check the design in Block Kit Builder (https://app.slack.com/block-kit-builder).
- When you send `blocks`, always put a short summary in `text` too. Slack uses it for notifications and accessibility.

## 4. Sending the message

Sending a message acts on the user's behalf. Confirm the text and the destination with the user before you send.

### 4-1. MCP servers and the Slack connector

Use the tool (an MCP server's "add message" tool, or `slack_send_message` in the connector). Choose native mrkdwn or CommonMark as in the table in section 0.

### 4-2. curl (works from Codex and Claude; fallback when no MCP is loaded)

This is the native mrkdwn route. Always use `--data-urlencode` so line breaks and symbols survive.

```bash
# SLACK_TOKEN is a bot (xoxb) or user (xoxp) token, loaded from your own .env
curl -s -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer ${SLACK_TOKEN}" \
  --data-urlencode "channel=C0XXXXXXX" \
  --data-urlencode "text=*bold* and _italic_ and <https://example.com|a link>" \
  --data-urlencode "unfurl_links=false" \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print('ok=%s ts=%s err=%s'%(d.get('ok'),d.get('ts'),d.get('error')))"
```

- Reply in a thread: add `--data-urlencode "thread_ts=1784256633.493239"`.
- Block Kit: add `--data-urlencode "blocks=$(cat blocks.json)"` and `text=<summary>`.
- Look up channel IDs from names with `conversations.list` (see the reference file).

### 4-3. Incoming webhook

`curl -X POST -H 'Content-type: application/json' --data '{"text":"*bold*"}' <WEBHOOK_URL>`. Native mrkdwn. `blocks` also work.

## 4-4. Write the content before you worry about syntax

Slack is shared with the team, and readers have not opened the code. Do not put file paths, line numbers, function names, variable names or code snippets in the message. Say whose what is affected and how, with amounts, counts and the people affected. Add a link to the issue or pull request and leave the details there.

Setting up a test environment, merging branches or redeploying are means, not the subject of the report. The subject is what is happening, how it affects people, and what you need from the reader. Mention the means in one line if needed.

For the same reason, do not make table names, column names, environment variables, internal error codes or state names the subject of a sentence. Even if the reader works on the product, they do not share your repository's internal names. Write "four top-up packs (100, 200, 300 and 700 points)" rather than "`credit_packs` has 4 rows".

## 4-4-1. Keep who, whom, what, where, when and how

Do not cut the subject to make a line shorter. In bullet lists, "who" and "to whom" are the first things to go missing, and without them the reader cannot picture what happened.

- Name the people in each item. Use the product's roles (learner, approver, admin, support staff). Do not settle for "the user".
- In a bug report, say whose what goes wrong and how. Do not stop at "data becomes inconsistent" or "an error occurs".
- When talking about a screen, start with who is looking at it.

```
✗ • Closed 3 paths that allowed completion without approval
✓ • Closed 3 paths that let a learner complete a quest without showing it to an approver

✗ • Concurrent actions caused an error
✓ • When 2 approvers pressed approve and reject at the same time, the one who acted saw an error

✗ • Also fixed the issue where the request list was readable
✓ • Also fixed: any member of an organization could read other people's approval requests
```

Check each line by asking "So who does this, and to whom?" If the line cannot answer, something is missing.

## 4-4-2. Keep it short and use lists

Slack is chat, not a document. Readers only read what fits on the screen without scrolling. Long messages get skipped or misread.

- Do not write paragraph after paragraph. Put facts in a list. Only the opening conclusion (1 or 2 sentences) and a closing request (1 sentence) should be prose.
- Aim for 10 lines per message, list included. If it is longer, split the message or move the details to an issue, pull request or thread reply.
- One item, one line. If an item runs to two lines, cut it or split it. Do not add explanations inside an item with line breaks.
- At most three small headings (bold lines). If you need chapters, write an issue and post the link.
- Do not describe the history, the investigation or the things you tried. Write three things: what happened, how it affects people, and what you need from the reader.
- Put numbers in the list, not in prose ("4 errors in 10 runs, 0 after the fix").
- A long status report format (background, problem, what was done, open items) is for the terminal. In Slack, compress it to one conclusion and 3 to 5 bullets.

Bad (a paragraph of history, too long) and good (conclusion and list):

```
✗ While looking into approvals, we found 3 ways in the organization approval
  flow to complete a quest without approval. All of them worked by calling
  the API directly, so even with approval required, people could mark their
  own quests complete. For organization customers this means... (and so on)

✓ I opened a PR for the approval fixes: <URL|PR #748>
  • Closed 3 ways to complete a quest without approval
  • Also fixed: members could read other people's approval requests
  • 15 records in production are affected. No impact on users
  Please let me know when to release it.
```

## 4-5. Patterns that break the layout

- Do not put a bare URL alone on a line. Always give links a label (`[title](URL)` in the CommonMark route, `<URL|title>` in mrkdwn). A list of bare URLs gets packed together, and the next item's text ends up on the same line as the link.
- Do not draw trees with full-width spaces or `└`. Indentation is not kept and the tree falls apart. Describe the hierarchy in one sentence, such as "#85 is the parent; #86 and #87 are under it".
- Do not put more than 4 or 5 links in one message. If you must, use one format per line ("link, owner, due date") and move the explanation to a separate paragraph.

## 5. Checklist before sending

- [ ] Lists of 3 or more items, nested lists or bold text are sent as a `rich_text` block, not hand-built `•` lines (section 3-0)
- [ ] Each line says who does what to whom. It answers "So who does this?" (4-4-1)
- [ ] `content_type` is set explicitly when the MCP server supports it (its default may be markdown conversion) (section 0)
- [ ] The syntax matches that `content_type` (`text/plain` uses `*bold*` and `•`; the default uses `**bold**` and `- `) (section 0)
- [ ] Lists will not collapse at single line breaks (section 1)
- [ ] The message fits in about 10 lines and the facts are in a list (4-4-2)
- [ ] No history, investigation steps or things you tried (4-4-2)
- [ ] No file paths, line numbers, function names or code in the text (4-4)
- [ ] No table names, variable names, error codes or state names as the subject. Real-world words instead (4-4)
- [ ] No bare URL on its own line and no trees drawn with spaces (4-5)
- [ ] The subject is the problem and its impact, not the means (4-4)
- [ ] The route is decided and the bold syntax matches it (`*bold*` or `**bold**`) (section 0)
- [ ] No leftover standard markdown (`**`, `[text](url)`, `#` headings, tables) in native mrkdwn
- [ ] Mentions and channels use IDs. No careless `<!channel>`
- [ ] Tables are converted to Block Kit `section.fields`
- [ ] curl uses `--data-urlencode` for every field, and `text` has a fallback
- [ ] The channel and the text were shown to the user before sending

## Optional: enforce this skill with a hook

If your agent supports pre-tool hooks (Claude Code's PreToolUse, for example), you can add a hook that runs before any Slack posting tool and blocks the post when:

- this skill has not been loaded in the session yet,
- there are no `blocks` and the text contains CommonMark bold (`**`), bracket links, `#` headings or a literal `\n`,
- there are no `blocks` and the text has 3 or more list lines,
- an MCP server call is missing `content_type`.

When the hook blocks a post, fix the text for the stated reason and send it again. Do not work around the hook.

## References and scripts

- `references/slack-mrkdwn-guide.md`: detailed syntax table, edge cases, Block Kit block types and all date tokens
- `scripts/lint_slack_text.py`: finds CommonMark leftovers (`**`, `[](url)`, `#` headings, tables) in a message and suggests native mrkdwn fixes. `--fix` prints a converted version
- `scripts/rich_text_blocks.py`: converts the simple syntax in section 3-0 to rich_text JSON. `--text` prints the plain fallback
- Slack docs: formatting https://docs.slack.dev/messaging/formatting-message-text/ and Block Kit Builder https://app.slack.com/block-kit-builder
- Based on the community skills `sirkitree/slack-markdown-formatter`, `slack-advanced-formatting` and `slack-block-kit-ui`, with the route-by-route differences and posting steps added
