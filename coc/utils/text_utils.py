from __future__ import annotations

import json
import math
import re
from typing import Iterable


def safe_json_loads(text: str) -> dict:
    payload = (text or "").strip()
    if not payload:
        return {}
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", payload, re.DOTALL)
        if fenced:
            return json.loads(fenced.group(1))
        match = re.search(r"\{.*\}", payload, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    return {}


def normalize_task_name(task_name: str) -> str:
    normalized = (task_name or "").strip().lower().replace("-", "").replace("_", "")
    aliases = {
        "tombench": "tombench",
        "socialiqa": "socialiqa",
        "sotopia": "sotopia",
    }
    return aliases.get(normalized, normalized)


def tokenize_text(text: str) -> list[str]:
    return re.findall(r"[\u4e00-\u9fffA-Za-z0-9_]+", (text or "").lower())


def format_history(history: Iterable[dict], max_items: int = 8) -> str:
    turns = list(history)[-max_items:]
    if not turns:
        return "(empty)"
    lines = []
    for item in turns:
        role = item.get("role", "user")
        content = (item.get("content", "") or "").strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines) if lines else "(empty)"


def keyword_overlap_score(text: str, keywords: Iterable[str]) -> float:
    haystack = set(tokenize_text(text))
    needles = [item for item in (str(k).strip().lower() for k in keywords) if item]
    if not needles:
        return 0.0
    hits = 0
    for keyword in needles:
        if keyword in haystack or keyword in (text or "").lower():
            hits += 1
    return round(hits / len(needles), 3)


def cosine_similarity(a: list[float] | None, b: list[float] | None) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return max(0.0, min(1.0, round((dot / (norm_a * norm_b) + 1) / 2, 4)))


def truncate_text(text: str, max_chars: int = 1200) -> str:
    content = (text or "").strip()
    if len(content) <= max_chars:
        return content
    return content[: max_chars - 3].rstrip() + "..."


def extract_choice_label(text: str, valid_letters: Iterable[str]) -> str:
    letters = "".join(sorted({str(letter).upper() for letter in valid_letters if str(letter).strip()}))
    if not letters:
        return ""
    content = text or ""
    bracket = re.search(rf"\[\[([{letters}])\]\]", content, re.IGNORECASE)
    if bracket:
        return bracket.group(1).upper()
    answer_line = re.search(rf"(?:final answer|answer)\s*[:：]?\s*([{letters}])\b", content, re.IGNORECASE)
    if answer_line:
        return answer_line.group(1).upper()
    for line in reversed(content.splitlines()):
        stripped = line.strip()
        plain = re.fullmatch(rf"([{letters}])", stripped, re.IGNORECASE)
        if plain:
            return plain.group(1).upper()
    matches = re.findall(rf"\b([{letters}])\b", content, re.IGNORECASE)
    return matches[-1].upper() if matches else ""


def first_nonempty(*values: str | None) -> str:
    for value in values:
        if value:
            return value
    return ""


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "_", (text or "").strip())
    return slug.strip("_") or "sample"


def clean_think_tags(text: str) -> str:
    """清理 <think>...</think> 标签"""
    return re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL).strip()


def extract_first_json(text: str) -> dict | None:
    """从文本中提取第一个 JSON 对象"""
    text = clean_think_tags(text)
    # 尝试直接解析
    try:
        return json.loads(text)
    except Exception:
        pass
    # 尝试从 ```json ... ``` 中提取
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # 尝试找第一个 { ... }
    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                try:
                    return json.loads(text[start:i + 1])
                except Exception:
                    start = -1
    return None


def recover_answer_by_option_text(text: str, options: dict[str, str]) -> str:
    """通过选项文本匹配恢复答案标签"""
    text_lower = (text or "").lower().strip()
    if not text_lower:
        return ""
    best_label = ""
    best_len = 0
    for label, opt_text in options.items():
        opt_lower = opt_text.lower().strip()
        if opt_lower and opt_lower in text_lower and len(opt_lower) > best_len:
            best_label = label
            best_len = len(opt_lower)
    return best_label


def recover_answer_by_last_line(text: str, options: dict[str, str]) -> str:
    """从最后一行匹配选项文本"""
    lines = [l.strip() for l in (text or "").strip().splitlines() if l.strip()]
    if not lines:
        return ""
    last_line = lines[-1].lower()
    for label, opt_text in options.items():
        if opt_text.lower().strip() in last_line:
            return label
    return ""


def md5_short(text: str, length: int = 8) -> str:
    """返回文本的短 MD5 摘要"""
    import hashlib
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:length]
