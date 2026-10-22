# Сводка по городу

CLI для получения погоды и курса валюты к рублю.

## Требования

Python 3.12.x

Нужен доступ к интернету. Зависимости: Requests для HTTP и Ruff для проверки кода.
Их версии указаны в `requirements.txt`. Тесты используют стандартный `unittest`.

## Установка

Из корня проекта, macOS/Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

В новом терминале снова активируйте `.venv` перед выполнением команд.

## Запуск

```bash
python main.py --city Moscow
python main.py --city Moscow --currency EUR
python main.py --city "Санкт-Петербург" --currency usd --json
```

`--city` обязателен. `--currency` по умолчанию равен `USD`, регистр букв
нормализуется. Названия с пробелами заключайте в кавычки. По геокодингу
выбирается первое совпадение, поэтому для одноимённых городов проверьте результат
или уточните запрос, например `--city "Paris, France"`.

Пример формата текстового результата (значения меняются со временем):

```text
Город: Moscow
Погода: -3.2°C, clear sky
Тёплая одежда: да
USD→RUB: 92.15
Дорогой курс: нет
```

`--json` печатает ту же сводку как JSON:

```json
{
  "city": "Moscow",
  "weather": {
    "temp_c": -3.2,
    "description": "clear sky",
    "warm_clothes": true
  },
  "rates": {
    "currency": "USD",
    "rate_to_rub": 92.15,
    "expensive": false
  }
}
```

Правила в `processing/preprocessing.py`:

- `warm_clothes` включён строго при температуре ниже 0 °C. При 0 он выключен.
- `expensive` включён строго при курсе выше 100 рублей. При 100 он выключен.

## Коды выхода

| Код | Значение | Пример |
| --- | --- | --- |
| 0 | Успех | `python main.py --city Moscow` |
| 2 | Ошибка аргументов | Нет `--city`, пустой город, код валюты не из трёх латинских букв |
| 3 | Город или валюта не найдены | Несуществующий город или `--currency ZZZ` |
| 4 | Ошибка внешнего сервиса | Исчерпаны повторы, неожиданный HTTP-статус, некорректный JSON или поля |

Успешная сводка идёт в stdout, сообщения об ошибках — в stderr.
После команды код можно посмотреть через `echo $?` в macOS/Linux
или `$LASTEXITCODE` в PowerShell. `--help` выводит справку с кодом 0.

## Компоненты и поток запросов

| Файл | Ответственность |
| --- | --- |
| `main.py` | argparse, выбор текст/JSON, вывод и коды выхода |
| `processing/service.py` | `build_city_summary(city, currency="USD")`, сборка результата |
| `processing/preprocessing.py` | Два правила и типы обработанных данных |
| `clients/weather.py` | Геокодинг, прогноз, проверка полей, перевод WMO-кода в описание |
| `clients/rates.py` | Курс выбранной валюты к RUB и проверка валютной пары |
| `clients/http.py` | GET, timeout, retry, проверка статуса и JSON |
| `clients/validation.py` | Проверка конечных чисел, исключение bool, NaN и Infinity |
| `clients/exceptions.py` | Понятные ошибки приложения и HTTP-статусов |
| `tests/` | Проверки HTTP-клиента, контрактов API, порогов, сборки и CLI |

Порядок работы:

1. CLI проверяет аргументы и вызывает `build_city_summary`.
2. `get_weather` ищет координаты города через Open-Meteo Geocoding.
3. По координатам Open-Meteo Forecast возвращает текущую температуру и WMO-код.
4. `get_rate` получает у Frankfurter курс выбранной валюты к RUB.
5. Сервис передаёт проверенные данные правилам предобработки и собирает словарь.
6. CLI печатает текст или JSON. При ошибке полной сводки нет.

## Контракты внешних API

Все внешние обращения выполняются методом GET по HTTPS.

| API | Запрос | Используемые поля ответа |
| --- | --- | --- |
| [Open-Meteo Geocoding](https://open-meteo.com/en/docs/geocoding-api) | `https://geocoding-api.open-meteo.com/v1/search?name=Moscow&count=1&language=en&format=json` | `results[0].latitude`, `results[0].longitude` |
| [Open-Meteo Forecast](https://open-meteo.com/en/docs) | `https://api.open-meteo.com/v1/forecast?latitude=55.75&longitude=37.62&current=temperature_2m,weather_code&temperature_unit=celsius` | `current.temperature_2m`, `current.weather_code` |
| [Frankfurter v2](https://frankfurter.dev/) | `https://api.frankfurter.dev/v2/rate/USD/RUB` | `base`, `quote`, положительный `rate` |

Перед разбором проверяются HTTP 200 и JSON Content-Type. Затем проверяются
структура и поля ответа. Координаты должны быть в допустимых диапазонах,
температура и курс — конечными числами, код погоды — известным целым WMO-кодом.
Frankfurter должен вернуть именно запрошенную валюту и RUB.
Неизвестные дополнительные поля не мешают работе.

Пустой или отсутствующий `results` означает, что город не найден.
Frankfurter v2 возвращает 422 для неизвестной валюты; 404 также переводится
в ошибку поиска. Остальные постоянные HTTP-ошибки не повторяются.
Курс Frankfurter обновляется по данным его поставщиков, обычно ежедневно,
и не является котировкой для обмена в банке.

## Timeout и retry

На каждой попытке используется `timeout=(3, 7)`: до 3 секунд на соединение
и 7 секунд ожидания данных при чтении. Это настройки Requests, а не общий
дедлайн всей программы. С учётом повторов и пауз выполнение может занять дольше.

Всего три попытки, то есть два повтора после первой, при:

- `requests.exceptions.Timeout` и `requests.exceptions.ConnectionError`;
- HTTP 500, 502, 503, 504;
- HTTP 429.

Паузы — 1 и 2 секунды плюс случайная добавка до 0.25 секунды.
Для 429 неотрицательный числовой `Retry-After` задаёт время ожидания в секундах,
включая 0. Если заголовок отсутствует или некорректен, применяется обычная пауза.
После последней попытки лишней паузы нет. Ответы закрываются после обработки.

## Аутентификация и секреты

В этой CLI нет регистрации, входа, пользователей, сессий, JWT, access token
или refresh token. Выбранные публичные API не требуют API-ключа для этого
учебного сценария. `WEATHER_API_KEY` не используется, поскольку клиент работает
с Open-Meteo. OAuth и обновление токенов не нужны.

В `clients/http.py` приложение задаёт только заголовки `Accept` и `User-Agent`.
Код не создаёт `Authorization` и не хранит учётные данные на диске.
Перенаправления отключены, HTTPS проверяется стандартными средствами Requests.
Сама библиотека Requests по умолчанию может учитывать системные настройки
прокси и файл `.netrc`; приложение не управляет этими внешними настройками.
`.env`, окружение и кеши исключены из Git. Для запуска нужны только зависимости
и сеть, передавать токены GitHub программе не требуется.

## Проверки

```bash
python -m unittest discover -v
ruff check .
ruff format --check .
```

Тесты не обращаются к сети: HTTP-ответы и задержки подменяются через
`unittest.mock`. Проверяются повторные попытки, `Retry-After`, HTTP-ошибки,
неверные форматы и поля, оба порога и коды выхода 0/2/3/4.

Для ручной проверки интеграции:

```bash
python main.py --city Moscow
python main.py --city Moscow --currency EUR --json
python main.py --city NoSuchCityQzxv12345
python main.py --city Moscow --currency ZZZ
```

Дополнительные возможности: `--json`, аннотации типов и тесты клиентов через
`unittest.mock`. Кеш курса и logging с run_id в этот вариант не входят.
Рабочая ветка `homework-2` предназначена для Pull Request в `main` без слияния
до проверки.
