# Быстрый старт

Это руководство поможет вам установить SILO, создать ваш первый навык ИИ, протестировать его и запустить.

## 1. Установка

Вы можете установить SILO с помощью `pip` или `uv`. Мы настоятельно рекомендуем использовать `uv`, так как навыки SILO спроектированы как автономные скрипты с инлайновыми зависимостями (PEP 723).

```bash
pip install -e .
```
*(предполагается, что вы устанавливаете фреймворк локально)*

Чтобы проверить готовность системы, запустите команду doctor:

```bash
silo doctor
```

Она проверит версию Python, наличие `uv` и работу системной связки ключей.

## 2. Создание первого навыка

SILO предоставляет CLI для мгновенного создания шаблонов. Давайте создадим навык для работы с GitHub. Мы знаем, что ему понадобится `GITHUB_TOKEN`.

```bash
silo init github_skill.py --secrets GITHUB_TOKEN
```

Это создаст файл `github_skill.py`. Откройте его в редакторе:

```python title="github_skill.py"
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "silo",
# ]
# ///

from typing import Optional
from pydantic import BaseModel, Field
from silo import Skill, Secret, JSONResponse

app = Skill(name="My Skill", description="A new SILO skill.")

@app.command()
def do_something(param: str):
    """Делает что-то крутое."""
    token = Secret.require("GITHUB_TOKEN")
    return JSONResponse({"status": "success", "param": param})

if __name__ == "__main__":
    app.run()
```

Обратите внимание на верхнюю секцию: блок `/// script` говорит `uv`, какие зависимости нужны этому файлу. Вы можете запустить этот файл где угодно, не создавая venv вручную.

## 3. Запуск навыка

Вы можете запустить стандартное выполнение через `uv`:

```bash
uv run github_skill.py do_something --param hello
```

**Что произойдет?**
Так как скрипт требует `GITHUB_TOKEN`, SILO поищет его в переменных окружения или Keychain.
Если ключ не найден и вы запустили скрипт интерактивно, SILO откроет вкладку в браузере с защищенной формой ввода. Введенный ключ сохранится в Keychain системы для будущего использования.

## 4. Тестирование для агентов (`silo test`)

LLM-агент работает в "headless" среде (без терминала и браузера). Важно, чтобы навык вел себя предсказуемо и не зависал в ожидании ввода.

Используйте `silo test` для симуляции работы агента:

```bash
silo test github_skill.py do_something --param agent_test
```

`silo test` проверяет, что:
1. Скрипт корректно генерирует манифест (`SKILL.md`).
2. Механизмы авторизации возвращают JSON-ошибки вместо того, чтобы вешать выполнение.
3. Вывод является чистым и валидным JSON или Markdown.
