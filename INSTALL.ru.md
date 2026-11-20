# Установка gamedev-studio с нуля (Windows)

Руководство для человека на чистом Windows 10 или 11 и для Claude, которому сказали «установи по этому руководству». Каждый шаг помечен:

- **[Claude]** — Claude Code делает сам;
- **[вы]** — делает человек: вход в учётные записи, окна Windows, перезапуск;
- **[Claude → вы]** — Claude выполняет, но сначала спрашивает ваше «да», а Windows может показать окно подтверждения.

English version: [INSTALL.md](INSTALL.md).

**Коротко:** получить zip от владельца → поставить Claude Code → распаковать архив → Claude ставит Git и Python, если их нет → Claude ставит плагин → проверка. Доступ к GitHub не нужен.

## Для владельца: перед передачей

1. **Скачайте архив.** Страница [Releases](https://github.com/ZMSkif/GameDev-AGI-Studio/releases), версия 0.4.1 или новее, раздел Assets, файл `gamedev-studio-0.4.1.zip`. Или одной командой:
   ```powershell
   gh release download v0.4.1 -R ZMSkif/GameDev-AGI-Studio -p "gamedev-studio-*.zip"
   ```
   Берите именно этот файл, а не «Source code (zip)»: в нём одна папка `gamedev-studio`, как ждёт руководство. В архивах 0.4.0 и старше нет ни этого руководства, ни скрипта проверки.
2. **Отправьте человеку** этот zip и файл `INSTALL.ru.md`. Руководство лежит и внутри архива. Ссылка на него в GitHub откроется только у того, у кого есть доступ к репозиторию.
3. **Доступ к GitHub давать не нужно.** Если хотите, чтобы человек сам скачивал новые версии, пригласите его: репозиторий → Settings → Collaborators → Add people. Учтите правило GitHub: в закрытом репозитории личной учётной записи приглашённый всегда получает право записи. Он сможет менять код и решения и выпускать релизы, поэтому приглашайте только тех, кому доверяете.

## Как это проверено

На ПК владельца ничего не устанавливалось. Настоящая установка прошла 20.11.2026 на чистой виртуальной машине GitHub Actions: Windows Server 2025, образ `windows-latest`, workflow «Clean install on Windows». Что там прошло:

- архив собран так же, как архив релиза, и распакован Windows PowerShell 5.1 в `C:\Tools`; в нём есть это руководство, скрипт проверки и правила студии;
- Claude Code 2.1.329 поставлен официальным установщиком; он сам предупредил, что папки `.local\bin` нет в PATH, поэтому в шаге 1 есть пункт про PATH;
- `claude plugin validate` прошёл;
- `claude plugin marketplace add` и `claude plugin install` прошли, `claude plugin list` показал плагин 0.4.1, включённый и прочитанный из `C:\Tools\gamedev-studio`; в плагине 17 навыков, 7 команд, 14 ролей агентов и 2 hooks;
- `python scripts/doctor.py`: все обязательные пункты ✅, у плагина «установлен из этой папки и включён»;
- с урезанным PATH скрипт показал ❌ и исправления для Claude Code, Git и Python;
- обновление заменой папки, как в разделе «Обновление»: без переустановки `claude plugin list` сразу показал версию из новой папки;
- память Hindsight по разделу «Память Hindsight» установилась и ответила на проверку.

Что там не проверить:

- на машине GitHub уже есть Git и Python, поэтому шаги 3 и 4 (winget) не выполнялись;
- вход в Claude и работа плагина в настоящей сессии, включая hooks и шаг 8: на машине GitHub никто не входит в Claude;
- домашние Windows 10 и 11: машина GitHub работает на Windows Server 2025;
- Codex.

## Шаг 0. Что нужно

- **Windows** 10 версии 1809 или новее либо Windows 11; x64 или ARM64; 4 ГБ памяти или больше; интернет.
- **Платная подписка Claude**, например Pro или Max. Аккаунт Console (оплата API) не подходит: студия работает по подписке и не переходит на платный API.
- **Архив `gamedev-studio-<версия>.zip`** от владельца, версия 0.4.1 или новее.

## Шаг 1. [вы] Установить Claude Code и войти

1. Откройте **PowerShell** (обычный, права администратора не нужны) и выполните:
   ```powershell
   irm https://claude.ai/install.ps1 | iex
   ```
2. Закройте окно, откройте новое и проверьте: `claude --version`.
   - Если команда не найдена или установщик написал `...\.local\bin is not in your PATH`, значит, папки установки нет в PATH. Установщик кладёт программу в `%USERPROFILE%\.local\bin`, но в PATH её может не добавить. Добавьте эту папку в PATH пользователя: Параметры → Система → О системе → Дополнительные параметры системы → Переменные среды → в верхнем списке `Path` → Изменить → Создать → `%USERPROFILE%\.local\bin` → ОК. Затем откройте новое окно PowerShell.
3. Запустите `claude`. На вопрос о способе входа выберите аккаунт Claude с подпиской, а не Console. Войдите через браузер. Если браузер не открылся, нажмите `c`, чтобы скопировать ссылку, откройте её сами и вставьте код обратно в терминал. Затем выйдите командой `/exit`.

Другой способ: `winget install Anthropic.ClaudeCode`. Такая установка не обновляется сама, а `claude update` для неё ничего не делает. Обновлять нужно так: `winget upgrade Anthropic.ClaudeCode`.

## Шаг 2. [вы] Распаковать архив и запустить Claude в папке плагина

```powershell
New-Item -ItemType Directory -Force C:\Tools | Out-Null
Expand-Archive -Path "$HOME\Downloads\gamedev-studio-0.4.1.zip" -DestinationPath C:\Tools
cd C:\Tools\gamedev-studio
claude
```

- Если архив называется иначе или лежит в другой папке, поправьте путь в `Expand-Archive`.
- Внутри архива одна папка `gamedev-studio`, это и есть **папка плагина**. Проверка: в ней есть файл `.claude-plugin\marketplace.json`.
- Плагин загружается прямо из этой папки, поэтому не удаляйте и не переносите её после установки. Эта папка только для установки и обновления: игры в ней не делайте, при обновлении она заменяется целиком (шаг 8 — где делать игры).
- Claude Code спросит, доверяете ли вы этой папке. Ответьте «да».

Теперь скажите Claude: «Установи плагин по INSTALL.ru.md, шаги 3–7».

> **Для Claude:** файл `AGENTS.md` в этой папке — правила для тех, кто развивает саму студию в её репозитории (GitHub Issues, проекты, pull request). К установке по этому руководству они не относятся: не запускай `gh` и ничего не создавай в GitHub.

## Шаг 3. [Claude] Посмотреть, что уже установлено

В PowerShell, ничего не устанавливая:

```powershell
$env:PYTHON_MANAGER_AUTOMATIC_INSTALL = "false"
Get-Command git, python, py -ErrorAction SilentlyContinue | Format-Table Name, Source
git --version
python --version
py -3 --version
```

Первая строка не даёт Python install manager поставить Python сам при проверке. В шаге 4 ставится только недостающее:

- **Git** — если `git` не найден.
- **Python** — если ни `python`, ни `py -3` не показали версию 3.10 или новее. Если `python` лежит в папке `...\WindowsApps\` и пишет про Microsoft Store, это заглушка, а не Python.

## Шаг 4. [Claude → вы] Установить недостающее

Claude показывает команды и спрашивает ваше «да». Оно означает и согласие с условиями источника и пакетов winget, поэтому в командах стоят флаги `--accept-source-agreements` и `--accept-package-agreements`. Установка может показать окно Windows «Разрешить этому приложению вносить изменения?», его подтверждаете вы.

```powershell
winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements
winget install --id Python.Python.3.13 -e --source winget --accept-source-agreements --accept-package-agreements
```

- **Если команды `winget` нет**, установите «Установщик приложений» (App Installer) из Microsoft Store. Это делаете вы.
- **Пакет `Git.Git`** ведёт сообщество winget, а не проект Git for Windows. Официальный установщик: <https://git-scm.com/install/windows>.
- **[вы] Перезапустите Claude Code после установки**, иначе он не увидит новые программы. Закройте окно, откройте новое окно PowerShell и выполните:
  ```powershell
  cd C:\Tools\gamedev-studio
  claude --continue
  ```
  `claude --continue` продолжает последний разговор **в текущей папке**, поэтому сначала нужен `cd`.

## Шаг 5. [Claude] Проверка компьютера

В папке плагина:

```powershell
python scripts/doctor.py
```

Если `python` не найден, а `py` есть: `py -3 scripts/doctor.py`.

По каждому пункту скрипт печатает ✅ или ❌, а для ❌ — как исправить и кто это делает. Пункт «Плагин» до шага 6 будет ❌, это нормально. Вывод на английском: `--lang en`, для Claude в JSON: `--json`.

Скрипт ничего не устанавливает и не меняет:

- он запускает только проверки версий: `claude --version`, `git --version`, `bash --version` и одну строку Python, которая печатает версию;
- автоматическую установку Python при этом он отключает;
- он читает файлы со списком плагинов Claude Code;
- Codex он не запускает, а только ищет в PATH;
- сам скрипт не пишет ни одного файла.

## Шаг 6. [Claude] Установить плагин

```powershell
claude plugin marketplace add "C:\Tools\gamedev-studio"
claude plugin install gamedev-studio@gamedev-studio
```

**[вы]** Перезапустите Claude Code так же, как в шаге 4: новое окно, `cd C:\Tools\gamedev-studio`, `claude --continue`.

**Codex (по желанию)**, если он у вас уже установлен:

```powershell
codex plugin marketplace add "C:\Tools\gamedev-studio"
codex plugin add gamedev-studio@gamedev-studio
```

## Шаг 7. Итоговая проверка

1. **[Claude]** `python scripts/doctor.py`: все обязательные пункты ✅, у плагина написано «установлен из этой папки и включён».
2. **[вы]** Откройте новую сессию Claude Code и спросите «какие навыки есть в плагине gamedev-studio?». В ответе должны быть `studio-rules`, `engine-profiles`, `memory` и другие.

Плагин установлен.

## Шаг 8. [вы] Своя игра — в своей папке

Каждую игру делайте в отдельной папке **вне** папки плагина, например `C:\Games\<название>`:

```powershell
New-Item -ItemType Directory -Force C:\Games\my-game | Out-Null
cd C:\Games\my-game
git init -b main
New-Item -ItemType File .gamedev-studio | Out-Null
claude
```

- Файл `.gamedev-studio` помечает папку как игру студии. Только в такой папке работают проверки плагина (hooks): напоминание о правилах при запуске, запрет коммитов прямо в `main` (кроме самого первого коммита в пустой репозиторий) и запрет коммитить пароли и ключи.
- В Claude начните игру командой `/gamedev-studio:new-web-game "Название"`. Claude проведёт интервью с вариантами ответов и ничего не создаёт и не скачивает без вашего «да».
- **Задачи игры** студия ведёт в GitHub Issues репозитория самой игры (DEC-002), а не в файлах. Для этого нужен ваш собственный бесплатный аккаунт GitHub и GitHub CLI: `winget install --id GitHub.cli -e --source winget --accept-source-agreements --accept-package-agreements`, затем `gh auth login` в отдельном окне PowerShell. Это ваш аккаунт, доступ к репозиторию студии он не даёт и не требует. Без него Claude скажет, что задачи вести негде, и спросит вас.

## Без доступа к репозиторию студии (обычный случай)

Работает всё, что нужно для игр:

- навыки, роли агентов и команды `/gamedev-studio:…`;
- проверки hooks в папке игры с файлом `.gamedev-studio` (шаг 8);
- правила студии: они в навыках плагина и в папках `contracts/v1/` и `reference/` внутри папки плагина.

Чего нет: полного списка решений владельца. Он хранится в GitHub Issues закрытого репозитория студии. Claude один раз скажет, что список недоступен, и будет работать по правилам плагина. Если понадобится решение, которого в плагине нет, Claude спросит вас, а не будет додумывать. Тогда спросите владельца.

Если GitHub CLI не установлен или вход не выполнен, при запуске Claude Code в папке игры появится предупреждение `GameDev Studio tool preflight FAILED`. Оно значит, что остановятся только задачи, которым нужен GitHub, например задачи игры (шаг 8); остальная работа идёт. Просить доступ к репозиторию студии не нужно.

## Обновление

1. **[вы]** Получите от владельца новый архив.
2. **[вы]** Закройте все окна Claude Code: Windows не даст переименовать папку, открытую в программе.
3. **[вы]** В PowerShell:
   ```powershell
   Rename-Item C:\Tools\gamedev-studio gamedev-studio-old
   Expand-Archive -Path "$HOME\Downloads\gamedev-studio-0.4.2.zip" -DestinationPath C:\Tools
   ```
   Если `gamedev-studio-old` уже есть от прошлого обновления, сначала удалите её.
4. **[вы]** Запустите Claude Code в папке плагина: `cd C:\Tools\gamedev-studio`, затем `claude`. Переустанавливать плагин не нужно: он загружается из этой папки, а по документации Claude Code изменения в ней действуют со следующего запуска.
5. **[Claude]** `python scripts/doctor.py` показывает новую версию. Когда всё работает, удалите `C:\Tools\gamedev-studio-old` сами.

Проверено на чистой машине GitHub: после замены папки `claude plugin list` без переустановки показал версию из новой папки, а `python scripts/doctor.py` — «установлен из этой папки и включён». Настоящая сессия после обновления там не запускалась, а обновление для Codex не проверялось. Игры в `C:\Games` обновление не затрагивает.

## Память Hindsight (по желанию, только по решению владельца)

Плагин работает без памяти. Где и как работает память студии, решает владелец, поэтому эти шаги делайте, только если он сам скажет.

> **Проверено на чистой машине GitHub Actions** (Windows Server 2025, Python 3.12.10). Команды шагов 1–3 прошли:
> - установка заняла около 5 минут и 2,2 ГБ;
> - сервер сам поднял свою базу данных, скачал модели и через 52 секунды ответил `healthy`, база подключена;
> - `doctor.py --hindsight` показал ✅.
>
> Извлечение фактов там не проверялось: на той машине нет входа в Claude. На ПК владельца сервер работает на Python 3.11.9 с `hindsight-api` 1.2.2.

1. **[Claude → вы]** Установка, около 2 ГБ, после вашего «да». Нужен Python 3.11 или новее:
   ```powershell
   python -m venv "$HOME\.hindsight-runtime"
   & "$HOME\.hindsight-runtime\Scripts\python.exe" -m pip install hindsight-api==1.2.2
   ```
2. **[вы] Запуск в отдельном окне PowerShell.** Сервер работает, пока окно открыто, и только на этом ПК (127.0.0.1). Факты он извлекает через вашу подписку Claude: провайдер `claude-code` описан для подписок Pro и Max. Платный API не нужен, но Claude Code должен быть установлен и с выполненным входом.
   ```powershell
   $env:HINDSIGHT_API_LLM_PROVIDER = "claude-code"
   $env:HINDSIGHT_API_HOST = "127.0.0.1"
   $env:HINDSIGHT_API_PORT = "8888"
   $env:HINDSIGHT_API_MODEL_INIT_TIMEOUT = "900"
   $env:HINDSIGHT_API_MCP_ENABLED_TOOLS = "retain,recall,list_memories,get_memory,get_bank"
   & "$HOME\.hindsight-runtime\Scripts\hindsight-api.exe" --host 127.0.0.1 --port 8888
   ```
   При первом запуске скачиваются модели поиска с Hugging Face: `BAAI/bge-small-en-v1.5` и `hindsight-ai/hs-rerank-1`. Это может занять несколько минут.
3. **[Claude]** Проверка: `python scripts/doctor.py --hindsight`.
4. **Подключение к игре** описано в навыке `memory`, раздел 2.

Удалять память может только владелец студии. Предупреждение: REST-маршруты DELETE сервера Hindsight открыты без авторизации, и от них агентов удерживает только правило в навыке `memory`.

## Если что-то не так

- **`claude` не найден:** откройте новое окно; если не помогло, добавьте папку в PATH, как описано в шаге 1.
- **`python` пишет про Microsoft Store:** Параметры → Приложения → Дополнительные параметры приложений → Псевдонимы выполнения приложений, отключите «python.exe» и «python3.exe». Если вы ставили Python install manager, его псевдонимы не трогайте.
- **Claude Code не находит Git Bash:** укажите путь к `bash.exe` в переменной `CLAUDE_CODE_GIT_BASH_PATH` в разделе `env` файла `settings.json` Claude Code. Пример: `C:\Program Files\Git\bin\bash.exe`.
- **Любой другой ❌:** `python scripts/doctor.py` печатает, как исправить.
