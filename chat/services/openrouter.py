"""Виклик OpenRouter API (синхронний HTTP)."""

import json
import ssl
import urllib.error
import urllib.request

import certifi

from velos.chat.constants import OPENROUTER_URL, SYSTEM_PROMPT


def _https_context():
    return ssl.create_default_context(cafile=certifi.where())


def build_openrouter_messages(history, site_knowledge: str = ''):
    """history: list of {role, content} — user | assistant"""
    system_text = SYSTEM_PROMPT
    if site_knowledge:
        system_text = (
            f'{SYSTEM_PROMPT}\n\n--- ДАНІ З САЙТУ (каталог VeloUkraine) ---\n{site_knowledge}'
        )
    msgs = [{'role': 'system', 'content': system_text}]
    for m in history[-12:]:
        role = m.get('role')
        content = (m.get('content') or '').strip()
        if not content:
            continue
        if role == 'user':
            msgs.append({'role': 'user', 'content': content})
        elif role in ('assistant', 'bot'):
            msgs.append({'role': 'assistant', 'content': content})
    return msgs


def call_openrouter(api_key: str, model: str, messages: list, referer: str = '') -> tuple[str, dict]:
    """
    Повертає (content, raw_json_choices_parent).
    Кидає urllib.error.HTTPError або повертає порожній content при помилці структури.
    """
    payload = {
        'model': model,
        'messages': messages,
        'max_tokens': 1600,
        'temperature': 0.65,
    }
    req_data = json.dumps(payload).encode('utf-8')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
        'X-Title': 'VeloUkraine',
    }
    if referer:
        headers['Referer'] = referer

    req = urllib.request.Request(OPENROUTER_URL, data=req_data, headers=headers, method='POST')

    with urllib.request.urlopen(req, timeout=60, context=_https_context()) as response:
        result = json.loads(response.read().decode('utf-8'))

    choices = result.get('choices') or []
    if not choices:
        return '', result
    content = (choices[0].get('message') or {}).get('content') or ''
    return content.strip(), result
