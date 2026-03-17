# Интеграция: Пользовательские оркестраторы

Хотя SILO отлично работает с Claude Desktop через MCP, он также спроектирован для программного использования в ваших собственных ИИ-агентах на Python.

## 1. Использование `Runner` напрямую

Класс `Runner` в модуле `silo.runner` — это программный способ выполнения скиллов из вашего кода.

```python
from silo.core.hub import HubManager
from silo.core.runner import Runner

hub = HubManager()
runner = Runner(hub)

async def main():
    # Выполнение инструмента
    result = await runner.execute(
        namespace="quotes",
        tool="get_random_quote",
        kwargs={}
    )
    
    print(result["llm_text"])

import asyncio
asyncio.run(main())
```

## 2. Использование `SearchEngine`

Вы можете интегрировать динамическое обнаружение SILO в цикл рассуждений вашего агента.

```python
from silo.services.search import SearchEngine

search = SearchEngine()

async def discover_tools(query: str):
    results = await search.search(query, limit=3)
    for res in results:
        print(f"Найден {res['full_id']}: {res['description']}")
```

## 3. Подключение к LangChain / LlamaIndex

Поскольку SILO предоставляет стандартный интерфейс MCP, вы можете использовать существующие адаптеры MCP для таких фреймворков, как LangChain.

```python
# Пример псевдокода
from langchain_mcp import MCPServerTool

s_tool = MCPServerTool(
    command="silo",
    args=["mcp", "run"]
)
agent.add_tool(s_tool)
```

---

**Далее:** Ознакомьтесь с полным [Справочником CLI](../reference/cli.ru.md).
