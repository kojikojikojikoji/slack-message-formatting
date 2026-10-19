#!/usr/bin/env python3
"""Convert a simple text syntax to a Slack Block Kit rich_text block.

To get real lists (with nesting) and bold text in Slack, send a rich_text block
instead of building lists by hand with "•" in mrkdwn. This script turns the
syntax below into a rich_text JSON array.

  # Heading           -> bold paragraph (a line that starts with "# ")
  - item              -> bullet (level 1)
    - child item      -> bullet (level 2; indent with 2 or more spaces)
  1. item             -> ordered item
  *bold*              -> bold (inline; one asterisk, same as mrkdwn)
  <URL|label>         -> link (same as mrkdwn)
  <@U012AB3CD>        -> user mention
  blank line          -> paragraph break
  any other line      -> plain paragraph

Usage:
  python3 rich_text_blocks.py < body.txt          -> blocks JSON on stdout
  python3 rich_text_blocks.py --text < body.txt   -> plain fallback text for notifications

With an MCP server's "add message" tool, pass this JSON as `blocks` and the fallback as `text`.
With curl, use --data-urlencode "blocks=$(python3 rich_text_blocks.py < body.txt)" and "text=...".
"""

import json
import re
import sys

INLINE = re.compile(r"(\*[^*\n]+\*|<[^>\n]+>)")


def inline(text):
    out = []
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("*") and part.endswith("*") and len(part) > 2:
            out.append({"type": "text", "text": part[1:-1], "style": {"bold": True}})
        elif part.startswith("<@") and part.endswith(">"):
            out.append({"type": "user", "user_id": part[2:-1]})
        elif part.startswith("<#") and part.endswith(">"):
            out.append({"type": "channel", "channel_id": part[2:-1].split("|")[0]})
        elif part.startswith("<") and part.endswith(">"):
            body = part[1:-1]
            url, _, label = body.partition("|")
            link = {"type": "link", "url": url}
            if label:
                link["text"] = label
            out.append(link)
        else:
            out.append({"type": "text", "text": part})
    return out or [{"type": "text", "text": ""}]


def build(source):
    elements = []
    pending = None  # groups consecutive list items of the same style and indent

    def flush():
        nonlocal pending
        if pending:
            elements.append(pending)
            pending = None

    for raw in source.splitlines():
        if not raw.strip():
            flush()
            continue
        stripped = raw.lstrip(" ")
        indent = (len(raw) - len(stripped)) // 2
        m = re.match(r"^(-|\d+\.)\s+(.*)$", stripped)
        if m:
            style = "bullet" if m.group(1) == "-" else "ordered"
            item = {"type": "rich_text_section", "elements": inline(m.group(2))}
            if pending and pending["style"] == style and pending["indent"] == indent:
                pending["elements"].append(item)
            else:
                flush()
                pending = {"type": "rich_text_list", "style": style, "indent": indent, "elements": [item]}
            continue
        flush()
        if stripped.startswith("# "):
            # Headings also parse links and mentions; every element is made bold
            heading = inline(stripped[2:].replace("*", ""))
            for el in heading:
                if el["type"] in ("text", "link"):
                    el["style"] = {"bold": True}
            elements.append({"type": "rich_text_section", "elements": heading})
        else:
            elements.append({"type": "rich_text_section", "elements": inline(stripped)})
    flush()
    return [{"type": "rich_text", "elements": elements}]


def fallback(source):
    lines = []
    for raw in source.splitlines():
        s = raw.strip()
        if not s:
            continue
        s = re.sub(r"^# ", "", s)
        s = re.sub(r"^(\d+\.|-)\s+", "• ", s)
        s = re.sub(r"<([^|>]+)\|([^>]+)>", r"\2", s)
        s = s.replace("*", "")
        lines.append(s)
    return "\n".join(lines)


if __name__ == "__main__":
    body = sys.stdin.read()
    if "--text" in sys.argv[1:]:
        print(fallback(body))
    else:
        print(json.dumps(build(body), ensure_ascii=False))
