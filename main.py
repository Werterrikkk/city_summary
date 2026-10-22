import argparse
import sys

from clients.exceptions import ExternalServiceError, NotFoundError
from processing.service import build_city_summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Сводка по городу")
    parser.add_argument("--city", required=True, help="Название города")
    parser.add_argument(
        "--currency", default="USD", help="Код валюты, например USD или EUR"
    )
    args = parser.parse_args()
    city = args.city.strip()
    currency = args.currency.strip().upper()
    if len(city) < 2:
        parser.error("Введите название города")
    if len(currency) != 3 or not currency.isascii() or not currency.isalpha():
        parser.error("Код валюты должен состоять из трёх латинских букв")

    try:
        summary = build_city_summary(city, currency)
    except NotFoundError as error:
        print(error, file=sys.stderr)
        return 3
    except ExternalServiceError as error:
        print(error, file=sys.stderr)
        return 4

    weather = summary["weather"]
    rates = summary["rates"]
    print(f"Город: {summary['city']}")
    print(f"Погода: {weather['temp_c']}°C, {weather['description']}")
    print(f"Тёплая одежда: {'да' if weather['warm_clothes'] else 'нет'}")
    print(f"{rates['currency']}→RUB: {rates['rate_to_rub']:.2f}")
    print(f"Дорогой курс: {'да' if rates['expensive'] else 'нет'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
