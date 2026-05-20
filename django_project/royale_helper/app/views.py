from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .services.api_client import (
    PlayerNotFoundError,
    ServiceUnavailableError,
    get_decks,
    get_player,
    get_recommendations_by_tag,
    get_zodiac_card,
)


def index(request: HttpRequest) -> HttpResponse:
    return render(request, "app/index.html")


def decks(request: HttpRequest) -> HttpResponse:
    context: dict = {}
    try:
        context["decks"] = get_decks(limit=50)
    except ServiceUnavailableError as exc:
        context["error"] = f"Не удалось загрузить колоды: {exc}"
        context["decks"] = []
    return render(request, "app/decks.html", context)


@require_http_methods(["GET", "POST"])
def recommend_deck(request: HttpRequest) -> HttpResponse:
    context: dict = {}

    if request.method != "POST":
        return render(request, "app/recommend.html", context)

    player_tag = request.POST.get("player_tag", "").strip()
    context["player_tag"] = player_tag

    if not player_tag:
        context["error"] = "Введите тег игрока."
        return render(request, "app/recommend.html", context)

    try:
        player = get_player(player_tag)
    except PlayerNotFoundError as exc:
        context["error"] = str(exc)
        return render(request, "app/recommend.html", context)
    except ServiceUnavailableError as exc:
        context["error"] = str(exc)
        return render(request, "app/recommend.html", context)

    context["player"] = player

    try:
        result = get_recommendations_by_tag(
            player_tag=player_tag,
            limit=3,
            rating_limit=10,
        )
    except ServiceUnavailableError as exc:
        context["error"] = f"Не удалось получить рекомендации: {exc}"
        return render(request, "app/recommend.html", context)

    context["current_recommendations"] = result.get("current", [])
    context["potential_recommendations"] = result.get("potential", [])

    if not result.get("current") and not result.get("potential"):
        context["info"] = "В базе пока нет метовых колод или нет подходящих колод для вашего профиля."

    return render(request, "app/recommend.html", context)


ZODIAC_SIGNS = [
    ("aries", "\u041e\u0432\u0435\u043d"),
    ("taurus", "\u0422\u0435\u043b\u0435\u0446"),
    ("gemini", "\u0411\u043b\u0438\u0437\u043d\u0435\u0446\u044b"),
    ("cancer", "\u0420\u0430\u043a"),
    ("leo", "\u041b\u0435\u0432"),
    ("virgo", "\u0414\u0435\u0432\u0430"),
    ("libra", "\u0412\u0435\u0441\u044b"),
    ("scorpio", "\u0421\u043a\u043e\u0440\u043f\u0438\u043e\u043d"),
    ("sagittarius", "\u0421\u0442\u0440\u0435\u043b\u0435\u0446"),
    ("capricorn", "\u041a\u043e\u0437\u0435\u0440\u043e\u0433"),
    ("aquarius", "\u0412\u043e\u0434\u043e\u043b\u0435\u0439"),
    ("pisces", "\u0420\u044b\u0431\u044b"),
]


@require_http_methods(["GET", "POST"])
def zodiac(request: HttpRequest) -> HttpResponse:
    context: dict = {"signs": ZODIAC_SIGNS}

    if request.method != "POST":
        return render(request, "app/zodiac.html", context)

    sign = request.POST.get("sign", "").strip()
    context["selected_sign"] = sign

    if not sign:
        context["error"] = "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0437\u043d\u0430\u043a \u0437\u043e\u0434\u0438\u0430\u043a\u0430."
        return render(request, "app/zodiac.html", context)

    try:
        result = get_zodiac_card(sign)
    except ServiceUnavailableError as exc:
        context["error"] = f"\u0421\u0435\u0440\u0432\u0438\u0441 \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u0435\u043d: {exc}"
        return render(request, "app/zodiac.html", context)

    context["card"] = result.get("card", {})
    return render(request, "app/zodiac.html", context)
