# City Summary

Консольная утилита: погода в городе и курс валюты к рублю.
Данные берутся из Open-Meteo и Frankfurter, ключи API не нужны.

## Требования

Python 3.12.x, зависимости из requirements.txt.

## Установка

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Запуск

```bash
python main.py --city Moscow
python main.py --city Moscow --currency EUR
```

При температуре ниже 0 включается флаг тёплой одежды,
при курсе выше 100 — флаг дорогого курса.

Коды выхода: 0 — успех, 2 — ошибка аргументов,
3 — город или валюта не найдены, 4 — ошибка внешнего сервиса.
