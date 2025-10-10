# NiceGUI Framework Documentation for Slack Insights

> **Research Date:** 2025-10-10
> **Purpose:** Comprehensive documentation for implementing NiceGUI interface (#3)
> **Framework Version:** NiceGUI 1.4+
> **Official Docs:** https://nicegui.io/

---

## Table of Contents

1. [Framework Overview](#framework-overview)
2. [Core Components](#core-components)
3. [Layout Components](#layout-components)
4. [Advanced Features](#advanced-features)
5. [Integration & Architecture](#integration--architecture)
6. [Deployment & Packaging](#deployment--packaging)
7. [Best Practices](#best-practices)
8. [Code Examples](#code-examples)
9. [Reference Links](#reference-links)

---

## Framework Overview

### What is NiceGUI?

NiceGUI is a Python web framework that turns Python code into interactive web interfaces without requiring JavaScript knowledge. It follows a **backend-first philosophy** where all UI logic lives in Python.

**Key Characteristics:**
- Python-native (no JavaScript required)
- Built on FastAPI backend + Vue/Quasar frontend
- Socket.io for real-time client-server communication
- Event-driven architecture (no full-page reruns like Streamlit)
- One uvicorn worker with full async support

**Installation:**
```bash
pip install nicegui
```

**Official Documentation:** https://nicegui.io/documentation

---

## Core Components

### 1. ui.input - Text Input Field

**Documentation:** https://nicegui.io/documentation/input

**Description:** Text entry field based on Quasar's QInput component with support for validation, autocomplete, and password modes.

**Key Parameters:**
- `label`: Display label for the input
- `placeholder`: Text shown when empty
- `value`: Initial/current value
- `password`: Boolean to hide input (default: False)
- `password_toggle_button`: Show visibility toggle (default: False)
- `on_change`: Callback function triggered on value change
- `autocomplete`: List of strings for autocompletion
- `validation`: Dict of validation rules or callable

**Validation Example:**
```python
query_input = ui.input(
    label='Natural language query',
    placeholder='What did Dan ask me to do?',
    validation={'Too short': lambda value: len(value) >= 3}
).classes('w-full')

# Event handling
query_input.on('keydown.enter', handle_submit)
query_input.on('blur', handle_blur)
```

**Styling Notes:**
- Cannot style input directly
- Use `.props('input-class=...')` and `.props('input-style=...')` to modify native input
- Apply Tailwind classes via `.classes('...')`

**Advanced Validation:**
```python
# Multiple validation rules
ui.input(
    validation={
        'Too short': lambda v: len(v) >= 3,
        'Too long': lambda v: len(v) <= 50,
        'Invalid chars': lambda v: v.isalnum()
    }
)

# Disable auto-validation (validate on submit)
ui.input(...).without_auto_validation()
```

---

### 2. ui.tree - Hierarchical Tree Display

**Documentation:** https://nicegui.io/documentation/tree

**Description:** Displays hierarchical data using Quasar's QTree component with support for selection, expansion, and checkboxes.

**Key Parameters:**
- `nodes`: Hierarchical list of node objects (required)
- `node_key`: Unique identifier property (default: "id")
- `label_key`: Property for node label (default: "label")
- `children_key`: Property for child nodes (default: "children")
- `on_select`: Callback for node selection changes
- `on_expand`: Callback for node expansion changes
- `on_tick`: Callback for checkbox interactions
- `tick_strategy`: Checkbox behavior ("leaf", "leaf-filtered", "strict")

**Data Structure:**
```python
nodes = [
    {
        'id': 'task-group-1',
        'label': '⚠ Mentioned 4 times - Deploy API endpoint',
        'children': [
            {'id': 'task-1-1', 'label': '2025-10-07 - "Deploy before EOD..."'},
            {'id': 'task-1-2', 'label': '2025-10-06 - "Reminder about API..."'},
        ]
    },
    {
        'id': 'task-group-2',
        'label': '⚠ Mentioned 3 times - Provide PSD file',
        'children': [...]
    }
]

tree = ui.tree(
    nodes,
    node_key='id',
    label_key='label',
    on_select=lambda e: handle_selection(e)
).classes('w-full')
```

**Important Notes:**
- Ensure node IDs are unique across the entire tree
- Checkboxes require setting `tick_strategy`
- Use `.props('default-expand-all')` to expand all nodes initially

**Programmatic Control:**
```python
# Expand/collapse programmatically (requires PR #1239 features)
tree.expand(['node-id-1', 'node-id-2'])
tree.collapse(['node-id-3'])
```

**GitHub Discussions:**
- Programmatic expand/collapse: https://github.com/zauberzeug/nicegui/discussions/1230
- Populating trees: https://github.com/zauberzeug/nicegui/discussions/804

---

### 3. ui.expansion - Collapsible Sections

**Documentation:** https://nicegui.io/documentation/expansion

**Description:** Creates expandable/collapsible containers based on Quasar's QExpansionItem.

**Key Parameters:**
- `text`: Title text (required)
- `caption`: Optional subtitle
- `icon`: Optional icon
- `group`: Optional group name for accordion mode
- `value`: Initially open state (default: False)
- `on_value_change`: Callback when expansion state changes

**Basic Usage:**
```python
with ui.expansion('⚠ Mentioned 4 times - Deploy API endpoint', caption='@itzaferg'):
    ui.label('Instance 1 - 2025-10-07 12:22')
    ui.markdown('**Status:** open\n"Deploy before EOD..."')
    ui.separator()
    ui.label('Instance 2 - 2025-10-07 12:21')
    ui.markdown('**Status:** open\n"Just a reminder..."')
```

**Accordion Mode (only one open at a time):**
```python
# Group expansions so only one can be open
with ui.expansion('Group 1', group='results'):
    ui.label('Content 1')

with ui.expansion('Group 2', group='results'):
    ui.label('Content 2')
```

**Dynamic Content:**
```python
def create_task_expansion(task_group):
    with ui.expansion(
        f"⚠ {task_group['count']}x - {task_group['canonical_task']}",
        icon='priority_high',
        value=False
    ):
        for instance in task_group['instances']:
            with ui.card().tight():
                ui.label(f"📅 {instance['date']}")
                ui.label(f"Status: {instance['status']}")
                ui.markdown(instance['context'])
```

---

### 4. ui.button - Interactive Buttons

**Documentation:** https://nicegui.io/documentation/button

**Description:** Versatile button component with multiple styles and interaction modes.

**Key Features:**
- Standard buttons, icon buttons, FABs
- Can await button clicks
- Context manager for disabling
- Various styling options

**Basic Usage:**
```python
# Standard button
ui.button('Search', on_click=handle_search)

# Icon button
ui.button(icon='search', on_click=handle_search).props('flat')

# Async button (await click)
async def wait_for_click():
    result = await ui.button('Click me').clicked()
    ui.notify('Button clicked!')
```

---

### 5. ui.label & ui.markdown - Text Display

**Documentation:**
- ui.label: https://nicegui.io/documentation/label
- ui.markdown: https://nicegui.io/documentation/markdown

**ui.label:**
```python
ui.label('Simple text')
ui.label('Dynamic text').bind_text(data_model, 'field_name')
```

**ui.markdown:**
```python
# Supports code blocks, tables, mermaid diagrams, LaTeX
ui.markdown('''
## Task Details
- **Status:** Open
- **Assigned:** @itzaferg
- **Date:** 2025-10-07

```python
def example():
    pass
```
''')

# Dynamic updates
content = ui.markdown()
content.set_content('# New content')
```

---

### 6. ui.context_menu - Right-Click Menus

**Documentation:** https://nicegui.io/documentation/context_menu

**Description:** Create context menus that appear on right-click.

**Usage:**
```python
with ui.card():
    ui.label('Task: Deploy API endpoint')

    with ui.context_menu():
        ui.menu_item('Mark as complete', on_click=lambda: mark_complete())
        ui.menu_item('Edit task', on_click=lambda: edit_task())
        ui.separator()
        ui.menu_item('Delete', on_click=lambda: delete_task())
```

---

### 7. ui.tooltip - Hover Information

**Documentation:** https://nicegui.io/documentation/tooltip

**Description:** Show additional information on hover.

**Usage:**
```python
with ui.button(icon='info'):
    ui.tooltip('This shows task context from the original Slack message')

# With nested elements
with ui.label('⚠'):
    with ui.tooltip():
        ui.label('High frequency task')
        ui.label('Mentioned 4 times')
```

---

### 8. ui.keyboard - Global Keyboard Events

**Documentation:** https://nicegui.io/documentation/keyboard

**Description:** Track keyboard events globally or within specific contexts.

**Key Event Details:**
- `action`: keydown, keyup, repeat
- `key.name`: Key name (e.g., "a", "Enter", "Escape")
- `key.code`: Key code
- `modifiers`: alt, ctrl, meta, shift

**Usage:**
```python
def handle_key(e):
    if e.key.name == 'Enter':
        submit_query()
    elif e.key.name == 'Escape':
        clear_results()
    elif e.modifiers.ctrl and e.key.name == 'k':
        focus_search_input()

ui.keyboard(on_key=handle_key)
```

---

## Layout Components

### 1. ui.row - Horizontal Layout

**Documentation:** https://nicegui.io/documentation/row

**Parameters:**
- `wrap`: Content wrapping (default: True)
- `align_items`: Vertical alignment ("start", "end", "center", "baseline", "stretch")

**Usage:**
```python
with ui.row().classes('w-full items-center'):
    ui.label('Status:')
    ui.label('⏳ Open').classes('text-yellow-500')
    ui.button(icon='check', on_click=mark_complete).props('flat')
```

---

### 2. ui.column - Vertical Layout

**Documentation:** https://nicegui.io/documentation/column

**Parameters:**
- `wrap`: Content wrapping (default: False)
- `align_items`: Horizontal alignment ("start", "end", "center", "baseline", "stretch")

**Usage:**
```python
with ui.column().classes('w-full gap-4'):
    ui.label('Task Details')
    ui.label('Date: 2025-10-07')
    ui.label('Status: Open')
```

---

### 3. ui.card - Content Container

**Documentation:** https://nicegui.io/documentation/card

**Description:** Container with dropped shadow, based on Quasar's QCard.

**Parameters:**
- `align_items`: Item alignment

**Key Methods:**
- `.tight()`: Remove default padding

**Usage:**
```python
with ui.card():
    ui.label('Task Group')
    with ui.row():
        ui.label('Status: ⏳ Open')
        ui.button(icon='expand_more')

# Tight layout (no padding)
with ui.card().tight():
    ui.image('screenshot.png')
```

**Styling:**
```python
with ui.card().classes('bg-slate-800 border border-slate-700'):
    ui.label('Dark mode card')
```

---

### 4. ui.grid - Grid Layout

**Documentation:** https://nicegui.io/documentation/grid

**Parameters:**
- `rows`: Number of rows or CSS grid-template-rows
- `columns`: Number of columns or CSS grid-template-columns

**Usage:**
```python
# Simple grid
with ui.grid(columns=2):
    ui.label('Label:')
    ui.label('Value')
    ui.label('Status:')
    ui.label('Open')

# Advanced grid with Tailwind spanning
with ui.grid(rows=6, columns=12):
    with ui.card().classes('col-span-8 row-span-4'):
        ui.label('Main content')

    with ui.card().classes('col-span-4 row-span-2'):
        ui.label('Sidebar')
```

---

## Advanced Features

### 1. ui.refreshable - Dynamic UI Updates

**Documentation:** https://nicegui.io/documentation/refreshable

**Description:** Decorator that allows functions to recreate their UI elements by calling `.refresh()`.

**Basic Usage:**
```python
@ui.refreshable
def results_display():
    results = query_database()
    for result in results:
        ui.label(result)

# Update display
ui.button('Refresh', on_click=results_display.refresh)
```

**Method Variant:**
```python
class ResultsView:
    @ui.refreshable_method
    def show(self):
        # Display results
        pass

view = ResultsView()
view.show.refresh()
```

**Best Practices:**
- Use when you need to completely rebuild a UI section
- For small changes, prefer updating individual elements
- Performance consideration: recreates all elements (use virtualization for large lists)

---

### 2. Dark Mode Implementation

**Documentation:** https://nicegui.io/documentation/styling

**Setup:**
```python
# Toggle dark mode
ui.dark_mode().bind_value(app.storage.user, 'dark_mode')

# Manual control
dark = ui.dark_mode()
ui.button('Toggle theme', on_click=dark.toggle)

# Set specific mode
dark.enable()  # Dark mode
dark.disable()  # Light mode
dark.auto()    # Follow system
```

**Styling with Dark Mode:**
```css
/* In custom CSS */
:root {
    --background: oklch(0.985 0 0);
    --foreground: oklch(0.145 0 0);
    --primary: oklch(0.488 0.243 264.376);
}

.dark {
    --background: oklch(0.145 0 0);
    --foreground: oklch(0.985 0 0);
    --primary: oklch(0.646 0.222 41.116);
}
```

**Tailwind Dark Mode Classes:**
```python
ui.label('Text').classes('text-slate-900 dark:text-slate-100')
ui.card().classes('bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700')
```

---

### 3. Custom Styling

**Tailwind CSS Classes:**
```python
# Spacing
ui.label('Text').classes('p-4 mb-2 space-y-4')

# Colors
ui.label('Status').classes('text-green-500 bg-green-100/50')

# Borders & Shadows
ui.card().classes('border border-slate-700/50 shadow-lg')

# Responsive
ui.grid().classes('grid-cols-1 md:grid-cols-2 lg:grid-cols-4')

# Animations
ui.button().classes('transition-colors hover:bg-primary/90 active:scale-95')
```

**Custom CSS:**
```python
ui.add_head_html('''
<style>
    .custom-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 16px;
    }
</style>
''')

ui.card().classes('custom-card')
```

---

### 4. File Download

**Documentation:** https://nicegui.io/documentation/download

**Methods:**
```python
# Download local file
ui.button('Download', on_click=lambda: ui.download('data.csv'))

# Download from URL
ui.button('Download', on_click=lambda: ui.download.from_url('https://example.com/file.pdf'))

# Download raw content
def export_results():
    content = '\n'.join(format_result(r) for r in results)
    ui.download(content.encode(), 'results.txt')

ui.button('Export', on_click=export_results)
```

**CSV Export Example:**
```python
import csv
import io

def export_csv():
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['task', 'status', 'date'])
    writer.writeheader()
    writer.writerows(results)

    ui.download(output.getvalue().encode(), 'tasks.csv')
```

**Markdown Export:**
```python
def export_markdown():
    md = '# Action Items\n\n'
    for result in results:
        md += f"## {result['task']}\n"
        md += f"- **Status:** {result['status']}\n"
        md += f"- **Date:** {result['date']}\n\n"

    ui.download(md.encode(), 'action-items.md')
```

---

## Integration & Architecture

### 1. FastAPI Integration

NiceGUI is built on FastAPI, allowing seamless integration with existing FastAPI apps.

**Basic Integration:**
```python
from fastapi import FastAPI
from nicegui import ui, app

# Create FastAPI app
fastapi_app = FastAPI()

# Add API endpoints
@fastapi_app.get('/api/tasks')
async def get_tasks():
    return {'tasks': [...]}

# Create NiceGUI pages
@ui.page('/')
def index():
    ui.label('Main page')

# Run together
ui.run_with(fastapi_app)
```

**Calling Backend from Frontend:**
```python
import httpx

@ui.page('/')
async def index():
    async def fetch_data():
        async with httpx.AsyncClient() as client:
            response = await client.get('http://localhost:8080/api/tasks')
            data = response.json()
            results_display(data)

    ui.button('Fetch', on_click=fetch_data)
```

---

### 2. Database Integration (SQLite)

**Official Example:** https://github.com/zauberzeug/nicegui/blob/main/examples/sqlite_database/main.py

**Using Tortoise ORM (Async):**
```python
from tortoise import Tortoise
from nicegui import app, ui

async def init_db():
    await Tortoise.init(
        db_url='sqlite://slack_insights.db',
        modules={'models': ['models']}
    )
    await Tortoise.generate_schemas()

async def close_db():
    await Tortoise.close_connections()

app.on_startup(init_db)
app.on_shutdown(close_db)

@ui.refreshable
async def query_results():
    tasks = await ActionItem.filter(status='open').all()
    for task in tasks:
        ui.label(task.description)

@ui.page('/')
async def index():
    query_input = ui.input('Query')

    async def search():
        await query_results.refresh()

    ui.button('Search', on_click=search)
    await query_results()
```

**Using sqlite3 (Sync with Thread Pool):**
```python
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from nicegui import ui

executor = ThreadPoolExecutor(max_workers=1)

def query_db_sync(query):
    conn = sqlite3.connect('slack_insights.db')
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results

@ui.page('/')
async def index():
    async def search():
        results = await asyncio.get_event_loop().run_in_executor(
            executor,
            query_db_sync,
            "SELECT * FROM action_items"
        )
        display_results(results)

    ui.button('Search', on_click=search)
```

---

### 3. Page Routing & Modularization

**Documentation:** https://nicegui.io/documentation/section_pages_routing

**Basic Routing:**
```python
@ui.page('/')
def index():
    ui.label('Home page')

@ui.page('/search')
def search():
    ui.label('Search page')

@ui.page('/results/{task_id}')
def task_detail(task_id: str):
    ui.label(f'Task {task_id}')
```

**Modular Structure with APIRouter:**
```python
# main.py
from nicegui import ui
from . import search_page, results_page

ui.run()

# search_page.py
from nicegui import ui, APIRouter

router = APIRouter()

@router.page('/search')
def search_page():
    ui.label('Search interface')
```

**Project Structure:**
```
src/slack_insights/
├── gui/
│   ├── __init__.py
│   ├── app.py              # Main entry point
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── search.py       # Search page
│   │   └── results.py      # Results page
│   ├── components/
│   │   ├── query_input.py  # Reusable components
│   │   └── task_card.py
│   └── utils/
│       ├── formatting.py
│       └── state.py
```

---

### 4. State Management

**User Storage (Per-User Session):**
```python
from nicegui import app, ui

@ui.page('/')
def index():
    # Store per-user data
    if 'query_history' not in app.storage.user:
        app.storage.user['query_history'] = []

    def add_query(query):
        app.storage.user['query_history'].append(query)
        app.storage.user['query_history'] = app.storage.user['query_history'][-10:]  # Keep last 10

    ui.label(f"Recent queries: {len(app.storage.user['query_history'])}")
```

**General Storage (Shared Across Users):**
```python
# Store app-wide data
app.storage.general['total_queries'] = app.storage.general.get('total_queries', 0) + 1
```

**Browser Storage (Client-Side):**
```python
# Persists across sessions in browser
app.storage.browser['dark_mode'] = True
```

---

## Deployment & Packaging

### 1. Local Development

**Basic Launch:**
```python
# main.py
from nicegui import ui

@ui.page('/')
def index():
    ui.label('Slack Insights')

ui.run()
```

**Run:**
```bash
python main.py
# Launches at http://localhost:8080
```

**Configuration:**
```python
ui.run(
    host='127.0.0.1',
    port=8080,
    title='Slack Insights',
    reload=True,  # Auto-reload on code changes
    show=True,    # Open browser automatically
    dark=None,    # Dark mode: None (auto), True, False
)
```

---

### 2. Desktop App with PyWebView

**GitHub Gist:** https://gist.github.com/eli-kha/06a47bfdf1e50f4cdfc3f43a199a6d2d

**Complete Implementation:**
```python
#!/usr/bin/env python3

import multiprocessing
import tempfile
from fastapi import FastAPI
from uvicorn import Config, Server
import webview
from nicegui import ui

class UvicornServer(multiprocessing.Process):
    def __init__(self, config: Config):
        super().__init__()
        self.server = Server(config=config)
        self.config = config

    def stop(self):
        self.terminate()

    def run(self, *args, **kwargs):
        self.server.run()

def start_window(pipe_send, url_to_load):
    def on_closed():
        pipe_send.send('closed')

    win = webview.create_window('Slack Insights', url=url_to_load, width=1200, height=800)
    win.events.closed += on_closed
    webview.start(storage_path=tempfile.mkdtemp())

# Your NiceGUI app
@ui.page('/app')
def main_page():
    ui.label('Slack Insights Desktop App')

if __name__ == '__main__':
    server_ip = "127.0.0.1"
    server_port = 8080

    conn_recv, conn_send = multiprocessing.Pipe()

    # Start PyWebView window
    windowsp = multiprocessing.Process(
        target=start_window,
        args=(conn_send, f'http://{server_ip}:{server_port}/app')
    )
    windowsp.start()

    # Start server
    config = Config("main:app", host=server_ip, port=server_port, log_level="error")
    instance = UvicornServer(config=config)
    instance.start()

    # Wait for window to close
    window_status = ''
    while 'closed' not in window_status:
        window_status = conn_recv.recv()

    # Cleanup
    instance.stop()
    windowsp.join()
```

**Installation:**
```bash
pip install pywebview
```

**Notes:**
- PyWebView creates native window (no browser UI)
- Works on macOS, Windows, Linux
- Can package with PyInstaller/py2app for distribution

---

### 3. Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

**Docker Compose:**
```yaml
version: '3.8'
services:
  slack-insights:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./slack_insights.db:/app/slack_insights.db
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
```

---

## Best Practices

### 1. Project Structure

**Recommended Organization:**
```
src/slack_insights/gui/
├── __init__.py
├── main.py                 # Entry point
├── pages/
│   ├── __init__.py
│   ├── search.py           # Search page
│   └── settings.py         # Settings page
├── components/
│   ├── __init__.py
│   ├── query_input.py      # Reusable query input
│   ├── results_tree.py     # Results display
│   └── task_card.py        # Task card component
└── utils/
    ├── __init__.py
    ├── formatting.py       # Date/text formatting
    └── state.py            # State management helpers
```

---

### 2. Component Design Patterns

**Reusable Component:**
```python
# components/task_card.py
from nicegui import ui

def task_card(task):
    """Display a single task in a card."""
    with ui.card().classes('w-full'):
        with ui.row().classes('w-full items-center justify-between'):
            ui.label(task['description']).classes('font-medium')
            ui.label(task['status']).classes('text-sm')

        with ui.row().classes('gap-2 mt-2'):
            ui.label(f"👤 {task['assigner']}")
            ui.label(f"📅 {task['date']}")

# Usage
from .components.task_card import task_card

for task in tasks:
    task_card(task)
```

**Refreshable Component:**
```python
@ui.refreshable
def results_view(query_results):
    """Display query results with refresh capability."""
    if not query_results:
        ui.label('No results found').classes('text-gray-500')
        return

    for group in query_results:
        with ui.expansion(f"⚠ {group['count']}x - {group['task']}"):
            for instance in group['instances']:
                task_card(instance)

# Update results
results_view.refresh()
```

---

### 3. Performance Optimization

**Pagination for Large Lists:**
```python
@ui.refreshable
def paginated_results(results, page=1, per_page=20):
    start = (page - 1) * per_page
    end = start + per_page
    page_results = results[start:end]

    for result in page_results:
        task_card(result)

    # Pagination controls
    with ui.row():
        if page > 1:
            ui.button('Previous', on_click=lambda: show_page(page - 1))
        if end < len(results):
            ui.button('Next', on_click=lambda: show_page(page + 1))

def show_page(page):
    paginated_results.refresh()
```

**Lazy Loading:**
```python
@ui.refreshable
def lazy_results(visible_count):
    """Load more results as user scrolls."""
    for i, result in enumerate(results[:visible_count]):
        task_card(result)

    if visible_count < len(results):
        ui.button('Load more', on_click=lambda: lazy_results.refresh(visible_count + 20))
```

---

### 4. Error Handling

**User-Friendly Error Display:**
```python
async def handle_query(query_text):
    try:
        results = await query_database(query_text)
        display_results(results)
    except TimeoutError:
        ui.notify('Query timed out. Please try again.', type='negative')
    except Exception as e:
        ui.notify(f'Error: {str(e)}', type='negative')
        logger.exception('Query failed')
```

**Loading States:**
```python
async def search_with_loading(query):
    spinner = ui.spinner('dots', size='lg')
    status = ui.label('Searching...')

    try:
        results = await perform_search(query)
        spinner.delete()
        status.delete()
        display_results(results)
    except Exception as e:
        spinner.delete()
        status.set_text(f'Error: {str(e)}')
```

---

## Code Examples

### Example 1: Complete Search Interface

```python
from nicegui import ui, app
import asyncio

# State
current_results = []

@ui.refreshable
def results_display():
    """Display search results with grouping."""
    if not current_results:
        ui.label('Enter a query to search').classes('text-gray-500')
        return

    for group in current_results:
        with ui.expansion(
            f"⚠ {group['count']}x - {group['task']}",
            icon='priority_high'
        ).classes('w-full'):
            for instance in group['instances']:
                with ui.card().tight().classes('mb-2'):
                    with ui.row().classes('items-center justify-between p-4'):
                        ui.label(f"📅 {instance['date']}")
                        ui.label(instance['status'])
                    ui.markdown(instance['context']).classes('p-4 pt-0')

@ui.page('/')
def main():
    ui.label('🔍 Slack Insights').classes('text-2xl font-bold mb-4')

    query_input = ui.input(
        placeholder='What did Dan ask me to do?',
        on_change=lambda e: handle_query(e.value)
    ).classes('w-full')

    query_input.on('keydown.enter', lambda: handle_search())

    ui.button('Search', on_click=handle_search)

    results_display()

async def handle_search():
    global current_results
    query = query_input.value

    if not query:
        return

    # Show loading
    ui.notify('Searching...', type='ongoing')

    try:
        # Query backend
        results = await query_backend(query)
        current_results = results
        results_display.refresh()
        ui.notify(f'Found {len(results)} results', type='positive')
    except Exception as e:
        ui.notify(f'Error: {str(e)}', type='negative')

ui.run()
```

---

### Example 2: Task Card Component with Context Menu

```python
from nicegui import ui

def task_card(task):
    """Reusable task card with context menu."""
    with ui.card().classes('w-full hover:shadow-lg transition-shadow'):
        # Header
        with ui.row().classes('w-full items-center justify-between'):
            status_icon = '⏳' if task['status'] == 'open' else '✅'
            ui.label(f"{status_icon} {task['description']}").classes('font-medium')
            ui.label(f"{task['count']}x" if task['count'] > 1 else '').classes('text-sm')

        # Metadata
        with ui.row().classes('gap-4 mt-2 text-sm text-gray-600'):
            ui.label(f"👤 {task['assigner']}")
            ui.label(f"📅 {task['date']}")

        # Context menu
        with ui.context_menu():
            ui.menu_item('Mark complete', on_click=lambda: mark_complete(task))
            ui.menu_item('View in Slack', on_click=lambda: open_slack(task))
            ui.separator()
            ui.menu_item('Copy context', on_click=lambda: copy_context(task))
            ui.menu_item('Export', on_click=lambda: export_task(task))

def mark_complete(task):
    ui.notify(f"Marked '{task['description']}' as complete")
    # Update database
    # Refresh display

def open_slack(task):
    # Open Slack URL
    pass

def copy_context(task):
    # Copy to clipboard
    ui.notify('Context copied to clipboard')

def export_task(task):
    # Export single task
    pass
```

---

### Example 3: Query History Sidebar

```python
from nicegui import ui, app

@ui.refreshable
def query_history():
    """Display recent queries with click to re-run."""
    history = app.storage.user.get('query_history', [])

    if not history:
        ui.label('No recent queries').classes('text-gray-500')
        return

    ui.label('Recent Queries').classes('font-bold mb-2')

    for query in reversed(history):
        with ui.row().classes('w-full items-center justify-between hover:bg-gray-100 dark:hover:bg-gray-800 p-2 rounded cursor-pointer'):
            ui.label(query['text']).on('click', lambda q=query: rerun_query(q))
            ui.label(query['date']).classes('text-sm text-gray-500')

def add_to_history(query_text):
    """Add query to history (max 10)."""
    history = app.storage.user.get('query_history', [])
    history.append({
        'text': query_text,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M')
    })
    app.storage.user['query_history'] = history[-10:]  # Keep last 10
    query_history.refresh()

def rerun_query(query):
    """Re-run a previous query."""
    query_input.value = query['text']
    handle_search()
```

---

### Example 4: Dark Mode Toggle

```python
from nicegui import ui, app

@ui.page('/')
def main():
    # Initialize dark mode
    dark = ui.dark_mode()

    # Load user preference
    if 'dark_mode' in app.storage.browser:
        if app.storage.browser['dark_mode']:
            dark.enable()
        else:
            dark.disable()

    # Header with dark mode toggle
    with ui.header().classes('items-center'):
        ui.label('Slack Insights').classes('text-xl')

        def toggle_dark():
            dark.toggle()
            app.storage.browser['dark_mode'] = dark.value

        ui.button(
            icon='dark_mode' if not dark.value else 'light_mode',
            on_click=toggle_dark
        ).props('flat')

    # Content with dark mode styling
    with ui.card().classes('bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700'):
        ui.label('Content').classes('text-slate-900 dark:text-slate-100')
```

---

## Reference Links

### Official Documentation
- **Main Documentation:** https://nicegui.io/documentation
- **Components:** https://nicegui.io/documentation/section_data_elements
- **Page Layout:** https://nicegui.io/documentation/section_page_layout
- **Styling:** https://nicegui.io/documentation/styling
- **Configuration & Deployment:** https://nicegui.io/documentation/section_configuration_deployment

### Component-Specific Docs
- **ui.input:** https://nicegui.io/documentation/input
- **ui.tree:** https://nicegui.io/documentation/tree
- **ui.expansion:** https://nicegui.io/documentation/expansion
- **ui.button:** https://nicegui.io/documentation/button
- **ui.label:** https://nicegui.io/documentation/label
- **ui.markdown:** https://nicegui.io/documentation/markdown
- **ui.context_menu:** https://nicegui.io/documentation/context_menu
- **ui.tooltip:** https://nicegui.io/documentation/tooltip
- **ui.keyboard:** https://nicegui.io/documentation/keyboard
- **ui.row:** https://nicegui.io/documentation/row
- **ui.column:** https://nicegui.io/documentation/column
- **ui.card:** https://nicegui.io/documentation/card
- **ui.grid:** https://nicegui.io/documentation/grid
- **ui.refreshable:** https://nicegui.io/documentation/refreshable
- **ui.download:** https://nicegui.io/documentation/download

### Examples & Tutorials
- **GitHub Repository:** https://github.com/zauberzeug/nicegui
- **SQLite Database Example:** https://github.com/zauberzeug/nicegui/blob/main/examples/sqlite_database/main.py
- **PyWebView Integration Gist:** https://gist.github.com/eli-kha/06a47bfdf1e50f4cdfc3f43a199a6d2d
- **DataCamp Tutorial:** https://www.datacamp.com/tutorial/nicegui

### Community Discussions
- **Tree Programmatic Control:** https://github.com/zauberzeug/nicegui/discussions/1230
- **Tree Population:** https://github.com/zauberzeug/nicegui/discussions/804
- **FastAPI Integration:** https://github.com/zauberzeug/nicegui/discussions/2223
- **Project Structure:** https://github.com/zauberzeug/nicegui/discussions/661
- **CSV Export:** https://github.com/zauberzeug/nicegui/discussions/3068

### Related Technologies
- **Quasar Framework:** https://quasar.dev/ (underlying UI framework)
- **FastAPI:** https://fastapi.tiangolo.com/ (backend framework)
- **Tailwind CSS:** https://tailwindcss.com/ (styling)
- **PyWebView:** https://pywebview.flowrl.com/ (desktop packaging)

---

## Summary

NiceGUI provides a Python-native approach to building modern web interfaces with minimal JavaScript knowledge required. Key strengths for the Slack Insights project:

1. **Tree/Expansion Components:** Perfect for hierarchical task grouping
2. **Event-Driven:** No full-page reruns, smooth interactions
3. **FastAPI Integration:** Seamless connection to existing backend
4. **Modern UI:** Quasar components provide professional appearance
5. **Desktop Packaging:** Can deploy as native app with PyWebView
6. **Privacy-First:** All data stays local, no cloud dependencies

**Recommended Implementation Path:**
1. Start with basic search interface using ui.input and ui.expansion
2. Integrate with existing database.py and deduplication.py modules
3. Add visual polish with Tailwind classes and dark mode
4. Implement nice-to-have features (query history, export)
5. Package as desktop app if needed

**Estimated Timeline:** 2-3 weeks for production-ready implementation per spec #3.
