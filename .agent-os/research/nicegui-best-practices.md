# NiceGUI Best Practices Research

> Research Date: 2025-10-10
> Sources: Official NiceGUI documentation, GitHub discussions, community examples
> Purpose: Guide production-ready NiceGUI application development

## Table of Contents

1. [Architecture Patterns](#architecture-patterns)
2. [Project Structure](#project-structure)
3. [UI/UX Best Practices](#uiux-best-practices)
4. [Performance Optimization](#performance-optimization)
5. [State Management](#state-management)
6. [Testing Strategies](#testing-strategies)
7. [Desktop App Deployment](#desktop-app-deployment)
8. [Common Pitfalls & Solutions](#common-pitfalls--solutions)

---

## Architecture Patterns

### FastAPI Integration

**Official Pattern** (from NiceGUI examples):

NiceGUI is built on FastAPI and integrates seamlessly using `ui.run_with()`:

```python
from fastapi import FastAPI
from nicegui import app as nicegui_app, ui

app = FastAPI()

@app.get('/api/data')
def read_data():
	return {'status': 'ok'}

@ui.page('/dashboard')
def dashboard():
	ui.label('Dashboard')

ui.run_with(
	app=app,
	storage_secret='pick_your_private_secret_here',
)
```

**Separation of Concerns Pattern:**

Create `frontend.py` with an `init()` function:

```python
# frontend.py
from nicegui import ui

def init(app: FastAPI) -> None:
	"""Initialize UI routes with FastAPI app reference"""

	@ui.page('/')
	def index():
		ui.label('Homepage')

	@ui.page('/settings')
	def settings():
		ui.label('Settings')
```

```python
# main.py
from fastapi import FastAPI
from nicegui import ui
import frontend

app = FastAPI()
frontend.init(app)

ui.run_with(app=app)
```

**Benefits:**
- Clear separation between API logic and UI code
- Easy to test backend independently
- Maintains single app instance for middleware/auth

**Sources:**
- [NiceGUI FastAPI Example](https://github.com/zauberzeug/nicegui/blob/main/examples/fastapi/)
- [GitHub Discussion #2223](https://github.com/zauberzeug/nicegui/discussions/2223)

---

## Project Structure

### Recommended Directory Layout

Based on the [official NiceGUI template](https://github.com/zauberzeug/nicegui-template):

```
project_root/
├── .github/
│   └── workflows/          # CI/CD pipelines
├── .vscode/                # Editor settings
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── conftest.py        # Pytest fixtures
│   └── test_ui.py
├── src/                   # Application code
│   ├── __init__.py
│   ├── main.py           # Entry point
│   ├── pages/            # Page definitions
│   │   ├── __init__.py
│   │   ├── home.py
│   │   └── settings.py
│   ├── components/       # Reusable UI components
│   │   ├── __init__.py
│   │   ├── header.py
│   │   └── sidebar.py
│   └── utils/           # Helper functions
│       ├── __init__.py
│       └── theme.py
├── .env.example         # Environment template
├── .gitignore
├── .pylintrc           # Linting config
├── mypy.ini            # Type checking config
├── pytest.ini          # Test config
├── ruff.toml           # Formatting config
├── requirements.txt    # Dependencies
├── requirements-locked.txt
└── README.md
```

### Four Modularization Patterns

The [official modularization example](https://github.com/zauberzeug/nicegui/tree/main/examples/modularization) demonstrates four approaches:

#### 1. Custom Page Decorator with Separate Content

```python
# main.py
@ui.page('/')
def index_page() -> None:
	with theme.frame('Homepage'):
		home_page.content()

# home_page.py
from nicegui import ui

def content() -> None:
	ui.label('Welcome to homepage')
	ui.button('Click me')
```

**Use when:** Simple pages with shared layout/theme

#### 2. Function-Based Pages

```python
# function_example.py
from nicegui import ui

def create() -> None:
	@ui.page('/example')
	def page():
		ui.label('Function-based page')

# main.py
import function_example
function_example.create()
```

**Use when:** Organizing pages into separate modules

#### 3. Class-Based Pages

```python
# class_example.py
from nicegui import ui

class DashboardPage:
	def __init__(self) -> None:
		@ui.page('/dashboard')
		def page():
			with theme.frame('Dashboard'):
				self._render_content()

	def _render_content(self) -> None:
		ui.label('Dashboard content')
		ui.table(...)

# main.py
import class_example
class_example.DashboardPage()
```

**Use when:** Pages need internal state or complex logic

#### 4. APIRouter for Sub-Modules

```python
# api_router_example.py
from nicegui import APIRouter, ui

router = APIRouter(prefix='/admin')

@router.page('/users')
def users():
	ui.label('User management')

@router.page('/settings')
def settings():
	ui.label('Admin settings')

# main.py
from nicegui import app
import api_router_example

app.include_router(api_router_example.router)
```

**Use when:** Grouping related pages with common prefix

**Sources:**
- [NiceGUI Modularization Example](https://github.com/zauberzeug/nicegui/tree/main/examples/modularization)
- [GitHub Discussion #661](https://github.com/zauberzeug/nicegui/discussions/661)
- [Official Documentation - APIRouter](https://nicegui.io/documentation/page#modularize_with_apirouter)

### Component Organization Pattern

**Inherit from NiceGUI Classes:**

```python
# components/header.py
from nicegui import ui

class AppHeader(ui.header):
	def __init__(self, title: str):
		super().__init__()
		with self:
			ui.label(title).classes('text-h6')
			ui.space()
			self._create_menu()

	def _create_menu(self) -> None:
		with ui.row():
			ui.button('Home', on_click=lambda: ui.navigate.to('/'))
			ui.button('Settings', on_click=lambda: ui.navigate.to('/settings'))

# Usage
@ui.page('/')
def index():
	AppHeader('My Application')
	ui.label('Page content')
```

**Benefits:**
- Encapsulates component logic
- Reusable across pages
- Maintains NiceGUI's API
- Easier to test

**Source:** [GitHub Discussion #661](https://github.com/zauberzeug/nicegui/discussions/661)

---

## UI/UX Best Practices

### Hierarchical Data Display

NiceGUI provides three main components for hierarchical data:

#### 1. ui.tree

```python
from nicegui import ui

tree_data = [
	{
		'id': 'channels',
		'label': 'Channels',
		'children': [
			{'id': 'general', 'label': '#general'},
			{'id': 'random', 'label': '#random'},
		],
	},
	{
		'id': 'dms',
		'label': 'Direct Messages',
		'children': [
			{'id': 'dan', 'label': 'Dan Smith'},
		],
	},
]

tree = ui.tree(tree_data, label_key='label')
tree.on('tick', lambda e: print(f'Selected: {e.args}'))
```

**Best Practices:**
- Use for 300+ nodes across 5+ levels
- Add filter box for large trees
- Store tree state for user preferences
- Consider lazy loading for very deep trees

**Limitations:**
- Nodes don't auto-expand when selected (unlike Quasar QTree)
- Need custom wrapper for dynamic node addition

**Source:** [NiceGUI Tree Documentation](https://nicegui.io/documentation/tree), [GitHub Discussion #1924](https://github.com/zauberzeug/nicegui/discussions/1924)

#### 2. ui.expansion

```python
from nicegui import ui

with ui.expansion('Action Items', icon='task').classes('w-full'):
	ui.label('Task 1: Review PR #123')
	ui.label('Task 2: Update documentation')

with ui.expansion('Completed', icon='check_circle'):
	ui.label('Task 3: Fixed bug')
```

**Use when:**
- Organizing content into collapsible sections
- Building FAQ pages
- Grouping related information

**Source:** [NiceGUI Expansion Documentation](https://nicegui.io/documentation/expansion)

#### 3. AGGrid for Nested Data

```python
from nicegui import ui

grid = ui.aggrid({
	'columnDefs': [
		{'field': 'channel', 'rowGroup': True, 'hide': True},
		{'field': 'user', 'headerName': 'User'},
		{'field': 'message', 'headerName': 'Message'},
	],
	'rowData': [
		{'channel': 'general', 'user': 'Dan', 'message': 'Hello'},
		{'channel': 'general', 'user': 'Sarah', 'message': 'Hi'},
		{'channel': 'random', 'user': 'Dan', 'message': 'Question?'},
	],
	'defaultColDef': {'flex': 1},
})
```

**Benefits:**
- Built-in grouping and aggregation
- Row virtualization for performance
- Pagination support
- Filtering and sorting

**Source:** [NiceGUI AGGrid Documentation](https://nicegui.io/documentation/aggrid)

### Query Input Design

**Natural Language Interface Pattern:**

```python
from nicegui import ui

class QueryInterface:
	def __init__(self):
		self.query_input = None
		self.results_container = None
		self._setup_ui()

	def _setup_ui(self) -> None:
		with ui.column().classes('w-full max-w-4xl'):
			ui.label('Ask a question about your data').classes('text-h5')

			self.query_input = ui.input(
				'What did Dan ask me to do?',
				placeholder='Type your question...',
			).classes('w-full').on('keydown.enter', self._handle_query)

			with ui.row():
				ui.button('Search', icon='search', on_click=self._handle_query)
				ui.button('Clear', icon='clear', on_click=self._clear_results)

			self.results_container = ui.column().classes('w-full')

	async def _handle_query(self) -> None:
		query_text = self.query_input.value
		if not query_text:
			return

		self.results_container.clear()
		with self.results_container:
			with ui.card().classes('w-full'):
				ui.spinner(size='lg')
				ui.label('Processing query...')

		# Simulate async query
		await asyncio.sleep(1)

		# Display results
		self._display_results(query_text)

	def _display_results(self, query: str) -> None:
		self.results_container.clear()
		with self.results_container:
			ui.label('Results').classes('text-h6')
			# Display results here
```

**Best Practices:**
- Provide example queries as placeholders
- Show loading state immediately
- Clear previous results before new search
- Enable Enter key for submission

### Loading States & Progress Indicators

NiceGUI provides three progress components:

```python
from nicegui import ui
import asyncio

async def long_operation():
	# 1. Linear progress bar
	progress = ui.linear_progress(value=0).props('instant-feedback')

	for i in range(100):
		await asyncio.sleep(0.05)
		progress.value = (i + 1) / 100

	progress.delete()
	ui.notify('Complete!', type='positive')

# 2. Circular progress
with ui.card():
	ui.circular_progress(size='xl')
	ui.label('Loading...')

# 3. Spinner (indeterminate)
ui.spinner(size='lg', color='primary')
```

**Pattern for Long Page Loads:**

```python
@ui.page('/dashboard')
async def dashboard():
	# Show skeleton immediately
	with ui.card().classes('w-full') as loading_card:
		ui.skeleton().props('type=rect height=200px')
		ui.label('Loading dashboard...').classes('text-center')

	# Fetch data in background (after websocket connected)
	async def load_data():
		await asyncio.sleep(1)  # Simulate API call

		# Remove skeleton
		loading_card.delete()

		# Show actual content
		with ui.card().classes('w-full'):
			ui.label('Dashboard').classes('text-h4')
			ui.chart(...)  # Your actual content

	# Schedule background load
	ui.timer(0.1, load_data, once=True)
```

**Key Principles:**
- Use `ui.skeleton()` for immediate placeholder
- Schedule data loading with `ui.timer(0.1, callback, once=True)`
- Allow websocket to connect before heavy operations
- Use `run.cpu_bound()` for heavy computation with progress updates

**Sources:**
- [NiceGUI Progress Example](https://github.com/zauberzeug/nicegui/blob/main/examples/progress/main.py)
- [GitHub Discussion #2729](https://github.com/zauberzeug/nicegui/discussions/2729)
- [GitHub Discussion #3477](https://github.com/zauberzeug/nicegui/discussions/3477)

### Error Handling & User Feedback

**Notification System:**

```python
from nicegui import ui

# Success notification
ui.notify('Changes saved', type='positive')

# Warning
ui.notify('Connection slow', type='warning')

# Error
ui.notify('Failed to load data', type='negative', close_button=True)

# Persistent notification
notification = ui.notify('Processing...', type='info', timeout=None)
# Later: notification.dismiss()
```

**Client Context for Background Tasks:**

```python
from nicegui import ui, Client
import asyncio

@ui.page('/')
def index():
	button = ui.button('Start Task')

	async def background_task(client: Client):
		"""Background task with proper client context"""
		try:
			await asyncio.sleep(2)  # Simulate work

			# Must set client context to show notification
			with client:
				ui.notify('Task complete!', type='positive')
		except Exception as e:
			with client:
				ui.notify(f'Error: {str(e)}', type='negative')

	def start_task():
		# Get current client reference
		client = ui.context.client
		# Run in background with client reference
		asyncio.create_task(background_task(client))

	button.on_click(start_task)
```

**Best Practices:**
- Catch exceptions in page functions for UI-related errors
- Use global exception handler for logging (outside UI context)
- Always set client context when notifying from background tasks
- Provide clear error messages with suggested actions

**Source:** [GitHub Discussion #2026](https://github.com/zauberzeug/nicegui/discussions/2026)

---

## Performance Optimization

### Handling Large Datasets

**Problem:** Displaying 2000+ UI elements with live binding causes performance issues.

**Solutions:**

#### 1. Use AGGrid with Pagination

```python
from nicegui import ui

# AGGrid handles large datasets efficiently
grid = ui.aggrid({
	'columnDefs': [
		{'field': 'timestamp', 'headerName': 'Time'},
		{'field': 'user', 'headerName': 'User'},
		{'field': 'message', 'headerName': 'Message'},
	],
	'rowData': large_dataset,  # Can handle 10K+ rows
	'pagination': True,
	'paginationPageSize': 50,
	'defaultColDef': {'sortable': True, 'filter': True},
})
```

**Benefits:**
- Row virtualization (only visible rows rendered)
- Built-in pagination
- Fast sorting/filtering
- Excel-like features

#### 2. Split Data with Tabs

```python
from nicegui import ui

with ui.tabs() as tabs:
	ui.tab('Recent', icon='schedule')
	ui.tab('This Week', icon='date_range')
	ui.tab('All Time', icon='history')

with ui.tab_panels(tabs).classes('w-full'):
	with ui.tab_panel('Recent'):
		# Show only last 100 items
		ui.table(...)

	with ui.tab_panel('This Week'):
		# Load on demand
		pass
```

#### 3. Avoid ui.refreshable for Large UIs

**Anti-Pattern:**

```python
# BAD: Destroys and recreates all elements
@ui.refreshable
def render_messages():
	for msg in messages:  # 1000+ messages
		ui.label(msg)

render_messages()
# Later: render_messages.refresh()  # Very slow!
```

**Better Pattern:**

```python
# GOOD: Update individual elements
class MessageList:
	def __init__(self):
		self.container = ui.column()
		self.message_labels = {}

	def add_message(self, msg_id: str, text: str):
		with self.container:
			label = ui.label(text)
			self.message_labels[msg_id] = label

	def update_message(self, msg_id: str, text: str):
		if msg_id in self.message_labels:
			self.message_labels[msg_id].text = text

	def remove_message(self, msg_id: str):
		if msg_id in self.message_labels:
			self.message_labels[msg_id].delete()
			del self.message_labels[msg_id]
```

**Sources:**
- [GitHub Discussion #2876](https://github.com/zauberzeug/nicegui/discussions/2876)
- [NiceGUI AGGrid Documentation](https://nicegui.io/documentation/aggrid)

### Optimal Update Patterns

**Avoid Full Refreshes:**

The `@ui.refreshable` decorator destroys and recreates elements every time, which is inefficient for real-world apps.

**Alternatives:**

1. **Data Binding:**

```python
from nicegui import ui

class Dashboard:
	def __init__(self):
		self.data = {'count': 0}

	def render(self):
		# Bind label to data
		ui.label().bind_text_from(self.data, 'count')

		# Updates automatically
		ui.button('Increment', on_click=lambda: self._increment())

	def _increment(self):
		self.data['count'] += 1
```

2. **Element Visibility Toggle:**

```python
# Show/hide elements instead of recreating
class ConditionalView:
	def __init__(self):
		self.loading_card = None
		self.content_card = None
		self._setup_ui()

	def _setup_ui(self):
		self.loading_card = ui.card().classes('w-full')
		with self.loading_card:
			ui.spinner()

		self.content_card = ui.card().classes('w-full hidden')
		with self.content_card:
			ui.label('Loaded content')

	def show_content(self):
		self.loading_card.classes(add='hidden')
		self.content_card.classes(remove='hidden')
```

3. **Incremental Updates:**

```python
# Add new items without refreshing existing ones
class IncrementalList:
	def __init__(self):
		self.container = ui.column()

	def append_item(self, text: str):
		with self.container:
			ui.label(text)
```

**When to Use ui.refreshable:**

- Simple components with few elements
- Periodic updates with `ui.timer()`
- Components that need complete re-rendering logic

**Sources:**
- [GitHub Discussion #2772](https://github.com/zauberzeug/nicegui/discussions/2772)
- [NiceGUI Refreshable Documentation](https://nicegui.io/documentation/refreshable)

### Async Operations Best Practices

**Use run_in_executor for Long Tasks:**

```python
from nicegui import ui, run
import asyncio

@ui.page('/')
def index():
	async def process_data():
		# CPU-bound work
		result = await run.cpu_bound(expensive_calculation)
		ui.notify(f'Result: {result}')

	ui.button('Process', on_click=process_data)

def expensive_calculation():
	# Heavy computation here
	return sum(range(10000000))
```

**Progress Updates from Background Tasks:**

```python
from nicegui import ui, run
import asyncio
from queue import Queue

@ui.page('/')
def index():
	progress = ui.linear_progress(value=0)

	async def heavy_work():
		queue = Queue()

		def work_with_progress():
			for i in range(100):
				# Simulate work
				time.sleep(0.1)
				queue.put(i + 1)
			return 'Done'

		# Start work in background
		task = run.cpu_bound(work_with_progress)

		# Update progress
		while not task.done():
			try:
				current = queue.get_nowait()
				progress.value = current / 100
			except:
				pass
			await asyncio.sleep(0.1)

		result = await task
		ui.notify(result)

	ui.button('Start', on_click=heavy_work)
```

**Source:** [NiceGUI Progress Example](https://github.com/zauberzeug/nicegui/blob/main/examples/progress/main.py)

### Memory Management

**Known Issues:**

1. **BindableProperty Memory Leaks:**
   - BindableProperty holds long-term references to objects
   - Elements reference Props objects which reference elements back (circular refs)
   - Can cause memory exhaustion in long-running SPAs

2. **Connection Cleanup:**
   - Low timeout → rapid connection purge but frequent GC (200ms)
   - High timeout → many connections in memory, slow GC (seconds)

**Mitigation Strategies:**

```python
from nicegui import ui

# 1. Explicitly delete unused elements
class DynamicContent:
	def __init__(self):
		self.current_view = None

	def switch_view(self, new_view_fn):
		# Delete old view before creating new one
		if self.current_view:
			self.current_view.delete()

		self.current_view = new_view_fn()

# 2. Use context managers for temporary UI
async def show_temporary_dialog():
	with ui.dialog() as dialog:
		with ui.card():
			ui.label('Temporary content')
			ui.button('Close', on_click=dialog.close)

	await dialog
	# Dialog automatically cleaned up when closed

# 3. Clear storage on startup (for testing)
from nicegui import app

# In main.py
app.on_startup(lambda: app.storage.clear())
```

**Recommendations:**
- Monitor memory usage in production
- Implement periodic cleanup for long-running sessions
- Avoid holding references to deleted elements
- Consider SPA mode carefully for memory-sensitive apps

**Sources:**
- [GitHub Issue #4521](https://github.com/zauberzeug/nicegui/issues/4521)
- [GitHub Issue #727](https://github.com/zauberzeug/nicegui/issues/727)
- [GitHub Discussion #991](https://github.com/zauberzeug/nicegui/discussions/991)

---

## State Management

### Reactive Data Binding

NiceGUI provides built-in two-way binding for UI elements:

```python
from nicegui import ui

class ViewModel:
	def __init__(self):
		self.name = ''
		self.age = 0
		self.is_active = False

vm = ViewModel()

# Two-way binding
ui.input('Name').bind_value(vm, 'name')
ui.number('Age').bind_value(vm, 'age')
ui.checkbox('Active').bind_value(vm, 'is_active')

# One-way binding (from model to UI)
ui.label().bind_text_from(vm, 'name')

# One-way binding (from UI to model)
ui.input().bind_value_to(vm, 'name')

# Computed binding
ui.label().bind_text_from(vm, 'age', lambda x: f'{x} years old')
```

**Binding Nested Properties:**

```python
class Config:
	def __init__(self):
		self.settings = {
			'theme': 'dark',
			'notifications': True,
		}

config = Config()

# Bind to nested dict
ui.select(
	options=['light', 'dark'],
	value='dark',
).bind_value(config.settings, 'theme')
```

**Source:** [NiceGUI Binding Documentation](https://nicegui.io/documentation/section_binding_properties)

### Global Store Pattern

For applications with shared state across pages:

```python
# store.py
from dataclasses import dataclass
from typing import Dict, List, Callable

@dataclass
class ActionItem:
	id: str
	description: str
	assignee: str
	status: str

class AppStore:
	"""Central data store with observer pattern"""

	def __init__(self):
		self._action_items: Dict[str, ActionItem] = {}
		self._observers: List[Callable] = []

	def add_item(self, item: ActionItem) -> None:
		self._action_items[item.id] = item
		self._notify_observers()

	def update_item(self, item_id: str, **kwargs) -> None:
		if item_id in self._action_items:
			item = self._action_items[item_id]
			for key, value in kwargs.items():
				setattr(item, key, value)
			self._notify_observers()

	def get_items(self) -> List[ActionItem]:
		return list(self._action_items.values())

	def subscribe(self, callback: Callable) -> None:
		self._observers.append(callback)

	def _notify_observers(self) -> None:
		for callback in self._observers:
			callback()

# Global store instance
store = AppStore()
```

```python
# Usage in pages
from nicegui import ui
from store import store

@ui.page('/')
def index():
	container = ui.column()

	def render_items():
		container.clear()
		with container:
			for item in store.get_items():
				ui.label(f'{item.description} - {item.status}')

	# Subscribe to store changes
	store.subscribe(render_items)

	# Initial render
	render_items()

	# Add new item
	ui.button('Add Item', on_click=lambda: store.add_item(...))
```

**Source:** [GitHub Discussion #1029](https://github.com/zauberzeug/nicegui/discussions/1029)

### Per-User State with Storage

NiceGUI provides three storage scopes:

```python
from nicegui import ui, app

@ui.page('/')
def index():
	# 1. Client storage (browser-specific, persists across sessions)
	client_prefs = app.storage.client.get('preferences', {})

	# 2. User storage (user-specific, persists across browsers)
	user_data = app.storage.user.get('profile', {})

	# 3. General storage (global, shared across all users)
	global_config = app.storage.general.get('config', {})

	# Save changes
	app.storage.client['preferences'] = {'theme': 'dark'}
	app.storage.user['profile'] = {'name': 'Dale'}
```

**Best Practices:**
- Use client storage for UI preferences (theme, layout)
- Use user storage for user-specific data (settings, history)
- Use general storage for app-wide configuration
- Set `storage_secret` in `ui.run()` to encrypt data

**Source:** [NiceGUI Storage Documentation](https://nicegui.io/documentation/storage)

### Multi-User Sessions

**Pattern for Per-User UI State:**

```python
from nicegui import ui

# Move refreshable OUT of page function
@ui.refreshable
def user_specific_content(user_id: str):
	# Fetch user-specific data
	data = get_user_data(user_id)
	ui.label(f'Welcome, {data["name"]}')
	ui.table(data['items'])

@ui.page('/dashboard')
def dashboard():
	# Each user gets their own instance
	user_id = get_current_user_id()
	user_specific_content(user_id)
```

**Source:** Chat app example in NiceGUI repository

---

## Testing Strategies

### NiceGUI Testing with Pytest

NiceGUI includes official pytest plugins for testing:

**Setup (`conftest.py`):**

```python
# conftest.py
import pytest
from nicegui import ui

# Enable NiceGUI pytest plugin
pytest_plugins = ['nicegui.testing.user_plugin']

@pytest.fixture
async def user(user):
	"""Configure user fixture with your app"""
	# Setup runs before each test
	yield user
	# Teardown runs after each test
```

**Test Configuration (`pytest.ini`):**

```ini
[pytest]
asyncio_mode = auto
main_file = main.py  # Entry point for your app
```

### Two Testing Approaches

#### 1. User Fixture (Recommended)

**Fast, lightweight simulation without browser:**

```python
# test_ui.py
import pytest
from nicegui import ui
from nicegui.testing import User

@pytest.mark.asyncio
async def test_query_interface(user: User) -> None:
	# Build UI
	@ui.page('/')
	def index():
		ui.input(placeholder='Enter query').classes('query-input')
		ui.button('Search', icon='search').classes('search-btn')
		ui.column().classes('results')

	# Open page
	await user.open('/')

	# Interact with UI
	user.find('query-input').type('what did Dan ask me?')
	user.find('search-btn').click()

	# Assert results
	results = user.find('results')
	assert results.text != ''

@pytest.mark.asyncio
async def test_action_items_display(user: User) -> None:
	@ui.page('/items')
	def items_page():
		with ui.column():
			ui.label('Action Items').classes('header')
			ui.label('Task 1').classes('task')
			ui.label('Task 2').classes('task')

	await user.open('/items')

	# Find elements
	assert user.find('header').text == 'Action Items'
	tasks = user.find_all('.task')
	assert len(tasks) == 2
```

**User Fixture Methods:**
- `user.open(path)` - Navigate to page
- `user.find(selector)` - Find single element by class/id
- `user.find_all(selector)` - Find multiple elements
- `element.click()` - Simulate click
- `element.type(text)` - Type text into input
- `element.text` - Get element text
- `element.value` - Get input value

#### 2. Screen Fixture

**Tests through headless browser (slower but more realistic):**

```python
import pytest
from nicegui.testing import Screen

pytest_plugins = ['nicegui.testing.screen_plugin']

@pytest.mark.asyncio
async def test_with_browser(screen: Screen) -> None:
	# Same API as user fixture
	await screen.open('/')
	screen.find('.search-btn').click()
```

**When to use:**
- JavaScript-heavy interactions
- Testing browser-specific behavior
- Visual regression testing

### Testing Best Practices

**1. Test Component Classes Directly:**

```python
# components/query_box.py
from nicegui import ui

class QueryBox:
	def __init__(self):
		self.input = ui.input('Query')
		self.results = []

	def search(self, query: str):
		# Search logic
		self.results = ['result1', 'result2']
		return self.results

# test_query_box.py
import pytest
from components.query_box import QueryBox

def test_query_box_search():
	qb = QueryBox()
	results = qb.search('test query')
	assert len(results) == 2
```

**2. Mock External Dependencies:**

```python
import pytest
from unittest.mock import AsyncMock, patch
from nicegui.testing import User

@pytest.mark.asyncio
async def test_api_call(user: User):
	@ui.page('/')
	def index():
		async def fetch_data():
			data = await api.get_action_items()
			ui.label(f'Found {len(data)} items')

		ui.button('Fetch', on_click=fetch_data)

	await user.open('/')

	# Mock API call
	with patch('api.get_action_items', new=AsyncMock(return_value=[1, 2, 3])):
		user.find('Fetch').click()
		await asyncio.sleep(0.1)  # Wait for async operation

		assert 'Found 3 items' in user.find('body').text
```

**3. Test User Interactions:**

```python
@pytest.mark.asyncio
async def test_form_submission(user: User):
	@ui.page('/form')
	def form_page():
		submitted = {'value': None}

		def handle_submit():
			submitted['value'] = text_input.value
			ui.notify('Submitted!')

		text_input = ui.input('Name').classes('name-input')
		ui.button('Submit', on_click=handle_submit).classes('submit-btn')

	await user.open('/form')

	# Fill form
	user.find('.name-input').type('Dale')

	# Submit
	user.find('.submit-btn').click()

	# Verify notification
	# (User fixture captures notifications)
```

**Sources:**
- [NiceGUI Testing Documentation](https://nicegui.io/documentation/section_testing)
- [Stack Overflow - Testing NiceGUI](https://stackoverflow.com/questions/79443748/how-to-properly-test-nicegui-applications-with-pytest)

---

## Desktop App Deployment

### PyWebView Integration

NiceGUI can create native desktop applications using PyWebView:

**Installation:**

```bash
pip install nicegui[native]
# or
pip install nicegui pywebview
```

**Basic Desktop App:**

```python
# main.py
from nicegui import ui
import webview

@ui.page('/')
def index():
	ui.label('Desktop App')
	ui.button('Click me')

if __name__ == '__main__':
	# Start NiceGUI without browser
	from threading import Thread
	thread = Thread(target=lambda: ui.run(
		port=8080,
		show=False,  # Don't open browser
		reload=False,
	))
	thread.daemon = True
	thread.start()

	# Create native window
	webview.create_window(
		'My App',
		'http://localhost:8080',
		width=1200,
		height=800,
	)
	webview.start()
```

**Advanced Pattern with Process Wrapping:**

```python
import multiprocessing
from nicegui import ui
import webview

def start_nicegui():
	"""Run NiceGUI in separate process"""
	@ui.page('/')
	def index():
		ui.label('Desktop App')

	ui.run(port=8080, show=False)

def start_window():
	"""Create PyWebView window"""
	webview.create_window('My App', 'http://localhost:8080')
	webview.start()

if __name__ == '__main__':
	# Start both processes
	nicegui_process = multiprocessing.Process(target=start_nicegui)
	nicegui_process.start()

	# Wait for server to start
	import time
	time.sleep(1)

	# Start window
	start_window()

	# Cleanup
	nicegui_process.terminate()
```

**Packaging with PyInstaller:**

```bash
# Install PyInstaller
pip install pyinstaller

# Create executable
pyinstaller --onefile \
	--windowed \
	--add-data "static:static" \
	--hidden-import nicegui \
	main.py
```

**Sources:**
- [GitHub Gist - PyWebView Integration](https://gist.github.com/eli-kha/06a47bfdf1e50f4cdfc3f43a199a6d2d)
- [GitHub Issue #1069](https://github.com/r0x0r/pywebview/issues/1069)
- [NiceGUI Configuration Documentation](https://nicegui.io/documentation/section_configuration_deployment)

### Desktop App Best Practices

**1. Local Storage:**

```python
from nicegui import ui, app
from pathlib import Path

# Use local directory for data
DATA_DIR = Path.home() / '.my-app'
DATA_DIR.mkdir(exist_ok=True)

# Configure storage
ui.run(
	storage_secret='your-secret',
	# Use file-based storage
)
```

**2. System Tray Integration:**

```python
import pystray
from PIL import Image
import threading

def create_tray_icon():
	icon_image = Image.open('icon.png')

	def on_quit(icon, item):
		icon.stop()
		# Stop NiceGUI server

	menu = pystray.Menu(
		pystray.MenuItem('Open', lambda: webview.windows[0].show()),
		pystray.MenuItem('Quit', on_quit),
	)

	icon = pystray.Icon('my_app', icon_image, 'My App', menu)
	icon.run()

# Run in thread
threading.Thread(target=create_tray_icon, daemon=True).start()
```

**3. Auto-Start on Boot:**

```python
# Linux: Create .desktop file in ~/.config/autostart/
# macOS: Create Launch Agent plist
# Windows: Add to Startup folder or registry
```

---

## Common Pitfalls & Solutions

### 1. UI Context Issues

**Problem:** Calling `ui.notify()` from background tasks fails

```python
# BAD
async def background_task():
	await asyncio.sleep(2)
	ui.notify('Done')  # ERROR: No client context!
```

**Solution:** Pass and use client reference

```python
# GOOD
from nicegui import ui, Client

@ui.page('/')
def index():
	async def background_task(client: Client):
		await asyncio.sleep(2)
		with client:
			ui.notify('Done')

	def start():
		client = ui.context.client
		asyncio.create_task(background_task(client))

	ui.button('Start', on_click=start)
```

### 2. Refreshable State Sharing

**Problem:** Multiple instances share state

```python
# BAD
@ui.refreshable
def counter():
	count = 0  # Shared across all users!
	ui.label(count)

@ui.page('/')
def index():
	counter()
```

**Solution:** Use class-based approach

```python
# GOOD
class Counter:
	def __init__(self):
		self.count = 0
		self.render()

	@ui.refreshable
	def render(self):
		ui.label(self.count)
		ui.button('Increment', on_click=self.increment)

	def increment(self):
		self.count += 1
		self.render.refresh()

@ui.page('/')
def index():
	Counter()  # Each user gets their own instance
```

### 3. Async Operations Blocking UI

**Problem:** Long-running sync code blocks UI

```python
# BAD
def process_data():
	time.sleep(5)  # Blocks event loop!
	return result

ui.button('Process', on_click=lambda: process_data())
```

**Solution:** Use run.cpu_bound or run.io_bound

```python
# GOOD
from nicegui import ui, run

async def process_data():
	result = await run.cpu_bound(expensive_calculation)
	ui.notify(f'Result: {result}')

ui.button('Process', on_click=process_data)
```

### 4. Memory Leaks from Bindings

**Problem:** BindableProperty holds long-term references

**Solution:** Explicitly delete unused elements

```python
class DynamicView:
	def __init__(self):
		self.current_elements = []

	def update_view(self, new_data):
		# Delete old elements
		for element in self.current_elements:
			element.delete()
		self.current_elements.clear()

		# Create new elements
		for item in new_data:
			elem = ui.label(item)
			self.current_elements.append(elem)
```

### 5. Keyboard Shortcuts Conflicts

**Problem:** Custom shortcuts conflict with browser/screen reader

**Solution:** Follow ARIA guidelines

```python
from nicegui import ui

@ui.page('/')
def index():
	# Good: Use meta key modifiers
	ui.keyboard(
		lambda e: handle_search() if e.key == 's' and e.modifiers.ctrl else None
	)

	# Bad: Single letter shortcuts
	# ui.keyboard(lambda e: handle_search() if e.key == 's' else None)

	# Provide visible shortcuts list
	with ui.dialog() as shortcuts_dialog:
		ui.label('Keyboard Shortcuts').classes('text-h6')
		ui.label('Ctrl+S - Search')
		ui.label('Ctrl+N - New Item')

	ui.button('Shortcuts', icon='keyboard', on_click=shortcuts_dialog.open)
```

---

## Additional Resources

### Official Documentation
- [NiceGUI Official Docs](https://nicegui.io/documentation)
- [NiceGUI GitHub Repository](https://github.com/zauberzeug/nicegui)
- [NiceGUI Examples](https://github.com/zauberzeug/nicegui/tree/main/examples)

### Community Examples
- [RoSys Robotics Framework](https://github.com/zauberzeug/rosys) - Large-scale NiceGUI application
- [NiceGUI Template](https://github.com/zauberzeug/nicegui-template) - Official project template
- [Community Projects Wiki](https://github.com/zauberzeug/nicegui/wiki) - User-contributed examples

### Key GitHub Discussions
- [Code Organization #661](https://github.com/zauberzeug/nicegui/discussions/661)
- [Multi-route Structure #858](https://github.com/zauberzeug/nicegui/discussions/858)
- [State Management #1029](https://github.com/zauberzeug/nicegui/discussions/1029)
- [Performance #2876](https://github.com/zauberzeug/nicegui/discussions/2876)
- [Loading States #2729](https://github.com/zauberzeug/nicegui/discussions/2729)

### Testing & Quality
- [Official Testing Docs](https://nicegui.io/documentation/section_testing)
- [Pytest Examples](https://github.com/zauberzeug/nicegui/tree/main/examples/pytests)

---

## Recommendations for Slack Insights NiceGUI Interface

Based on this research, here are specific recommendations for the Slack Insights project:

### 1. Project Structure

```
src/
├── main.py              # Entry point with ui.run()
├── pages/
│   ├── __init__.py
│   ├── home.py         # Main query interface
│   └── settings.py     # Configuration
├── components/
│   ├── __init__.py
│   ├── query_box.py    # Natural language query input
│   ├── results_tree.py # Hierarchical results display
│   └── action_card.py  # Individual action item card
├── store/
│   ├── __init__.py
│   └── app_store.py    # Global state management
└── utils/
	├── __init__.py
	└── theme.py        # Shared theme/layout
```

### 2. Use AGGrid for Results

Display action items in AGGrid with grouping:

```python
grid = ui.aggrid({
	'columnDefs': [
		{'field': 'channel', 'rowGroup': True, 'hide': True},
		{'field': 'person', 'headerName': 'Person'},
		{'field': 'task', 'headerName': 'Task'},
		{'field': 'date', 'headerName': 'Date'},
		{'field': 'status', 'headerName': 'Status'},
	],
	'pagination': True,
	'paginationPageSize': 50,
})
```

### 3. Loading States for AI Queries

Show progress while Claude processes queries:

```python
async def handle_query(query: str):
	results_container.clear()
	with results_container:
		ui.spinner(size='lg')
		ui.label('Analyzing conversations...')

	# Call Claude API
	results = await run.io_bound(lambda: query_engine.search(query))

	# Display results
	display_results(results)
```

### 4. Desktop Mode

Package as native app with PyWebView for "local-first" feel.

### 5. Testing Strategy

Use pytest with `user` fixture for fast UI tests:

```python
async def test_query_interface(user: User):
	await user.open('/')
	user.find('.query-input').type('what did Dan ask me?')
	user.find('.search-btn').click()
	# Assert results displayed
```

---

*End of Research Document*
