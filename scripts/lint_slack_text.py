#!/usr/bin/env python3
"""
Lint a message meant for Slack native mrkdwn (an MCP server with content_type text/plain,
chat.postMessage or an incoming webhook; not the Slack connector in Claude, which uses
CommonMark). Flags standard markdown and CommonMark leftovers that do not render in Slack,
and suggests native mrkdwn fixes.

Usage:
  python3 lint_slack_text.py < message.txt
  echo "**bold** [docs](https://x.com)" | python3 lint_slack_text.py
  python3 lint_slack_text.py --fix < message.txt      # print an auto-converted version

Exit code 1 if any issue was found (0 if clean), so it can gate a send step.
"""
import re, sys, argparse

CHECKS = [
    # (name, regex, hint)
    ("bold-commonmark", re.compile(r"\*\*(.+?)\*\*"),
     "CommonMark bold `**x**` -> native mrkdwn uses `*x*`"),
    ("strike-commonmark", re.compile(r"~~(.+?)~~"),
     "CommonMark strikethrough `~~x~~` -> native uses `~x~`"),
    ("md-link", re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)"),
     "markdown link `[t](url)` -> native uses `<url|t>`"),
    ("md-image", re.compile(r"!\[([^\]]*)\]\((https?://[^)]+)\)"),
     "markdown image `![alt](url)` does not work in Slack -> use a Block Kit image block"),
    ("heading", re.compile(r"^#{1,6}\s+\S", re.M),
     "`#` headings do not work -> use `*Heading*` (bold) or a Block Kit header"),
    ("table", re.compile(r"^\s*\|.+\|\s*$", re.M),
     "markdown tables do not work -> use Block Kit section.fields"),
    ("task-list", re.compile(r"^\s*[-*]\s+\[[ xX]\]", re.M),
     "task lists `- [ ]` do not work -> use `•` with an emoji such as :white_check_mark:"),
    ("bare-at-mention", re.compile(r"(?<![<\w])@(?:here|channel|everyone)\b"),
     "plain @here/@channel does not notify -> use `<!here>` `<!channel>`"),
]

def convert(text):
    text = re.sub(r"\*\*(.+?)\*\*", r"*\1*", text)
    text = re.sub(r"~~(.+?)~~", r"~\1~", text)
    text = re.sub(r"!\[([^\]]*)\]\((https?://[^)]+)\)", r"<\2|\1>", text)  # best-effort
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"<\2|\1>", text)
    text = re.sub(r"^(#{1,6})\s+(.*)$", r"*\2*", text, flags=re.M)
    return text

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true", help="print auto-converted native-mrkdwn text")
    args = ap.parse_args()
    text = sys.stdin.read()

    if args.fix:
        sys.stdout.write(convert(text))
        return

    issues = []
    for name, rx, hint in CHECKS:
        for m in rx.finditer(text):
            line = text[:m.start()].count("\n") + 1
            issues.append((line, name, m.group(0).replace("\n", "\\n")[:60], hint))
    if not issues:
        print("OK: no native mrkdwn issues found.", file=sys.stderr)
        return
    issues.sort()
    print(f"{len(issues)} issue(s) to fix:", file=sys.stderr)
    for line, name, snippet, hint in issues:
        print(f"  L{line} [{name}] {snippet!r}\n        -> {hint}", file=sys.stderr)
    print("\nRun with --fix to print a converted version (check tables, images and headings by hand).", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()
