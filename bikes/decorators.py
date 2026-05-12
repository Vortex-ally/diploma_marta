from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


DEFAULT_LOGIN_MESSAGE = 'Увійдіть або зареєструйтесь, щоб отримати доступ до цієї функції'


def login_required_with_message(message: str = DEFAULT_LOGIN_MESSAGE):
    """
    Like login_required, but also shows a Django message and preserves `next`.
    Uses the project's `login` named URL.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if request.user.is_authenticated:
                return view_func(request, *args, **kwargs)

            messages.info(request, message)
            login_url = reverse('login')
            nxt = request.get_full_path()
            return redirect(f'{login_url}?next={nxt}')

        return _wrapped

    return decorator

