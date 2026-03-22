````md
# project_18machine

Локальная система управления машиной с веб-интерфейсом на **FastAPI** и управлением платой клапанов через **COM-порт**.

## Статус проекта
🚧 В разработке

---

## Описание

Проект предназначен для:
- выбора рецепта;
- задания количества повторов рецепта;
- управления циклами и событиями клапанов;
- отображения текущего состояния машины в реальном времени;
- работы как в **mock-режиме**, так и с **реальной платой**.

---

## Возможности

### Главный экран
- отображение состояния машины;
- отображение угла энкодера;
- отображение оборотов;
- отображение текущего цикла;
- отображение текущего оборота цикла;
- отображение текущего повтора рецепта;
- выбор рецепта;
- изменение количества повторов;
- сброс на первый цикл;
- переход в настройки.

### Экран настроек
- создание рецептов;
- копирование рецептов;
- удаление рецептов;
- создание циклов;
- копирование циклов;
- удаление циклов;
- изменение порядка циклов;
- настройка количества оборотов в цикле;
- настройка событий клапанов;
- сохранение всех рецептов.

### Работа с железом
Поддерживается два режима:
- `mock` — для отладки без реальной платы;
- `real` — для работы с реальной платой клапанов через COM-порт.

---

## Стек проекта

### Backend
- FastAPI
- Pydantic
- Jinja2
- WebSocket
- pyserial

### Frontend
- HTML (Jinja2 templates)
- JavaScript (vanilla)
- CSS

---

## Структура проекта

```text
project_18machine/
├── app/
│   ├── core/
│   │   ├── engine.py
│   │   └── machine_state.py
│   │
│   ├── hardware/
│   │   ├── board_driver.py
│   │   ├── hardware_manager.py
│   │   └── mock_valve_driver.py
│   │
│   ├── routes/
│   │   ├── api_recipes.py
│   │   ├── ui.py
│   │   └── ws.py
│   │
│   ├── services/
│   │   ├── execution_service.py
│   │   └── recipe_service.py
│   │
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   │
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   └── settings.html
│   │
│   └── main.py
│
├── requirements.txt
└── test_engine.py
````

---

## Формат рецепта

```python
{
    "id": 1,
    "name": "Мочалка A",
    "repeats": 3,
    "cycles": [
        {
            "id": 101,
            "turns": 2,
            "events": [
                {"valve": 1, "event": "on", "angle": 45},
                {"valve": 2, "event": "off", "angle": 90}
            ]
        }
    ]
}
```

### Пояснение

* `repeats` — сколько раз повторить рецепт;
* `cycles` — список циклов;
* `turns` — количество оборотов в цикле;
* `events` — список событий клапанов;
* `event`:

  * `""` — нет действия
  * `"on"` — включить
  * `"off"` — выключить

---

## Зависимости

Рекомендуемый `requirements.txt`:

```txt
fastapi
uvicorn[standard]
jinja2
pydantic
pyserial
```

---

## Установка

### 1. Клонирование

```bash
git clone https://github.com/iGrayf2/project_18machine.git
cd project_18machine
```

### 2. Виртуальное окружение

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

---

## Запуск

```bash
uvicorn app.main:app --reload
```

Открыть в браузере:

```
http://127.0.0.1:8000
```

---

## Переменные окружения

```env
HARDWARE_MODE=mock
BOARD_PORT=COM5
BOARD_BAUDRATE=625000
BOARD_CHANNELS=80
BOARD_PROTOCOL_CHANNELS=96
BOARD_AUTO_INIT=1
```

### Примеры

#### Windows PowerShell

```powershell
$env:HARDWARE_MODE="mock"
uvicorn app.main:app --reload
```

#### Linux

```bash
export HARDWARE_MODE=mock
uvicorn app.main:app --reload
```

---

## Режимы работы

### Mock режим

```bash
HARDWARE_MODE=mock
```

Используется для разработки без оборудования.

---

### Real режим

```bash
HARDWARE_MODE=real
BOARD_PORT=COM5
BOARD_BAUDRATE=625000
BOARD_CHANNELS=80
BOARD_PROTOCOL_CHANNELS=96
BOARD_AUTO_INIT=1
```

Используется для работы с реальной платой.

---

## WebSocket

Endpoint:

```
/ws
```

### События от сервера

* `machine_status`

### Действия от клиента

```json
{ "action": "select_recipe", "recipe_id": 1 }
{ "action": "set_recipe_repeats", "value": 3 }
{ "action": "reset_to_cycle_1" }
```

---

## API

### Получить рецепты

```
GET /api/recipes
```

### Сохранить рецепты

```
POST /api/recipes/save
```

```json
{
  "recipes": []
}
```

---

## Горячие клавиши

### Главный экран

* F2 — настройки
* F5 — сброс
* ↑ / ↓ — смена рецепта
* Enter — применить
* Esc — убрать фокус

### Настройки

* F2 — назад
* F6 — сохранить
* Insert — новый
* Delete — удалить
* Alt + ↑ / ↓ — рецепты
* PageUp / PageDown — циклы
* Ctrl + ↑ / ↓ — перемещение цикла
* Space — смена события
* 0 / 1 / 2 — действие
* Enter — редактировать угол
* Ctrl + C / Ctrl + V — копировать / вставить

---

## Тестирование

```bash
python test_engine.py
```

Проверяет:

* работу движка;
* переходы циклов;
* обработку событий клапанов.

---

## Планы

* подключение реального энкодера;
* подключение датчика оборота;
* отказ от симуляции;
* сохранение рецептов в БД;
* логирование;
* диагностика оборудования;
* сервисный режим.

---

## Автор

Сергей iGray
GitHub: [https://github.com/iGrayf2](https://github.com/iGrayf2)

```
