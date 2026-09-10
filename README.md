# telegram-price-bot

Приватный Telegram-бот для одного пользователя: принимает фотографию товара с подписью вида
`Кроссовки женские — 3500 руб`, получает официальный курс RUB/BYN НБРБ, рассчитывает цену,
сохраняет оригинал в Google Drive, добавляет строку в Google Sheets и возвращает готовый пост.

## Требования и архитектура

- Python 3.12+;
- существующие Google Spreadsheet и папка Drive;
- Telegram-бот и OAuth 2.0 Desktop client Google.

`app/bot` содержит только Telegram-слой, `app/services` — бизнес-логику и интеграции,
`app/domain` — модели, `app/utils` — парсер. `ProductService` выполняет pipeline. База данных
не используется: для приватного MVP достаточно множества обработанных `message_id` в памяти.
После перезапуска эта защита обнуляется; постоянную идемпотентность при необходимости лучше
добавить отдельно (например, SQLite), не усложняя текущий сценарий.

## Настройка Telegram

1. Откройте `@BotFather`, выполните `/newbot`, задайте имя и username, сохраните токен.
2. Узнайте свой числовой `user_id`, например отправив сообщение боту `@userinfobot`.
3. Запишите токен и ID в `.env`. Сообщения других пользователей отклоняются до обращений к НБРБ
   и Google.

## Настройка Google OAuth

1. В [Google Cloud Console](https://console.cloud.google.com/) создайте или выберите проект.
2. В **APIs & Services → Library** включите **Google Drive API** и **Google Sheets API**.
3. В **APIs & Services → OAuth consent screen** настройте экран согласия. Для приложения в режиме
   Testing добавьте Google-аккаунт пользователя в список test users.
4. В **APIs & Services → Credentials** создайте OAuth client типа **Desktop app**. Скачайте JSON,
   создайте локально каталог `credentials/` и сохраните файл как
   `credentials/google-oauth-client.json`. Каталог исключён из Git.
5. Откройте таблицу и скопируйте её ID из URL между `/d/` и `/edit`.
6. Создайте лист `Products` и первую строку:

   ```text
   created_at | telegram_message_id | category | price_rub | rub_byn_rate | base_price_byn | markup_percent | final_price_byn | drive_file_id | drive_url | status
   ```

7. Скопируйте ID нужной папки Google Drive — последнюю часть её URL. OAuth работает от имени
   вошедшего пользователя, поэтому у этого аккаунта должен быть доступ на запись в папку и таблицу.
   Бот не делает файл или папку публичными.
8. При первом разрешённом запуске откроется браузер. После согласия token будет сохранён как
   `credentials/google-oauth-token.json`; последующие запуски используют и автоматически обновляют
   его. Оба JSON-файла являются секретными и не должны попадать в Git.

Первую авторизацию можно выполнить отдельно от Telegram (только после явного разрешения):

```powershell
python -m app.google_auth
```

После авторизации выполните безопасную настройку Drive и проверку Sheets:

```powershell
python -m app.google_setup
```

Команда использует минимальный scope `drive.file`. Если `GOOGLE_DRIVE_FOLDER_ID` пуст, она сначала
ищет ранее созданную приложением папку `Telegram Price Bot Photos`, а при её отсутствии создаёт
папку через Drive API и выводит ID. `.env` автоматически не изменяется: скопируйте ID вручную.
Если ID уже задан, команда только проверяет, что он доступен и указывает на папку. Затем она читает
метаданные указанной Spreadsheet и проверяет наличие листа `GOOGLE_SHEETS_WORKSHEET`. Фотографии и
строки при setup не создаются.

## Контролируемый Google write smoke-test

После успешных `app.google_auth` и `app.google_setup` можно вручную выполнить ровно одну тестовую
загрузку и одну запись, без Telegram и НБРБ:

```powershell
python -m app.google_smoke_write test-photo.jpg
```

Команда принимает JPG/JPEG/PNG, загружает один файл `smoke-test-<timestamp>.<ext>` и добавляет одну
строку со статусом `TEST` и фиксированной ценой 35 BYN. Тестовые данные автоматически не удаляются.
Если загрузка Drive успешна, но Sheets недоступен, файл остаётся в Drive, а CLI явно сообщает о
частичном результате.

## Раздельная маршрутизация сети

`TELEGRAM_PROXY_URL` задаёт HTTP proxy только для Telegram Bot API. При пустом значении Telegram
подключается напрямую. `CurrencyService` всегда создаёт `httpx.AsyncClient(trust_env=False)`, поэтому
НБРБ игнорирует Windows System Proxy и переменные `HTTP_PROXY`/`HTTPS_PROXY`. Google использует
собственную существующую OAuth-конфигурацию без изменений.

Безопасная диагностика `getMe` и курса RUB (без Google write operations):

```powershell
python -m app.network_check
```

Не создавайте таблицу автоматически и не коммитьте JSON-ключ.

## Установка и локальный запуск

В каталоге проекта:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Заполните `.env`:

```dotenv
TELEGRAM_BOT_TOKEN=токен_от_BotFather
ALLOWED_TELEGRAM_USER_ID=123456789
GOOGLE_OAUTH_CLIENT_FILE=credentials/google-oauth-client.json
GOOGLE_OAUTH_TOKEN_FILE=credentials/google-oauth-token.json
GOOGLE_DRIVE_FOLDER_ID=id_папки
GOOGLE_SHEETS_SPREADSHEET_ID=id_таблицы
GOOGLE_SHEETS_WORKSHEET=Products
MARKUP_PERCENT=0
FIXED_MARKUP_BYN=0
PRICE_ROUNDING=1
LOG_LEVEL=INFO
```

Запуск через long polling:

```powershell
python -m app.main
```

Telegram присылает несколько размеров фото; бот скачивает самый большой доступный вариант.

## Формула цены

Формула находится только в `app/services/price_calculator.py`:

```text
base_byn = price_rub * rub_to_byn_rate
final_byn = base_byn * (1 + MARKUP_PERCENT / 100) + FIXED_MARKUP_BYN
```

Затем результат округляется до ближайшего шага `PRICE_ROUNDING` по правилу `ROUND_HALF_UP`.
Например, `1` означает целый BYN, `0.01` — копейки, `5` — шаг в 5 BYN. Для изменения бизнес-
формулы достаточно заменить метод `PriceCalculator.calculate` и его тесты.

## Тесты и линтер

Тесты полностью offline: Telegram, НБРБ и Google не вызываются.

```powershell
python -m pytest
python -m ruff check .
```

## Развёртывание на PythonAnywhere

На бесплатном PythonAnywhere нельзя надёжно держать бесконечный long polling: Always-on tasks
доступны платным планам, а новые бесплатные аккаунты также не имеют ежедневной scheduled task.
Поэтому для free-tier предусмотрена WSGI-точка `app.webhook:application`. Бесплатное web app
нужно периодически продлевать в панели PythonAnywhere; кроме того, его исходящий интернет
ограничен allowlist. До выбора этой площадки проверьте, доступны ли из консоли домены
`api.telegram.org`, `api.nbrb.by`, `www.googleapis.com` и `oauth2.googleapis.com`. Если хотя бы один
не разрешён, запросите добавление официального API в allowlist или используйте другой хостинг/
платный аккаунт. Long polling остаётся рекомендуемым гарантированным локальным режимом.

Порядок настройки webhook:

1. Загрузите проект, создайте virtualenv, установите `requirements.txt`, добавьте `.env` и JSON.
2. На вкладке **Web** создайте manual web app с Python 3.12 (или новейшей доступной версией),
   укажите virtualenv и замените содержимое WSGI-файла на:

   ```python
   import sys
   sys.path.insert(0, "/home/USERNAME/telegram-price-bot")
   from app.webhook import application
   ```

3. Создайте случайный секрет без пробелов, запишите его в `WEBHOOK_SECRET` и перезагрузите web app.
4. Один раз зарегистрируйте HTTPS webhook (не публикуйте токен и секрет в истории shell):

   ```text
   https://api.telegram.org/bot<ТОКЕН>/setWebhook?url=https://USERNAME.pythonanywhere.com/&secret_token=<WEBHOOK_SECRET>
   ```

   Безопаснее выполнить эквивалентный POST из локального HTTP-клиента, передав значения через
   переменные окружения. Для EU-аккаунта домен имеет вид `USERNAME.eu.pythonanywhere.com`.

Webhook проверяет заголовок `X-Telegram-Bot-Api-Secret-Token`. Сетевой reverse proxy уже
завершает HTTPS. Не запускайте одновременно polling и webhook для одного токена. Для платного
PythonAnywhere вместо webhook можно создать Always-on task с `python -m app.main`.

## Ошибки и безопасность

Пользователь получает короткое понятное сообщение, а технические детали пишутся в лог без токенов
и credentials. При сбое курса запись и загрузка не начинаются; при сбое Drive таблица не меняется.
Если Drive уже принял файл, но Sheets недоступен, бот сообщает о частичном результате — файл нужно
проверить вручную. Полностью атомарной транзакции между независимыми Google API нет.
