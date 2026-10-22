import argparse
import json
import re
import sys

from clients.exceptions import ExternalServiceError, NotFoundError
from processing.service import CitySummary, build_city_summary


def city_argument(value: str) -> str:
    value = value.strip()
    if len(value) < 2:
        raise argparse.ArgumentTypeError(
            "Название города должно содержать хотя бы 2 символа"
        )
    return value


def currency_argument(value: str) -> str:
    value = value.strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", value):
        raise argparse.ArgumentTypeError("Валюта должна быть ISO-кодом из трёх букв")
    return value


def format_summary(summary: CitySummary) -> str:
    weather = summary["weather"]
    rates = summary["rates"]
    return "\n".join(
        [
            f"Город: {summary['city']}",
            f"Погода: {weather['temp_c']:.1f}°C, {weather['description']}",
            f"Тёплая одежда: {'да' if weather['warm_clothes'] else 'нет'}",
            f"{rates['currency']}→RUB: {rates['rate_to_rub']:.2f}",
            f"Дорогой курс: {'да' if rates['expensive'] else 'нет'}",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Погода и курс валюты для города")
    parser.add_argument(
        "--city", required=True, type=city_argument, help="Название города"
    )
    parser.add_argument(
        "--currency", default="USD", type=currency_argument, help="ISO-код валюты"
    )
    parser.add_argument("--json", action="store_true", help="Вывести сводку в JSON")
    args = parser.parse_args(argv)
    try:
        summary = build_city_summary(args.city, args.currency)
    except NotFoundError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 3
    except ExternalServiceError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 4
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False))
    else:
        print(format_summary(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
