# Интеграция: Claude Desktop

Подключение SILO к Claude Desktop позволяет использовать все установленные скиллы напрямую в интерфейсе Claude на macOS или Windows.

## 1. Найдите конфиг Claude

Откройте файл конфигурации Claude Desktop:
- **macOS**: `~/Library/Application Support/AnthropicClaude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\AnthropicClaude\claude_desktop_config.json`

## 2. Добавьте SILO как MCP-сервер

Добавьте новую запись в объект `mcpServers`. Замените `<PATH_TO_SILO>` на абсолютный путь к исполняемому файлу `silo` (обычно находится в вашем virtualenv или глобальном пути).

```json
{
  "mcpServers": {
    "silo": {
      "command": "<PATH_TO_SILO>",
      "args": ["mcp", "run"]
    }
  }
}
```

## 3. Перезапустите Claude

Полностью выйдите из Claude Desktop и запустите его снова. Вы должны увидеть сервер `silo` в настройках в разделе подключенных MCP-серверов.

## 4. Использование

Просто попросите Claude выполнить задачу.

- **Обнаружение (Discovery)**: Claude автоматически вызовет `silo_search`, если не найдет прямого соответствия инструмента.
- **Выполнение (Execution)**: Claude вызовет `silo_execute` для запуска найденных инструментов.

> **Пример**: «Claude, найди скиллы для проверки метрик сайта и затем получи отчет для example.com».

---

**Далее:** Узнайте, как использовать [Пользовательские оркестраторы](custom.md).
