DEPLOYMENT — PizzaMania
========================

Краткое руководство: как подготовить проект к проду и задеплоить на PythonAnywhere (MySQL-только в бесплатном тарифе).

1) Что мы сделали в проекте
- `PizzaMania/settings.py`: теперь читает конфигурацию из переменных окружения (`DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `MYSQL_*` и т.д.).
- `requirements.txt`: добавлены `mysqlclient` и `python-dotenv`.
- Добавлен `.env.example` с примерами переменных.
- Обновлён `.gitignore`.

2) Локальная подготовка (перед пушем на GitHub)
- Скопируйте `.env.example` в `.env` и отредактируйте значения для локальной разработки:

  ```bash
  cp .env.example .env
  # Редактируйте .env (например через nano или VSCode)
  ```

- Установите зависимости (лучше в виртуальном окружении):

  ```bash
  python -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

- Для локальной разработки оставьте `USE_MYSQL=0` (или пусто) — будет использоваться `db.sqlite3`.
- Примените миграции и создайте суперпользователя:

  ```bash
  python manage.py migrate
  python manage.py createsuperuser
  ```

- Запустите локально:

  ```bash
  python manage.py runserver
  ```

3) Публикация на GitHub
- Убедитесь, что `.env` не добавлен в git (в `.gitignore`).
- Добавьте, закоммитьте и запушьте репозиторий:

  ```bash
  git add .
  git commit -m "Prepare for production: env-based settings, MySQL support"
  git push origin <branch>
  ```

4) Развёртывание на PythonAnywhere (пошагово)

- Зарегистрируйтесь / войдите на https://www.pythonanywhere.com/
- Создайте новый Web App (в панели `Web`) — выберите "Manual configuration" и версию Python, которая совпадает с вашей локальной (например 3.11).
- В разделе `Consoles` откройте Bash и клонируйте ваш репозиторий:

  ```bash
  git clone https://github.com/<your-username>/<your-repo>.git
  cd <your-repo>
  python -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

- Настройка MySQL на PythonAnywhere:
  - В бесплатном аккаунте PythonAnywhere предоставляет MySQL-сервер для вашего аккаунта (создаётся база через вкладку `Databases`).
  - В панели `Databases` создайте базу — система покажет имя базы, пользователя и хост (обычно `yourusername$yourdbname` и `yourusername.mysql.pythonanywhere-services.com`).
  - Скопируйте эти значения.

- Задайте переменные окружения в PythonAnywhere: открыв вкладку `Web` → `Environment variables`, добавьте:
  - `DJANGO_SECRET_KEY` = (ваш секретный ключ)
  - `DJANGO_DEBUG` = False
  - `DJANGO_ALLOWED_HOSTS` = yourusername.pythonanywhere.com
  - `USE_MYSQL` = 1
  - `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_HOST`, `MYSQL_PORT` — значения, показанные в панели `Databases` (MYSQL_PORT обычно 3306)

- Выполните миграции и соберите статические файлы в консоли (Bash) на PythonAnywhere:

  ```bash
  source venv/bin/activate
  cd /home/yourusername/<your-repo>
  python manage.py migrate --noinput
  python manage.py collectstatic --noinput
  ```

- Настройка WSGI (вкладка `Web`):
  - Укажите путь к виртуальному окружению (`/home/yourusername/<your-repo>/venv`) и к файлу проекта (путь до `PizzaMania` directory).
  - Отредактируйте WSGI-конфиг, если нужно, чтобы указать `sys.path` на ваш проект.

- В `Web` → `Static files` добавьте правило для `URL /static/` → `Directory /home/yourusername/<your-repo>/staticfiles`.
- Нажмите кнопку `Reload` в панели `Web`.
- Проверьте сайт по адресу `https://yourusername.pythonanywhere.com`.

5) Полезные заметки
- Никогда не храните реальные секреты (пароли, SECRET_KEY) в git — используйте переменные окружения.
- Если возникнут проблемы с `mysqlclient` на PythonAnywhere, обычно достаточно установить пакет в виртуальном окружении (мы добавили в `requirements.txt`).
- Для CI/CD можно добавить workflow, который автоматически собирает и тестирует проект перед пушем (опционально).

6) Если секретный ключ (или другие секреты) уже попали в git-history

- Ситуация: вы обнаружили настоящий `SECRET_KEY` в репозитории (в коммите). Проблема в том, что ключ остаётся в истории — его нужно поменять и удалить из истории репозитория.

- Шаги для безопасного восстановления:
  1. Сгенерируйте новый секретный ключ локально:

    ```bash
    python - <<'PY'
from secrets import token_urlsafe
print(token_urlsafe(50))
PY
    ```

  2. Установите `DJANGO_SECRET_KEY` в окружении на проде (PythonAnywhere → `Web` → `Environment variables`) и в других местах, где проект работает.

  3. (Опционально, но рекомендовано) Удалите старый ключ из истории git. Для этого используйте `git filter-repo` или BFG (пример с BFG):

    ```bash
    # Установите BFG (https://rtyley.github.io/bfg-repo-cleaner/)
    # Пример использования BFG для удаления строки/файла с секретом
    bfg --replace-text passwords.txt

    # С помощью git-filter-repo (более гибкий):
    git clone --mirror https://github.com/<your-username>/<your-repo>.git
    cd <your-repo>.git
    # Потом используем git filter-repo с правилом, удаляющим секреты (пример в документации)
    git filter-repo --path-glob 'path/to/file/with/secret' --invert-paths

    # После редактирования истории — force-push в репозиторий:
    git push --force
    ```

  4. Сообщите коллегам, что история переписана — всем нужно будет заново клонировать репозиторий.

  5. Если секреты могли быть использованы злоумышленниками, смените связанные пароли/ключи (например, пароль БД).

Примечание: переписывание истории — радикальная мера; если вы не уверены, помогу составить безопасный план и выполню необходимые команды с инструкциями.

Если хотите — могу добавить пример `.github/workflows` для автоматической проверки тестов перед пушем.
