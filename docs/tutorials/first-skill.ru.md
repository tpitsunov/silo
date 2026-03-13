# Руководство: Ваш первый скилл

Это руководство проведет вас через процесс создания, установки и запуска простого скилла SILO, который получает случайную цитату из API.

## 1. Инициализация скилла

Используйте CLI SILO для создания заготовки проекта. Мы назовем его `quote-master`.

```bash
silo init quote-master
```

Это создаст директорию `quote-master/` с файлом `skill.py`, готовым для вашей логики.

## 2. Определение инструментов

Откройте `quote-master/skill.py` и замените его содержимое следующим кодом:

```python
import requests
from silo.skill import Skill
from silo.types import AgentResponse

skill = Skill(namespace="quotes")

@skill.tool(require_approval=False)
def get_random_quote():
    """Получает случайную вдохновляющую цитату."""
    response = requests.get("https://dummyjson.com/quotes/random")
    data = response.json()
    return AgentResponse(
        llm_text=f"'{data['quote']}' — {data['author']}",
        raw_data=data
    )

if __name__ == "__main__":
    skill.run()
```

## 3. Установка скилла

Сообщите хабу SILO о вашем новом скилле. Это зарегистрирует пространство имен и подготовит песочницу.

```bash
silo install ./quote-master
```

## 4. Ручной запуск

Протестируйте ваш инструмент напрямую из терминала. Обратите внимание, как SILO использует пространство имен, которое вы определили в коде.

```bash
silo run quotes get_random_quote
```
```text title="Симуляция вывода"
⠋ Executing quotes:get_random_quote...
╭────────────────────────────── Execution Result ───────────────────────────────╮
│ 'Life is 10% what happens to you and 90% how you react to it.' — Charles R.  │
│ Swindoll                                                                     │
╰──────────────────────────────────────────────────────────────────────────────╯
```

Проверьте установленные скиллы, чтобы увидеть `quotes` в списке вместе с его весом.
```bash
silo ps
```
```text title="Симуляция вывода"
                              Installed SILO Skills
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Namespace   ┃ Size (Src) ┃ Size (Env) ┃ Last Used                          ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ quotes      │     2.1 KB │    42.1 MB │ 2024-03-13 18:45                   │
└─────────────┴────────────┴────────────┴────────────────────────────────────┘
```

## 6. Инспекция инструментов

Чтобы точно увидеть, какие инструменты предоставляет скилл, и прочитать его инструкции, используйте:
```bash
silo inspect quotes
```
```text title="Симуляция вывода"
⠋ Inspecting quotes...
╭─────────────────────────── Skill: quotes (Instructions) ─────────────────────────────╮
│ Describe the philosophical purpose and usage of this skill here.                    │
│ The Agent will read this to understand how to use the tools.                        │
╰──────────────────────────────────────────────────────────────────────────────────────╯
                                   Available Tools
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Tool Name        ┃ Description                                          ┃ Approvals ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ get_random_quote │ Получает случайную вдохновляющую цитату.              │   Auto    │
└──────────────────┴──────────────────────────────────────────────────────┴───────────┘
```

---

**Следующий шаг:** Узнайте, как работать с [Секретными API-ключами](../guide/security.ru.md).
