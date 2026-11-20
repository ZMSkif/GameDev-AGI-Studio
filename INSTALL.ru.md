# Установка gamedev-studio с нуля (Windows)

Руководство для человека на чистом Windows 10 или 11 и для Claude, которому сказали «установи по этому руководству». Каждый шаг помечен:

- **[Claude]** — Claude Code может сделать сам;
- **[вы]** — делает человек: вход в учётные записи, окна Windows, письма с приглашениями;
- **[Claude → вы]** — Claude выполняет, но сначала спрашивает вас, а Windows может показать окно подтверждения.

English version: [INSTALL.md](INSTALL.md).

> **Как проверено это руководство.** Установка на чистую машину не проводилась: владелец попросил ничего не ставить на свой ПК, чтобы не создавать дубли. Проверено вот что:
> - скрипт проверки `scripts/doctor.py` запускался на ПК владельца (только чтение) и в окружении, похожем на чистый ПК (пустой PATH): он нашёл каждый недостающий пункт и показал исправление;
> - архив релиза: в нём есть всё, что нужно руководству, и `claude plugin validate` проходит на распакованной копии;
> - команды и требования сверены с документацией Claude Code, Git for Windows, GitHub CLI и Python.
>
> Настоящая проверка на чистой системе — Windows Sandbox. Включить её может только владелец ПК.

## Шаг 0. Что нужно заранее

- **Windows:** 10 версии 1809 или новее, или Windows 11; x64 или ARM64; 4 ГБ памяти или больше.
- **Аккаунт Claude:** Pro, Max, Team, Enterprise или Console. Бесплатного плана claude.ai недостаточно.
- **Архив плагина (zip)**, один из двух вариантов:
  - архив, который прислал владелец (ZMSkif);
  - исходный архив релиза: <https://github.com/ZMSkif/GameDev-AGI-Studio/releases>, нужная версия, «Source code (zip)». Репозиторий закрытый, поэтому скачать его можно только с доступом (шаг 6).
- **Учётная запись GitHub:** нужна, чтобы плагин читал решения студии. Без неё плагин работает, но с ограничениями (раздел «Без доступа к GitHub»).

## Шаг 1. [вы] Установить Claude Code и войти

1. Откройте **PowerShell** (обычный, права администратора не нужны) и выполните:
   ```powershell
   irm https://claude.ai/install.ps1 | iex
   ```
2. Закройте окно, откройте новое и проверьте: `claude --version`.
3. Запустите `claude` и войдите через браузер. Если браузер не открылся, нажмите `c`, чтобы скопировать ссылку, откройте её сами и вставьте код обратно в терминал.

Вариант: `winget install Anthropic.ClaudeCode`. Он не обновляется сам, поэтому `claude update` придётся запускать вручную.

## Шаг 2. [Claude] Распаковать архив в постоянную папку

Плагин загружается прямо из этой папки, поэтому не кладите её в «Загрузки» или Temp и не удаляйте после установки.

```powershell
New-Item -ItemType Directory -Force C:\Tools | Out-Null
Expand-Archive -Path "$HOME\Downloads\GameDev-AGI-Studio-0.4.0.zip" -DestinationPath C:\Tools
```

Внутри `C:\Tools` появится папка вида `GameDev-AGI-Studio-0.4.0`. Дальше она называется **папкой плагина**. Проверка: в ней есть файл `.claude-plugin\marketplace.json`.

Теперь можно запустить Claude Code в папке плагина и дать ему задачу: «Установи плагин по INSTALL.ru.md, шаги 3–8».

## Шаг 3. [Claude → вы] Установить Git for Windows, Python и GitHub CLI

Claude показывает три команды и спрашивает ваше согласие. Ваше «да» означает и согласие с условиями источника winget: поэтому в командах стоят флаги `--accept-…`. Каждая установка может показать окно Windows «Разрешить этому приложению вносить изменения?», его подтверждаете вы.

```powershell
winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements
winget install --id Python.Python.3.13 -e --source winget --accept-source-agreements --accept-package-agreements
winget install --id GitHub.cli --source winget --accept-source-agreements --accept-package-agreements
```

- **Если команды `winget` нет**, установите «Установщик приложений» (App Installer) из Microsoft Store. Это делаете вы.
- **Пакет `Git.Git`** собирает не сам проект Git for Windows, а сообщество winget. Если нужен официальный установщик, он есть на <https://git-scm.com/install/windows>.
- **Python** можно поставить и через Python install manager с <https://www.python.org/downloads/>.
- **[вы] Перезапустите Claude Code после установки**: закройте терминал, откройте новый и выполните `claude --continue`. Без этого Claude не увидит новые программы.

## Шаг 4. [Claude] Проверка

В папке плагина:

```powershell
python scripts\doctor.py
```

Скрипт только читает: ничего не устанавливает, не меняет и не удаляет. По каждому пункту он печатает ✅ или ❌, для ❌ — как исправить и кто это делает. Вариант на английском: `python scripts\doctor.py --lang en`. Вывод для Claude в JSON: `--json`.

## Шаг 5. [вы] Войти в GitHub

`gh auth login` спрашивает в диалоге и открывает браузер. Поэтому запускайте его **сами, в отдельном окне PowerShell**, а не через Claude:

```powershell
gh auth login
```

Выберите GitHub.com, затем вход через браузер (Login with a web browser). Проверка: `gh auth status`.

## Шаг 6. [вы] Получить доступ к закрытому репозиторию

1. Напишите владельцу (ZMSkif) свой логин GitHub.
2. Он добавит вас в доступ к `ZMSkif/GameDev-AGI-Studio`.
3. Примите приглашение по ссылке из письма GitHub.
4. [Claude] Повторите проверку `python scripts\doctor.py`. Пункты «Доступ к репозиторию» и «Чтение решений» должны стать ✅.

## Шаг 7. [Claude] Установить плагин

Укажите путь к **своей** папке плагина:

```powershell
claude plugin marketplace add "C:\Tools\GameDev-AGI-Studio-0.4.0"
claude plugin install gamedev-studio@gamedev-studio
```

[вы] Перезапустите Claude Code (новый терминал, `claude --continue`). Проверка: `claude plugin list` показывает `gamedev-studio@gamedev-studio`.

**Codex (по желанию)**, если вы работаете в Codex:

```powershell
codex plugin marketplace add "C:\Tools\GameDev-AGI-Studio-0.4.0"
codex plugin add gamedev-studio@gamedev-studio
```

## Шаг 8. [Claude] Итоговая проверка

1. `python scripts\doctor.py`: все обязательные пункты ✅.
2. В новой сессии Claude Code спросите «какие навыки есть в плагине gamedev-studio?». В ответе должны быть `studio-rules`, `engine-profiles`, `memory` и другие.

## Без доступа к GitHub

Работает без GitHub:
- навыки;
- роли агентов;
- команды `/gamedev-studio:…`;
- проверки hooks. Им нужны только Git и Python, а предпроверка GitHub при отказе ничего не блокирует.

Не работает без GitHub:
- навык `studio-rules` требует читать решения студии из GitHub Issues (метка `decision`). Без доступа Claude их не увидит;
- исходный архив релиза не скачать.

**Обходной путь.** Владелец выгружает решения в файл и присылает его вместе с архивом:

```powershell
gh issue list -R ZMSkif/GameDev-AGI-Studio --label decision --state open --limit 1000 --json number,title,url,body > decisions.json
```

- Положите `decisions.json` в папку плагина. В начале работы скажите Claude: «решения студии лежат в decisions.json, читай их оттуда».
- Команда брифа принимает этот файл прямо: `--decisions decisions.json`.
- Файл устаревает: просите новый с каждым релизом.

## Обновление

1. Получите новый архив.
2. Распакуйте его рядом, в новую папку с номером версии.
3. Поставьте плагин из новой папки (шаг 7 с новым путём).
4. Перезапустите Claude Code.

Если папка плагина — клон git-репозитория, а не распакованный архив, обновление проще:

```powershell
claude plugin marketplace update gamedev-studio
claude plugin update gamedev-studio@gamedev-studio
```

## Память Hindsight (по желанию)

Плагин работает и без памяти. Память включается отдельно и только с согласия владельца студии: где будет работать сервер, решается в задаче [#150](https://github.com/ZMSkif/GameDev-AGI-Studio/issues/150).

> **Не проверено на чистой машине.** На ПК владельца сервер стоит так:
> - отдельное окружение (venv), созданное uv 0.13.1 на Python 3.11.9;
> - пакет `hindsight-api` 1.2.2;
> - около 1,8 ГБ.
>
> Команды ниже — стандартный путь через `venv` и `pip`; в таком виде они не проверялись.

1. **[Claude → вы]** Установка, около 2 ГБ, после вашего «да»:
   ```powershell
   python -m venv "$HOME\.hindsight-runtime"
   & "$HOME\.hindsight-runtime\Scripts\python.exe" -m pip install hindsight-api==1.2.2
   ```
2. **[Claude] Запуск.** Сервер работает только на этом ПК (127.0.0.1). Факты извлекаются через вашу подписку Claude: провайдер `claude-code`, платный API не нужен, но Claude Code должен быть установлен и с выполненным входом.
   ```powershell
   $env:HINDSIGHT_API_LLM_PROVIDER = "claude-code"
   $env:HINDSIGHT_API_HOST = "127.0.0.1"
   $env:HINDSIGHT_API_PORT = "8888"
   $env:HINDSIGHT_API_MODEL_INIT_TIMEOUT = "900"
   $env:HINDSIGHT_API_MCP_ENABLED_TOOLS = "retain,recall,list_memories,get_memory,get_bank"
   & "$HOME\.hindsight-runtime\Scripts\hindsight-api.exe" --host 127.0.0.1 --port 8888
   ```
   При первом запуске скачиваются модели поиска с Hugging Face (`BAAI/bge-small-en-v1.5` и `hindsight-ai/hs-rerank-1`). Это может занять несколько минут, поэтому таймаут поднят до 900 с.
3. **[Claude] Проверка:** `python scripts\doctor.py --hindsight`. Полный тест: `python scripts\hindsight_smoke.py --run <новый id>`. Он создаёт тестовые банки, а удаляет их только владелец.
4. **Подключение к игре** описано в навыке `memory`, раздел 2. Каждый шаг там — только с согласия владельца.

Предупреждение: REST-маршруты DELETE сервера Hindsight открыты без авторизации. От них агентов удерживает только правило в навыке `memory`.

## Если что-то не так

- **`claude` не найден** после установки: откройте новый терминал. Если не помогло, перезагрузите компьютер.
- **`python` открывает Microsoft Store:** Параметры → Приложения → Дополнительные параметры приложений → Псевдонимы выполнения приложений, отключите оба «python».
- **Claude Code не находит Git Bash:** укажите путь к `bash.exe` в переменной `CLAUDE_CODE_GIT_BASH_PATH` в разделе `env` файла `settings.json` Claude Code. Пример: `C:\Program Files\Git\bin\bash.exe`.
- **Для любого другого ❌** скрипт `python scripts\doctor.py` печатает исправление.
