# Создание навыков

Это руководство описывает основные концепции создания команд в SILO.

## Класс `Skill`

Навык SILO — это экземпляр класса `Skill`, который управляет командами, парсингом аргументов, обработкой ошибок и сериализацией.

```python
from silo import Skill

app = Skill(name="My Skill", description="Описание того, что он делает.")
```

## Создание команд

Команды — это функции, обернутые в декоратор `@app.command()`. SILO читает сигнатуру функции, чтобы определить аргументы, их типы и значения по умолчанию.

```python
@app.command()
def greet(name: str, shout: bool = False):
    """Приветствует пользователя по имени."""
    msg = f"Hello, {name}!"
    if shout:
        msg = msg.upper()
    return {"message": msg}
```

SILO автоматически преобразует это в CLI-флаги:
```bash
uv run my_skill.py greet --name Alice --shout True
```

## Использование Pydantic для сложных данных

LLM отлично пишут JSON. Если вашей команде нужна сложная структура данных (объект или список), используйте **Pydantic-модели** вместо длинного списка аргументов.

SILO автоматически примет JSON-строку из CLI, провалидирует ее и передаст готовый объект в вашу функцию.

```python
from pydantic import BaseModel
from silo import Skill, JSONResponse

app = Skill("issue_tracker")

class Issue(BaseModel):
    title: str
    body: str

@app.command()
def create_issue(repo: str, detail: Issue):
    """Создает новую задачу в репозитории."""
    # detail теперь является типизированным объектом Pydantic
    print(f"Создание задачи '{detail.title}' в {repo}")
    
    return JSONResponse(
        {"status": "created", "repo": repo, "issue": detail.title}
    )
```

Вызов из CLI:
```bash
uv run my_skill.py create_issue \
    --repo "user/repo" \
    --detail '{"title": "Bug", "body": "Fixed"}'
```

Если JSON не соответствует модели, SILO вернет понятную ошибку, объясняющую агенту, что именно пошло не так.

## Структура ответа

При возврате данных из команды ВСЕГДА возвращайте структурированный объект (словарь, список или `SiloResponse`). Агенты общаются через текстовые потоки и ищут данные, которые можно распарсить.

SILO предоставляет вспомогательные классы:

- **`JSONResponse(data)`**: Превращает вывод в красивый JSON.
- **`MarkdownResponse(text)`**: Указывает, что результат — это форматированный текст.

```python
from silo import Skill, JSONResponse, MarkdownResponse

app = Skill("format_tool")

@app.command()
def get_stats():
    # Рекомендуется: возврат JSON для программной обработки агентом
    return JSONResponse({"active": True, "users": 42})

@app.command()
def get_readme():
    # Рекомендуется: возврат чистого Markdown
    return MarkdownResponse("# Project README\n\nСодержимое файла.")
```
