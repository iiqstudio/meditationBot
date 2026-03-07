from src.bot.services.tracker import format_minutes_ru


def test_format_minutes_ru() -> None:
    assert format_minutes_ru(5) == "5 мин."
    assert format_minutes_ru(60) == "1 ч."
    assert format_minutes_ru(65) == "1 ч. 5 мин."
    assert format_minutes_ru(-65) == "-1 ч. 5 мин."
