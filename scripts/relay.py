#!/usr/bin/env python3
"""Minimal GitHub Issues <-> DeepSeek relay. Python standard library only."""

import json
import os
import sys
import urllib.error
import urllib.request


REPO = os.environ["GITHUB_REPOSITORY"]
OWNER = REPO.split("/")[0].lower()
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
MODEL = "deepseek-flash"
REPLY_MARKER = "<!-- deepseek-relay-answer -->"
GITHUB_API = "https://api.github.com"
DEEPSEEK_API = "https://api.deepseek.com/chat/completions"


def request_json(url, *, token, method="GET", payload=None, timeout=30):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    headers = {
        "Accept": "application/vnd.github+json" if url.startswith(GITHUB_API) else "application/json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "chatgpt-deepseek-relay/1.0",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    if url.startswith(GITHUB_API):
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def comment(issue_number, body):
    return request_json(
        f"{GITHUB_API}/repos/{REPO}/issues/{issue_number}/comments",
        token=GITHUB_TOKEN,
        method="POST",
        payload={"body": body[:58000]},
    )


def history(issue_number, issue_body, event_name):
    """Use original request + a small chronological history of owner/bot comments."""
    messages = [{"role": "system", "content":
                 "你是 DeepSeek 执行助手。准确遵循用户任务，优先提供清晰、可验证的结果。"
                 "不要声称运行了没有实际运行的代码或工具。请用简体中文回复。"}]
    initial = (issue_body or "").strip()[:16000]
    if initial:
        messages.append({"role": "user", "content": initial})

    if event_name == "issue_comment":
        items = request_json(
            f"{GITHUB_API}/repos/{REPO}/issues/{issue_number}/comments?per_page=100",
            token=GITHUB_TOKEN,
        )
        turns = []
        for item in items:
            author = (item.get("user") or {}).get("login", "").lower()
            body = (item.get("body") or "").strip()
            if author == OWNER and body:
                turns.append({"role": "user", "content": body[:16000]})
            elif author == "github-actions[bot]" and body.startswith(REPLY_MARKER):
                # Strip machine metadata after answer, if present.
                answer = body[len(REPLY_MARKER):].split("\n\n---\n", 1)[0].strip()
                if answer:
                    turns.append({"role": "assistant", "content": answer[:16000]})
        messages.extend(turns[-12:])
    return messages


def error_label(exc):
    if isinstance(exc, urllib.error.HTTPError):
        status = exc.code
        labels = {
            400: "请求格式不被接受，请检查 API 参数。",
            401: "DeepSeek API Key 无效或未被接受。",
            402: "DeepSeek 账户余额不足。",
            403: "API 或 GitHub 权限不足。",
            429: "触发了 DeepSeek 请求频率限制。",
        }
        return f"HTTP {status}：{labels.get(status, '服务端返回错误，请检查 GitHub Actions 运行记录。')}"
    if isinstance(exc, (TimeoutError, urllib.error.URLError)):
        return "网络连接失败或请求超时。"
    return f"通信失败（{type(exc).__name__}）。请检查 Actions 运行记录。"


def main():
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as f:
        event = json.load(f)
    event_name = os.environ["GITHUB_EVENT_NAME"]
    issue = event.get("issue") or {}
    number = issue.get("number")
    author = ((issue.get("user") or {}).get("login") or "").lower()
    title = issue.get("title") or ""
    if not number or author != OWNER or not title.startswith("[DeepSeek]"):
        print("Skipped unrelated issue.")
        return
    if event_name == "issue_comment":
        commenter = (((event.get("comment") or {}).get("user") or {}).get("login") or "").lower()
        if commenter != OWNER:
            print("Skipped non-owner comment.")
            return

    if not DEEPSEEK_KEY:
        comment(number, "⚠️ **桥接程序已启动，但尚未配置 API Key。**\n\n请在仓库 Settings → Secrets and variables → Actions 中添加仓库密钥 `DEEPSEEK_API_KEY`。配置后，在此 Issue 下评论任意新任务即可重试。")
        print("Missing DeepSeek API Key.")
        return

    try:
        messages = history(number, issue.get("body", ""), event_name)
        if not any(m["role"] == "user" for m in messages):
            comment(number, "⚠️ 任务内容为空，请输入具体指令。")
            return
        result = request_json(
            DEEPSEEK_API,
            token=DEEPSEEK_KEY,
            method="POST",
            payload={"model": MODEL, "messages": messages, "max_tokens": 6000, "stream": False, "thinking": {"type": "disabled"}},
            timeout=200,
        )
        choice = result["choices"][0]
        response = ((choice.get("message") or {}).get("content") or "").strip()
        if not response:
            response = "API 返回成功，但本次没有可展示的正文，请缩短任务后重试。"
        usage = result.get("usage") or {}
        usage_str = f"{usage.get('total_tokens', '未知')} tokens"
        comment(number, f"{REPLY_MARKER}\n### 🤖 DeepSeek 回复\n\n{response[:45000]}\n\n---\n_模型：{MODEL} · 用量：{usage_str} · 状态：{choice.get('finish_reason', '未知')}_")
        print(f"DeepSeek replied on issue #{number}.")
    except Exception as exc:
        # Never publish raw exceptions, HTTP response bodies or credentials.
        try:
            comment(number, "❌ **桥接任务失败**\n\n" + error_label(exc))
        except Exception:
            print("Unable to post failure notice.", file=sys.stderr)
            raise
        print(f"Task failed: {type(exc).__name__}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
