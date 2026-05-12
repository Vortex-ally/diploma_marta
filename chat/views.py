import json
import logging
import time
import urllib.error

from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from velos.chat.services.chips import suggest_chips
from velos.chat.services.knowledge import site_knowledge_block
from velos.chat.services.openrouter import build_openrouter_messages, call_openrouter
from velos.chat.services.wizard import (
    default_wizard_state,
    handle_bike_wizard,
    should_start_bike_wizard,
)
from velos.chat.models import AIChatRecord

logger = logging.getLogger('velo.chat')

DEMO_MAX_GUEST_MESSAGES = 2
DEMO_SESSION_KEY = 'velo_ai_demo_messages'
GUEST_LIMIT_RESPONSE = 'Для повного доступу до AI-помічника зареєструйтесь або увійдіть в акаунт'


@csrf_protect
@require_POST
def ai_chat(request):
    t0 = time.monotonic()
    try:
        data = json.loads(request.body)
        user_message = (data.get('message') or '').strip()
        messages = data.get('messages') or []
        wizard_state = data.get('wizard_state') or default_wizard_state()

        if not messages and user_message:
            messages = [{'role': 'user', 'content': user_message}]
        if not messages:
            return JsonResponse({'error': 'Повідомлення порожнє'}, status=400)

        is_guest = not request.user.is_authenticated
        if is_guest:
            used = int(request.session.get(DEMO_SESSION_KEY, 0) or 0)
            if used >= DEMO_MAX_GUEST_MESSAGES:
                chips = ['Увійти', 'Реєстрація', 'Каталог']
                return JsonResponse(
                    {
                        'response': GUEST_LIMIT_RESPONSE,
                        'demo': True,
                        'require_login': True,
                        'login_url': f"{reverse('login')}?next={request.get_full_path()}",
                        'quick_chips': chips,
                        'recommended_products': [],
                        'wizard_state': default_wizard_state(),
                    }
                )
            request.session[DEMO_SESSION_KEY] = used + 1

        # Майстер підбору з вільного тексту («розумний підбір» тощо)
        if is_guest and (
            wizard_state.get('mode') != 'none'
            or should_start_bike_wizard(user_message)
            or (user_message and 'підбір' in user_message.lower())
        ):
            chips = ['Увійти', 'Реєстрація', 'Каталог']
            return JsonResponse(
                {
                    'response': GUEST_LIMIT_RESPONSE,
                    'demo': True,
                    'require_login': True,
                    'login_url': f"{reverse('login')}?next={request.get_full_path()}",
                    'quick_chips': chips,
                    'recommended_products': [],
                    'wizard_state': default_wizard_state(),
                }
            )

        if wizard_state.get('mode') == 'none' and should_start_bike_wizard(user_message):
            wizard_state = {'mode': 'bike', 'bike_step': 'budget', 'data': {}}

        wiz = handle_bike_wizard(request, wizard_state, user_message)
        if wiz is not None:
            if request.user.is_authenticated and user_message:
                try:
                    AIChatRecord.objects.create(
                        user=request.user,
                        user_message=user_message,
                        assistant_message=(wiz.get('response') or ''),
                        model='wizard',
                        is_wizard=True,
                    )
                except Exception:
                    logger.exception('chat_record_save_failed wizard=1')
            logger.info(
                'chat_wizard step=%s ms=%s',
                wizard_state.get('bike_step'),
                int((time.monotonic() - t0) * 1000),
            )
            return JsonResponse(wiz)

        api_key = getattr(settings, 'OPENROUTER_API_KEY', '') or ''
        model = getattr(settings, 'OPENROUTER_MODEL', 'openai/gpt-4o-mini')
        referer = getattr(settings, 'OPENROUTER_HTTP_REFERER', '') or ''

        site_knowledge = site_knowledge_block(request)

        if not api_key:
            demo = (
                'Привіт! Це демо-режим без API-ключа OpenRouter. '
                'Додай OPENROUTER_API_KEY у .env — тоді я зможу відповідати з урахуванням каталогу. '
                'А поки скористайтесь «Розумний підбір велосипеда» — він працює без зовнішнього API.'
            )
            chips = suggest_chips(user_message, demo)
            return JsonResponse(
                {
                    'response': demo,
                    'demo': True,
                    'guest_demo': is_guest,
                    'guest_left': max(0, DEMO_MAX_GUEST_MESSAGES - int(request.session.get(DEMO_SESSION_KEY, 0) or 0)),
                    'quick_chips': chips,
                    'recommended_products': [],
                    'wizard_state': wizard_state,
                }
            )

        or_messages = build_openrouter_messages(messages, site_knowledge=site_knowledge)
        if len(or_messages) < 2:
            return JsonResponse({'error': 'Некоректна історія повідомлень'}, status=400)

        try:
            content, raw = call_openrouter(api_key, model, or_messages, referer=referer)
        except urllib.error.HTTPError as e:
            try:
                error_body = e.read().decode('utf-8')
            except Exception:
                error_body = str(e)
            logger.warning('openrouter_http %s: %s', e.code, error_body[:500])
            return JsonResponse(
                {'error': f'OpenRouter: {e.code}', 'details': error_body},
                status=502,
            )

        if not content.strip():
            logger.warning('openrouter_empty_response keys=%s', list((raw or {}).keys()))
            return JsonResponse(
                {'error': 'Модель повернула порожній текст', 'details': raw},
                status=502,
            )

        chips = suggest_chips(user_message, content)
        if request.user.is_authenticated and user_message:
            try:
                AIChatRecord.objects.create(
                    user=request.user,
                    user_message=user_message,
                    assistant_message=content.strip(),
                    model=model,
                    is_wizard=False,
                )
            except Exception:
                logger.exception('chat_record_save_failed wizard=0')
        logger.info(
            'chat_ai_ok model=%s ms=%s',
            model,
            int((time.monotonic() - t0) * 1000),
        )
        return JsonResponse(
            {
                'response': content.strip(),
                'quick_chips': chips,
                'recommended_products': [],
                'wizard_state': wizard_state,
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Некоректний JSON запиту'}, status=400)
    except Exception as e:
        logger.exception('chat_unhandled')
        return JsonResponse({'error': str(e)}, status=500)
