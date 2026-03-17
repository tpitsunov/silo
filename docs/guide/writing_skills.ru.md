# Создание скиллов

Это руководство описывает основные концепции создания инструментов (tools) в SILO.

## Класс `Skill`

Скилл в SILO — это экземпляр класса `Skill`, который управляет всеми инструментами, парсингом аргументов, обработкой ошибок и сериализацией.

```python
from silo import Skill

skill = Skill(namespace="github")
```

## Создание инструментов (Tools)

Инструменты — это функции, декорированные с помощью `@skill.tool()`. SILO использует Pydantic (через `validate_call`) для автоматического определения аргументов, их типов и значений по умолчанию.

```python
@skill.tool()
def greet(name: str, shout: bool = False):
    """Приветствует пользователя по имени."""
    msg = f"Hello, {name}!"
    if shout:
        msg = msg.upper()
    return f"Результат: {msg}"
```

SILO автоматически сопоставляет сигнатуру функции с флагами CLI:
```bash
silo run github greet --name Alice --shout
```
```text title="Симуляция вывода"
⠋ Executing github:greet...
╭────────────────────────────── Execution Result ───────────────────────────────╮
│ Result: HELLO, ALICE!                                                        │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Использование Pydantic для сложных входных данных

LLM отлично справляются с написанием JSON. Если вашему инструменту требуется сложная структура (объект или список), используйте **Pydantic-модели** в качестве типов аргументов.

```python
from pydantic import BaseModel
from silo import Skill, AgentResponse

skill = Skill("issue_tracker")

class Issue(BaseModel):
    title: str
    body: str

@skill.tool()
def create_issue(repo: str, detail: Issue):
    """Создает новую задачу (issue) в репозитории."""
    # detail теперь является типизированным объектом Pydantic
    print(f"Создание задачи '{detail.title}' в {repo}")
    
    return AgentResponse(
        llm_text=f"Задача '{detail.title}' создана в {repo}",
        raw_data={"status": "created", "repo": repo, "issue": detail.title}
    )
```

Использование через CLI:
```bash
silo run issue_tracker create_issue \
    --repo "user/repo" \
    --detail '{"title": "Bug", "body": "Fixed"}'
```
```text title="Симуляция вывода"
⠋ Executing issue_tracker:create_issue...
╭────────────────────────────── Execution Result ───────────────────────────────╮
│ Задача 'Bug' создана в user/repo                                             │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Управление секретами

Для работы с конфиденциальными данными (например, API-токенами), используйте `require_secret()`. SILO возьмет на себя безопасное хранение в Keychain ОС и запросит пользователя только один раз.

```python
from silo import Skill, require_secret

skill = Skill("github")

@skill.tool()
def get_user():
    token = require_secret("GITHUB_TOKEN")
    # Используйте токен в API-вызовах...
    return "Данные пользователя получены."
```

## Структурирование вывода

Инструмент SILO может возвращать:
1. **Строку**: Автоматически оборачивается в успешный ответ.
2. **Словарь (dict)**: Автоматически преобразуется в JSON.
3. **`AgentResponse`**: Рекомендуемый способ предоставить раздельный контент для LLM и для вызывающей системы (оркестратора).

```python
from silo import Skill, AgentResponse

skill = Skill("github")

@skill.tool()
def get_stats():
    # Предоставляем детальный контекст для LLM и сырые данные для системы
    return AgentResponse(
        llm_text="В репозитории 42 активных пользователя, система работает стабильно.",
        raw_data={"active_users": 42, "status": "healthy"}
    )
```
