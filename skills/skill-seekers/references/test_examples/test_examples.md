# Test Example Extraction Report

**Total Examples**: 599  
**High Value Examples** (confidence > 0.7): 599  
**Average Complexity**: 0.31  

## Examples by Category

- **config**: 10
- **instantiation**: 257
- **method_call**: 293
- **workflow**: 39

## Examples by Language

- **Python**: 599

## Extracted Examples

### test_analyze_python_workflow

**Category**: workflow  
**Description**: Workflow: Test analysis of Python workflow with multiple steps  
**Expected**: self.assertIn(metadata['complexity_level'], ['beginner', 'intermediate', 'advanced'])  
**Confidence**: 0.90  
**Tags**: unittest, workflow, integration  

```python
# Setup
self.analyzer = WorkflowAnalyzer()

'Test analysis of Python workflow with multiple steps'
workflow = {'code': "\ndef test_user_creation_workflow():\n    # Step 1: Create database\n    db = Database('test.db')\n\n    # Step 2: Create user\n    user = User(name='Alice', email='alice@example.com')\n    db.save(user)\n\n    # Step 3: Verify creation\n    assert db.get_user('Alice').email == 'alice@example.com'\n", 'language': 'python', 'category': 'workflow', 'test_name': 'test_user_creation_workflow', 'file_path': 'tests/test_user.py'}
steps, metadata = self.analyzer.analyze_workflow(workflow)
self.assertGreaterEqual(len(steps), 2)
self.assertIsInstance(steps[0], WorkflowStep)
self.assertEqual(steps[0].step_number, 1)
self.assertIsNotNone(steps[0].description)
self.assertIn('complexity_level', metadata)
self.assertIn(metadata['complexity_level'], ['beginner', 'intermediate', 'advanced'])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_how_to_guide_builder.py:42*

### test_extract_workflow_examples

**Category**: workflow  
**Description**: Workflow: Test extraction of workflow examples from mixed examples  
**Expected**: self.assertEqual(workflows[0]['category'], 'workflow')  
**Confidence**: 0.90  
**Tags**: unittest, workflow, integration  

```python
# Setup
self.builder = HowToGuideBuilder(enhance_with_ai=False)
self.temp_dir = tempfile.mkdtemp()

'Test extraction of workflow examples from mixed examples'
examples = [{'category': 'workflow', 'code': 'db = Database()\nuser = User()\ndb.save(user)', 'test_name': 'test_user_workflow', 'file_path': 'tests/test_user.py', 'language': 'python'}, {'category': 'instantiation', 'code': 'db = Database()', 'test_name': 'test_db', 'file_path': 'tests/test_db.py', 'language': 'python'}]
workflows = self.builder._extract_workflow_examples(examples)
self.assertEqual(len(workflows), 1)
self.assertEqual(workflows[0]['category'], 'workflow')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_how_to_guide_builder.py:427*

### test_create_guide_from_workflows

**Category**: workflow  
**Description**: Workflow: Test guide creation from grouped workflows  
**Expected**: self.assertIn(guide.complexity_level, ['beginner', 'intermediate', 'advanced'])  
**Confidence**: 0.90  
**Tags**: unittest, workflow, integration  

```python
# Setup
self.builder = HowToGuideBuilder(enhance_with_ai=False)
self.temp_dir = tempfile.mkdtemp()

'Test guide creation from grouped workflows'
workflows = [{'code': 'user = User(name="Alice")\ndb.save(user)', 'test_name': 'test_create_user', 'file_path': 'tests/test_user.py', 'language': 'python', 'category': 'workflow'}]
guide = self.builder._create_guide('User Management', workflows)
self.assertIsInstance(guide, HowToGuide)
self.assertEqual(guide.title, 'User Management')
self.assertGreater(len(guide.steps), 0)
self.assertIn(guide.complexity_level, ['beginner', 'intermediate', 'advanced'])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_how_to_guide_builder.py:452*

### test_analyze_python_workflow

**Category**: workflow  
**Description**: Workflow: Test analysis of Python workflow with multiple steps  
**Expected**: self.assertIn(metadata['complexity_level'], ['beginner', 'intermediate', 'advanced'])  
**Confidence**: 0.90  
**Tags**: unittest, workflow, integration  

```python
'Test analysis of Python workflow with multiple steps'
workflow = {'code': "\ndef test_user_creation_workflow():\n    # Step 1: Create database\n    db = Database('test.db')\n\n    # Step 2: Create user\n    user = User(name='Alice', email='alice@example.com')\n    db.save(user)\n\n    # Step 3: Verify creation\n    assert db.get_user('Alice').email == 'alice@example.com'\n", 'language': 'python', 'category': 'workflow', 'test_name': 'test_user_creation_workflow', 'file_path': 'tests/test_user.py'}
steps, metadata = self.analyzer.analyze_workflow(workflow)
self.assertGreaterEqual(len(steps), 2)
self.assertIsInstance(steps[0], WorkflowStep)
self.assertEqual(steps[0].step_number, 1)
self.assertIsNotNone(steps[0].description)
self.assertIn('complexity_level', metadata)
self.assertIn(metadata['complexity_level'], ['beginner', 'intermediate', 'advanced'])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_how_to_guide_builder.py:42*

### test_extract_workflow_examples

**Category**: workflow  
**Description**: Workflow: Test extraction of workflow examples from mixed examples  
**Expected**: self.assertEqual(workflows[0]['category'], 'workflow')  
**Confidence**: 0.90  
**Tags**: unittest, workflow, integration  

```python
'Test extraction of workflow examples from mixed examples'
examples = [{'category': 'workflow', 'code': 'db = Database()\nuser = User()\ndb.save(user)', 'test_name': 'test_user_workflow', 'file_path': 'tests/test_user.py', 'language': 'python'}, {'category': 'instantiation', 'code': 'db = Database()', 'test_name': 'test_db', 'file_path': 'tests/test_db.py', 'language': 'python'}]
workflows = self.builder._extract_workflow_examples(examples)
self.assertEqual(len(workflows), 1)
self.assertEqual(workflows[0]['category'], 'workflow')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_how_to_guide_builder.py:427*

### test_create_guide_from_workflows

**Category**: workflow  
**Description**: Workflow: Test guide creation from grouped workflows  
**Expected**: self.assertIn(guide.complexity_level, ['beginner', 'intermediate', 'advanced'])  
**Confidence**: 0.90  
**Tags**: unittest, workflow, integration  

```python
'Test guide creation from grouped workflows'
workflows = [{'code': 'user = User(name="Alice")\ndb.save(user)', 'test_name': 'test_create_user', 'file_path': 'tests/test_user.py', 'language': 'python', 'category': 'workflow'}]
guide = self.builder._create_guide('User Management', workflows)
self.assertIsInstance(guide, HowToGuide)
self.assertEqual(guide.title, 'User Management')
self.assertGreater(len(guide.steps), 0)
self.assertIn(guide.complexity_level, ['beginner', 'intermediate', 'advanced'])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_how_to_guide_builder.py:452*

### test_full_pipeline_with_streams

**Category**: workflow  
**Description**: Workflow: Test complete pipeline with three-stream data.  
**Expected**: assert result['conflict_summary']['total_conflicts'] == 0  
**Confidence**: 0.90  
**Tags**: workflow, integration  

```python
# Setup
# Fixtures: tmp_path

'Test complete pipeline with three-stream data.'
docs_data = {'pages': []}
github_data = {'apis': {}}
code_stream = CodeStream(directory=tmp_path, files=[])
docs_stream = DocsStream(readme='# Test Project\n\nA test project.', contributing='# Contributing\n\nPull requests welcome.', docs_files=[{'path': 'docs/quickstart.md', 'content': '# Quick Start'}, {'path': 'docs/api.md', 'content': '# API Reference'}])
insights_stream = InsightsStream(metadata={'stars': 2500, 'forks': 123, 'language': 'Python', 'description': 'Test framework'}, common_problems=[{'title': 'Installation fails on Windows', 'number': 150, 'state': 'open', 'comments': 25, 'labels': ['bug', 'windows']}, {'title': 'Memory leak in async mode', 'number': 142, 'state': 'open', 'comments': 18, 'labels': ['bug', 'async']}], known_solutions=[{'title': 'Fixed config loading', 'number': 130, 'state': 'closed', 'comments': 8, 'labels': ['bug']}, {'title': 'Resolved OAuth timeout', 'number': 125, 'state': 'closed', 'comments': 12, 'labels': ['oauth']}], top_labels=[{'label': 'bug', 'count': 45}, {'label': 'enhancement', 'count': 20}, {'label': 'question', 'count': 15}])
github_streams = ThreeStreamData(code_stream, docs_stream, insights_stream)
merger = RuleBasedMerger(docs_data, github_data, [], github_streams)
result = merger.merge_all()
assert 'apis' in result
assert 'github_context' in result
gh_context = result['github_context']
assert gh_context['docs']['readme'] == '# Test Project\n\nA test project.'
assert gh_context['docs']['contributing'] == '# Contributing\n\nPull requests welcome.'
assert gh_context['docs']['docs_files_count'] == 2
assert gh_context['metadata']['stars'] == 2500
assert gh_context['metadata']['language'] == 'Python'
assert gh_context['issues']['common_problems_count'] == 2
assert gh_context['issues']['known_solutions_count'] == 2
assert len(gh_context['issues']['top_problems']) == 2
assert len(gh_context['issues']['top_solutions']) == 2
assert len(gh_context['top_labels']) == 3
assert 'conflict_summary' in result
assert result['conflict_summary']['total_conflicts'] == 0
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_merge_sources_github.py:407*

### test_integration_with_code_analyzer

**Category**: workflow  
**Description**: Workflow: Test integration with actual code analyzer output format.  
**Expected**: self.assertIn('**Language**: JavaScript', js_content)  
**Confidence**: 0.90  
**Tags**: unittest, workflow, integration  

```python
# Setup
'Set up test environment'
self.temp_dir = tempfile.mkdtemp()
self.output_dir = Path(self.temp_dir) / 'api_reference'

'Test integration with actual code analyzer output format.'
code_analysis = {'files': [{'file': 'calculator.py', 'language': 'Python', 'classes': [{'name': 'Calculator', 'base_classes': [], 'methods': [{'name': 'add', 'parameters': [{'name': 'a', 'type_hint': 'float', 'default': None}, {'name': 'b', 'type_hint': 'float', 'default': None}], 'return_type': 'float', 'docstring': 'Add two numbers.', 'decorators': [], 'is_async': False, 'is_method': True}], 'docstring': 'Calculator class.', 'line_number': 1}], 'functions': []}, {'file': 'utils.js', 'language': 'JavaScript', 'classes': [], 'functions': [{'name': 'formatDate', 'parameters': [{'name': 'date', 'type_hint': None, 'default': None}], 'return_type': None, 'docstring': None, 'is_async': False, 'is_method': False, 'decorators': []}]}]}
builder = APIReferenceBuilder(code_analysis)
generated = builder.build_reference(self.output_dir)
self.assertEqual(len(generated), 2)
filenames = [f.name for f in generated.values()]
self.assertIn('calculator.md', filenames)
self.assertIn('utils.md', filenames)
py_file = next((f for f in generated.values() if f.name == 'calculator.md'))
py_content = py_file.read_text()
self.assertIn('Calculator class', py_content)
self.assertIn('add(a: float, b: float) → float', py_content)
js_file = next((f for f in generated.values() if f.name == 'utils.md'))
js_content = js_file.read_text()
self.assertIn('formatDate', js_content)
self.assertIn('**Language**: JavaScript', js_content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_api_reference_builder.py:214*

### test_integration_with_code_analyzer

**Category**: workflow  
**Description**: Workflow: Test integration with actual code analyzer output format.  
**Expected**: self.assertIn('**Language**: JavaScript', js_content)  
**Confidence**: 0.90  
**Tags**: unittest, workflow, integration  

```python
'Test integration with actual code analyzer output format.'
code_analysis = {'files': [{'file': 'calculator.py', 'language': 'Python', 'classes': [{'name': 'Calculator', 'base_classes': [], 'methods': [{'name': 'add', 'parameters': [{'name': 'a', 'type_hint': 'float', 'default': None}, {'name': 'b', 'type_hint': 'float', 'default': None}], 'return_type': 'float', 'docstring': 'Add two numbers.', 'decorators': [], 'is_async': False, 'is_method': True}], 'docstring': 'Calculator class.', 'line_number': 1}], 'functions': []}, {'file': 'utils.js', 'language': 'JavaScript', 'classes': [], 'functions': [{'name': 'formatDate', 'parameters': [{'name': 'date', 'type_hint': None, 'default': None}], 'return_type': None, 'docstring': None, 'is_async': False, 'is_method': False, 'decorators': []}]}]}
builder = APIReferenceBuilder(code_analysis)
generated = builder.build_reference(self.output_dir)
self.assertEqual(len(generated), 2)
filenames = [f.name for f in generated.values()]
self.assertIn('calculator.md', filenames)
self.assertIn('utils.md', filenames)
py_file = next((f for f in generated.values() if f.name == 'calculator.md'))
py_content = py_file.read_text()
self.assertIn('Calculator class', py_content)
self.assertIn('add(a: float, b: float) → float', py_content)
js_file = next((f for f in generated.values() if f.name == 'utils.md'))
js_content = js_file.read_text()
self.assertIn('formatDate', js_content)
self.assertIn('**Language**: JavaScript', js_content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_api_reference_builder.py:214*

### test_e2e_workflow_direct_git_url

**Category**: workflow  
**Description**: Workflow: E2E Test 1: Direct git URL workflow (no source registration)

Steps:
1. Clone repository via direct git URL
2. List available configs
3. Fetch specific config
4. Verify config content  
**Expected**: assert config['max_pages'] == 100  
**Confidence**: 0.90  
**Tags**: workflow, integration  

```python
# Setup
# Fixtures: temp_dirs, temp_git_repo

'\n        E2E Test 1: Direct git URL workflow (no source registration)\n\n        Steps:\n        1. Clone repository via direct git URL\n        2. List available configs\n        3. Fetch specific config\n        4. Verify config content\n        '
cache_dir, config_dir = temp_dirs
repo_dir, repo = temp_git_repo
git_url = f'file://{repo_dir}'
git_repo = GitConfigRepo(cache_dir=cache_dir)
repo_path = git_repo.clone_or_pull(source_name='test-direct', git_url=git_url, branch='master')
assert repo_path.exists()
assert (repo_path / '.git').exists()
configs = git_repo.find_configs(repo_path)
assert len(configs) == 3
config_names = [c.stem for c in configs]
assert set(config_names) == {'react', 'vue', 'django'}
config = git_repo.get_config(repo_path, 'react')
assert config['name'] == 'react'
assert config['description'] == 'React framework for UIs'
assert config['base_url'] == 'https://react.dev/'
assert 'selectors' in config
assert 'categories' in config
assert config['max_pages'] == 100
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_git_sources_e2e.py:107*

### test_e2e_workflow_with_source_registration

**Category**: workflow  
**Description**: Workflow: E2E Test 2: Complete workflow with source registration

Steps:
1. Add source to registry
2. List sources
3. Get source details
4. Clone via source name
5. Fetch config
6. Update source (re-add with different priority)
7. Remove source
8. Verify removal  
**Expected**: assert len(sources) == 0  
**Confidence**: 0.90  
**Tags**: workflow, integration  

```python
# Setup
# Fixtures: temp_dirs, temp_git_repo

'\n        E2E Test 2: Complete workflow with source registration\n\n        Steps:\n        1. Add source to registry\n        2. List sources\n        3. Get source details\n        4. Clone via source name\n        5. Fetch config\n        6. Update source (re-add with different priority)\n        7. Remove source\n        8. Verify removal\n        '
cache_dir, config_dir = temp_dirs
repo_dir, repo = temp_git_repo
git_url = f'file://{repo_dir}'
source_manager = SourceManager(config_dir=config_dir)
source = source_manager.add_source(name='team-configs', git_url=git_url, source_type='custom', branch='master', priority=10)
assert source['name'] == 'team-configs'
assert source['git_url'] == git_url
assert source['type'] == 'custom'
assert source['branch'] == 'master'
assert source['priority'] == 10
assert source['enabled'] is True
sources = source_manager.list_sources()
assert len(sources) == 1
assert sources[0]['name'] == 'team-configs'
retrieved_source = source_manager.get_source('team-configs')
assert retrieved_source['git_url'] == git_url
git_repo = GitConfigRepo(cache_dir=cache_dir)
repo_path = git_repo.clone_or_pull(source_name=source['name'], git_url=source['git_url'], branch=source['branch'])
assert repo_path.exists()
config = git_repo.get_config(repo_path, 'vue')
assert config['name'] == 'vue'
assert config['base_url'] == 'https://vuejs.org/'
updated_source = source_manager.add_source(name='team-configs', git_url=git_url, source_type='custom', branch='master', priority=5)
assert updated_source['priority'] == 5
removed = source_manager.remove_source('team-configs')
assert removed is True
sources = source_manager.list_sources()
assert len(sources) == 0
with pytest.raises(KeyError, match="Source 'team-configs' not found"):
    source_manager.get_source('team-configs')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_git_sources_e2e.py:150*

### test_e2e_multiple_sources_priority_resolution

**Category**: workflow  
**Description**: Workflow: E2E Test 3: Multiple sources with priority resolution

Steps:
1. Add multiple sources with different priorities
2. Verify sources are sorted by priority
3. Enable/disable sources
4. List enabled sources only  
**Expected**: assert 'high-priority' not in [s['name'] for s in enabled_sources]  
**Confidence**: 0.90  
**Tags**: workflow, integration  

```python
# Setup
# Fixtures: temp_dirs, temp_git_repo

'\n        E2E Test 3: Multiple sources with priority resolution\n\n        Steps:\n        1. Add multiple sources with different priorities\n        2. Verify sources are sorted by priority\n        3. Enable/disable sources\n        4. List enabled sources only\n        '
cache_dir, config_dir = temp_dirs
repo_dir, repo = temp_git_repo
git_url = f'file://{repo_dir}'
source_manager = SourceManager(config_dir=config_dir)
source_manager.add_source(name='low-priority', git_url=git_url, priority=100)
source_manager.add_source(name='high-priority', git_url=git_url, priority=1)
source_manager.add_source(name='medium-priority', git_url=git_url, priority=50)
sources = source_manager.list_sources()
assert len(sources) == 3
assert sources[0]['name'] == 'high-priority'
assert sources[1]['name'] == 'medium-priority'
assert sources[2]['name'] == 'low-priority'
source_manager.add_source(name='high-priority', git_url=git_url, priority=1, enabled=False)
enabled_sources = source_manager.list_sources(enabled_only=True)
assert len(enabled_sources) == 2
assert all((s['enabled'] for s in enabled_sources))
assert 'high-priority' not in [s['name'] for s in enabled_sources]
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_git_sources_e2e.py:225*

### test_e2e_pull_existing_repository

**Category**: workflow  
**Description**: Workflow: E2E Test 4: Pull updates from existing repository

Steps:
1. Clone repository
2. Add new commit to original repo
3. Pull updates
4. Verify new config is available  
**Expected**: assert fastapi_config['max_pages'] == 150  
**Confidence**: 0.90  
**Tags**: workflow, integration  

```python
# Setup
# Fixtures: temp_dirs, temp_git_repo

'\n        E2E Test 4: Pull updates from existing repository\n\n        Steps:\n        1. Clone repository\n        2. Add new commit to original repo\n        3. Pull updates\n        4. Verify new config is available\n        '
cache_dir, config_dir = temp_dirs
repo_dir, repo = temp_git_repo
git_url = f'file://{repo_dir}'
git_repo = GitConfigRepo(cache_dir=cache_dir)
repo_path = git_repo.clone_or_pull(source_name='test-pull', git_url=git_url, branch='master')
initial_configs = git_repo.find_configs(repo_path)
assert len(initial_configs) == 3
new_config = {'name': 'fastapi', 'description': 'FastAPI framework', 'base_url': 'https://fastapi.tiangolo.com/', 'selectors': {'main_content': 'article'}, 'url_patterns': {'include': [], 'exclude': []}, 'categories': {}, 'rate_limit': 0.5, 'max_pages': 150}
new_config_path = Path(repo_dir) / 'fastapi.json'
with open(new_config_path, 'w') as f:
    json.dump(new_config, f, indent=2)
repo.index.add(['fastapi.json'])
repo.index.commit('Add FastAPI config')
updated_repo_path = git_repo.clone_or_pull(source_name='test-pull', git_url=git_url, branch='master', force_refresh=False)
updated_configs = git_repo.find_configs(updated_repo_path)
assert len(updated_configs) == 4
fastapi_config = git_repo.get_config(updated_repo_path, 'fastapi')
assert fastapi_config['name'] == 'fastapi'
assert fastapi_config['max_pages'] == 150
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_git_sources_e2e.py:262*

### test_e2e_force_refresh

**Category**: workflow  
**Description**: Workflow: E2E Test 5: Force refresh (delete and re-clone)

Steps:
1. Clone repository
2. Modify local cache manually
3. Force refresh
4. Verify cache was reset  
**Expected**: assert len(configs) == 3  
**Confidence**: 0.90  
**Tags**: workflow, integration  

```python
# Setup
# Fixtures: temp_dirs, temp_git_repo

'\n        E2E Test 5: Force refresh (delete and re-clone)\n\n        Steps:\n        1. Clone repository\n        2. Modify local cache manually\n        3. Force refresh\n        4. Verify cache was reset\n        '
cache_dir, config_dir = temp_dirs
repo_dir, repo = temp_git_repo
git_url = f'file://{repo_dir}'
git_repo = GitConfigRepo(cache_dir=cache_dir)
repo_path = git_repo.clone_or_pull(source_name='test-refresh', git_url=git_url, branch='master')
corrupt_file = repo_path / 'CORRUPTED.txt'
with open(corrupt_file, 'w') as f:
    f.write('This file should not exist after refresh')
assert corrupt_file.exists()
refreshed_repo_path = git_repo.clone_or_pull(source_name='test-refresh', git_url=git_url, branch='master', force_refresh=True)
assert not corrupt_file.exists()
configs = git_repo.find_configs(refreshed_repo_path)
assert len(configs) == 3
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_git_sources_e2e.py:321*

### test_e2e_config_not_found

**Category**: workflow  
**Description**: Workflow: E2E Test 6: Error handling - config not found

Steps:
1. Clone repository
2. Try to fetch non-existent config
3. Verify helpful error message with suggestions  
**Expected**: assert 'django' in error_msg  
**Confidence**: 0.90  
**Tags**: workflow, integration  

```python
# Setup
# Fixtures: temp_dirs, temp_git_repo

'\n        E2E Test 6: Error handling - config not found\n\n        Steps:\n        1. Clone repository\n        2. Try to fetch non-existent config\n        3. Verify helpful error message with suggestions\n        '
cache_dir, config_dir = temp_dirs
repo_dir, repo = temp_git_repo
git_url = f'file://{repo_dir}'
git_repo = GitConfigRepo(cache_dir=cache_dir)
repo_path = git_repo.clone_or_pull(source_name='test-not-found', git_url=git_url, branch='master')
with pytest.raises(FileNotFoundError) as exc_info:
    git_repo.get_config(repo_path, 'nonexistent')
error_msg = str(exc_info.value)
assert 'nonexistent.json' in error_msg
assert 'not found' in error_msg
assert 'react' in error_msg
assert 'vue' in error_msg
assert 'django' in error_msg
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_git_sources_e2e.py:362*

### test_e2e_invalid_git_url

**Category**: workflow  
**Description**: Workflow: E2E Test 7: Error handling - invalid git URL

Steps:
1. Try to clone with invalid URL
2. Verify validation error  
**Confidence**: 0.90  
**Tags**: workflow, integration  

```python
# Setup
# Fixtures: temp_dirs

'\n        E2E Test 7: Error handling - invalid git URL\n\n        Steps:\n        1. Try to clone with invalid URL\n        2. Verify validation error\n        '
cache_dir, config_dir = temp_dirs
git_repo = GitConfigRepo(cache_dir=cache_dir)
invalid_urls = ['', 'not-a-url', 'ftp://invalid.com/repo.git', "javascript:alert('xss')"]
for invalid_url in invalid_urls:
    with pytest.raises(ValueError, match='Invalid git URL'):
        git_repo.clone_or_pull(source_name='test-invalid', git_url=invalid_url, branch='master')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_git_sources_e2e.py:394*

### test_e2e_source_name_validation

**Category**: workflow  
**Description**: Workflow: E2E Test 8: Error handling - invalid source names

Steps:
1. Try to add sources with invalid names
2. Verify validation errors  
**Confidence**: 0.90  
**Tags**: workflow, integration  

```python
# Setup
# Fixtures: temp_dirs

'\n        E2E Test 8: Error handling - invalid source names\n\n        Steps:\n        1. Try to add sources with invalid names\n        2. Verify validation errors\n        '
cache_dir, config_dir = temp_dirs
source_manager = SourceManager(config_dir=config_dir)
invalid_names = ['', 'name with spaces', 'name/with/slashes', 'name@with@symbols', 'name.with.dots', '123-only-numbers-start-is-ok', 'name!exclamation']
valid_git_url = 'https://github.com/test/repo.git'
for invalid_name in invalid_names[:-2]:
    if invalid_name == '123-only-numbers-start-is-ok':
        continue
    with pytest.raises(ValueError, match='Invalid source name'):
        source_manager.add_source(name=invalid_name, git_url=valid_git_url)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_git_sources_e2e.py:414*

### test_e2e_registry_persistence

**Category**: workflow  
**Description**: Workflow: E2E Test 9: Registry persistence across instances

Steps:
1. Add source with one SourceManager instance
2. Create new SourceManager instance
3. Verify source persists
4. Modify source with new instance
5. Verify changes persist  
**Expected**: assert source['priority'] == 50  
**Confidence**: 0.90  
**Tags**: workflow, integration  

```python
# Setup
# Fixtures: temp_dirs, temp_git_repo

'\n        E2E Test 9: Registry persistence across instances\n\n        Steps:\n        1. Add source with one SourceManager instance\n        2. Create new SourceManager instance\n        3. Verify source persists\n        4. Modify source with new instance\n        5. Verify changes persist\n        '
cache_dir, config_dir = temp_dirs
repo_dir, repo = temp_git_repo
git_url = f'file://{repo_dir}'
manager1 = SourceManager(config_dir=config_dir)
manager1.add_source(name='persistent-source', git_url=git_url, priority=25)
manager2 = SourceManager(config_dir=config_dir)
sources = manager2.list_sources()
assert len(sources) == 1
assert sources[0]['name'] == 'persistent-source'
assert sources[0]['priority'] == 25
manager2.add_source(name='persistent-source', git_url=git_url, priority=50)
manager3 = SourceManager(config_dir=config_dir)
source = manager3.get_source('persistent-source')
assert source['priority'] == 50
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_git_sources_e2e.py:444*

### test_e2e_cache_isolation

**Category**: workflow  
**Description**: Workflow: E2E Test 10: Cache isolation between different cache directories

Steps:
1. Clone to cache_dir_1
2. Clone same repo to cache_dir_2
3. Verify both caches are independent
4. Modify one cache
5. Verify other cache is unaffected  
**Confidence**: 0.90  
**Tags**: workflow, integration  

```python
# Setup
# Fixtures: temp_dirs, temp_git_repo

'\n        E2E Test 10: Cache isolation between different cache directories\n\n        Steps:\n        1. Clone to cache_dir_1\n        2. Clone same repo to cache_dir_2\n        3. Verify both caches are independent\n        4. Modify one cache\n        5. Verify other cache is unaffected\n        '
_config_dir = temp_dirs[1]
repo_dir, repo = temp_git_repo
cache_dir_1 = tempfile.mkdtemp(prefix='ss_cache1_')
cache_dir_2 = tempfile.mkdtemp(prefix='ss_cache2_')
try:
    git_url = f'file://{repo_dir}'
    git_repo_1 = GitConfigRepo(cache_dir=cache_dir_1)
    repo_path_1 = git_repo_1.clone_or_pull(source_name='test-source', git_url=git_url, branch='master')
    git_repo_2 = GitConfigRepo(cache_dir=cache_dir_2)
    repo_path_2 = git_repo_2.clone_or_pull(source_name='test-source', git_url=git_url, branch='master')
    assert repo_path_1 != repo_path_2
    assert repo_path_1.exists()
    assert repo_path_2.exists()
    marker_file = repo_path_1 / 'MARKER.txt'
    with open(marker_file, 'w') as f:
        f.write('Cache 1 marker')
    assert marker_file.exists()
    assert not (repo_path_2 / 'MARKER.txt').exists()
    configs_1 = git_repo_1.find_configs(repo_path_1)
    configs_2 = git_repo_2.find_configs(repo_path_2)
    assert len(configs_1) == len(configs_2) == 3
finally:
    shutil.rmtree(cache_dir_1, ignore_errors=True)
    shutil.rmtree(cache_dir_2, ignore_errors=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_git_sources_e2e.py:485*

### test_github_workflows_reference_correct_paths

**Category**: workflow  
**Description**: Workflow: Test that GitHub workflows reference correct MCP paths  
**Confidence**: 0.90  
**Tags**: workflow, integration  

```python
'Test that GitHub workflows reference correct MCP paths'
workflow_file = Path('.github/workflows/tests.yml')
if workflow_file.exists():
    with open(workflow_file) as f:
        content = f.read()
    assert 'mcp/requirements.txt' not in content or 'skill_seeker_mcp/requirements.txt' in content, 'GitHub workflow should use correct MCP paths'
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_setup_scripts.py:200*

### test_high_confidence_full_app

**Category**: workflow  
**Description**: Workflow: Test complete SwiftUI app (high confidence expected)  
**Expected**: assert confidence >= 0.95  
**Confidence**: 0.90  
**Tags**: workflow, integration  

```python
'Test complete SwiftUI app (high confidence expected)'
detector = LanguageDetector()
code = '\n        import SwiftUI\n\n        @main\n        struct MyApp: App {\n            @StateObject private var viewModel = AppViewModel()\n\n            var body: some Scene {\n                WindowGroup {\n                    ContentView()\n                        .environmentObject(viewModel)\n                }\n            }\n        }\n\n        struct ContentView: View {\n            @EnvironmentObject var viewModel: AppViewModel\n            @State private var searchText = ""\n\n            var body: some View {\n                NavigationStack {\n                    List {\n                        ForEach(viewModel.filteredItems) { item in\n                            NavigationLink(destination: DetailView(item: item)) {\n                                ItemRow(item: item)\n                            }\n                        }\n                    }\n                    .navigationTitle("Items")\n                    .searchable(text: $searchText)\n                    .refreshable {\n                        await viewModel.refresh()\n                    }\n                }\n            }\n        }\n        '
lang, confidence = detector.detect_from_code(code)
assert lang == 'swift'
assert confidence >= 0.95
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_swift_detection.py:960*

### test_empty_swift_patterns_handled_gracefully

**Category**: workflow  
**Description**: Workflow: Test that empty SWIFT_PATTERNS dict doesn't crash detection  
**Confidence**: 0.90  
**Tags**: mock, workflow, integration  

```python
"Test that empty SWIFT_PATTERNS dict doesn't crash detection"
import sys
from unittest.mock import patch
for mod in list(sys.modules.keys()):
    if 'skill_seekers.cli' in mod:
        del sys.modules[mod]
with patch.dict('sys.modules', {'skill_seekers.cli.swift_patterns': type('MockModule', (), {'SWIFT_PATTERNS': {}})}):
    from skill_seekers.cli.language_detector import LanguageDetector
    detector = LanguageDetector()
    code = 'import SwiftUI\nstruct MyView: View { }'
    lang, confidence = detector.detect_from_code(code)
    assert isinstance(lang, str)
    assert isinstance(confidence, (int, float))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_swift_detection.py:1323*

### test_add_source_full_parameters

**Category**: workflow  
**Description**: Workflow: Test adding source with all parameters.  
**Expected**: assert source['enabled'] is False  
**Confidence**: 0.90  
**Tags**: workflow, integration  

```python
# Setup
# Fixtures: source_manager

'Test adding source with all parameters.'
source = source_manager.add_source(name='company', git_url='https://gitlab.company.com/platform/configs.git', source_type='gitlab', token_env='CUSTOM_TOKEN', branch='develop', priority=1, enabled=False)
assert source['name'] == 'company'
assert source['type'] == 'gitlab'
assert source['token_env'] == 'CUSTOM_TOKEN'
assert source['branch'] == 'develop'
assert source['priority'] == 1
assert source['enabled'] is False
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_source_manager.py:98*

### test_full_workflow_unified_config

**Category**: workflow  
**Description**: Workflow: Test complete workflow with unified config  
**Expected**: assert validator.needs_api_merge()  
**Confidence**: 0.90  
**Tags**: workflow, integration  

```python
'Test complete workflow with unified config'
config = {'name': 'test_unified', 'description': 'Test unified workflow', 'merge_mode': 'rule-based', 'sources': [{'type': 'documentation', 'base_url': 'https://example.com', 'extract_api': True}, {'type': 'github', 'repo': 'user/repo', 'include_code': True, 'code_analysis_depth': 'surface'}]}
validator = ConfigValidator(config)
validator.validate()
assert validator.is_unified
assert validator.needs_api_merge()
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_unified.py:527*

### test_end_to_end_workflow

**Category**: workflow  
**Description**: Workflow: Test complete extraction workflow  
**Expected**: self.assertGreater(len(report.examples_by_category), 0)  
**Confidence**: 0.90  
**Tags**: unittest, workflow, integration  

```python
# Setup
self.temp_dir = Path(tempfile.mkdtemp())
self.extractor = TestExampleExtractor(min_confidence=0.5, max_per_file=10)

'Test complete extraction workflow'
(self.temp_dir / 'tests').mkdir()
(self.temp_dir / 'tests' / 'test_unit.py').write_text('\nimport unittest\n\nclass TestAPI(unittest.TestCase):\n    def test_connection(self):\n        """Test API connection"""\n        api = APIClient(url="https://api.example.com", timeout=30)\n        self.assertTrue(api.connect())\n')
(self.temp_dir / 'tests' / 'test_integration.py').write_text('\ndef test_workflow():\n    """Test complete workflow"""\n    user = User(name="John", email="john@example.com")\n    user.save()\n    user.verify()\n    assert user.is_active\n')
report = self.extractor.extract_from_directory(self.temp_dir / 'tests')
self.assertGreater(report.total_examples, 0)
self.assertIsInstance(report.examples_by_category, dict)
self.assertIsInstance(report.examples_by_language, dict)
self.assertGreaterEqual(report.avg_complexity, 0.0)
self.assertLessEqual(report.avg_complexity, 1.0)
self.assertGreater(len(report.examples_by_category), 0)
for example in report.examples:
    self.assertIsNotNone(example.example_id)
    self.assertIsNotNone(example.test_name)
    self.assertIsNotNone(example.category)
    self.assertIsNotNone(example.code)
    self.assertIsNotNone(example.language)
    self.assertGreaterEqual(example.confidence, 0.0)
    self.assertLessEqual(example.confidence, 1.0)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_test_example_extractor.py:535*

### test_end_to_end_workflow

**Category**: workflow  
**Description**: Workflow: Test complete extraction workflow  
**Expected**: self.assertGreater(len(report.examples_by_category), 0)  
**Confidence**: 0.90  
**Tags**: unittest, workflow, integration  

```python
'Test complete extraction workflow'
(self.temp_dir / 'tests').mkdir()
(self.temp_dir / 'tests' / 'test_unit.py').write_text('\nimport unittest\n\nclass TestAPI(unittest.TestCase):\n    def test_connection(self):\n        """Test API connection"""\n        api = APIClient(url="https://api.example.com", timeout=30)\n        self.assertTrue(api.connect())\n')
(self.temp_dir / 'tests' / 'test_integration.py').write_text('\ndef test_workflow():\n    """Test complete workflow"""\n    user = User(name="John", email="john@example.com")\n    user.save()\n    user.verify()\n    assert user.is_active\n')
report = self.extractor.extract_from_directory(self.temp_dir / 'tests')
self.assertGreater(report.total_examples, 0)
self.assertIsInstance(report.examples_by_category, dict)
self.assertIsInstance(report.examples_by_language, dict)
self.assertGreaterEqual(report.avg_complexity, 0.0)
self.assertLessEqual(report.avg_complexity, 1.0)
self.assertGreater(len(report.examples_by_category), 0)
for example in report.examples:
    self.assertIsNotNone(example.example_id)
    self.assertIsNotNone(example.test_name)
    self.assertIsNotNone(example.category)
    self.assertIsNotNone(example.code)
    self.assertIsNotNone(example.language)
    self.assertGreaterEqual(example.confidence, 0.0)
    self.assertLessEqual(example.confidence, 1.0)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_test_example_extractor.py:535*

### test_unity_full_script

**Category**: workflow  
**Description**: Workflow: Test complete Unity script (high confidence expected)  
**Expected**: assert confidence >= 0.9  
**Confidence**: 0.90  
**Tags**: workflow, integration  

```python
'Test complete Unity script (high confidence expected)'
detector = LanguageDetector()
code = '\n        using UnityEngine;\n        using System.Collections;\n\n        public class PlayerController : MonoBehaviour\n        {\n            [SerializeField]\n            private float speed = 5.0f;\n\n            [SerializeField]\n            private Rigidbody rb;\n\n            void Awake()\n            {\n                rb = GetComponent<Rigidbody>();\n            }\n\n            void Update()\n            {\n                float moveH = Input.GetAxis("Horizontal");\n                float moveV = Input.GetAxis("Vertical");\n\n                Vector3 movement = new Vector3(moveH, 0, moveV);\n                rb.AddForce(movement * speed);\n            }\n\n            IEnumerator DashCoroutine()\n            {\n                speed *= 2;\n                yield return new WaitForSeconds(0.5f);\n                speed /= 2;\n            }\n        }\n        '
lang, confidence = detector.detect_from_code(code)
assert lang == 'csharp'
assert confidence >= 0.9
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_language_detector.py:256*

### test_full_metadata

**Category**: workflow  
**Description**: Workflow: Test metadata with all fields  
**Expected**: self.assertEqual(metadata.tags, ['react', 'javascript', 'web'])  
**Confidence**: 0.90  
**Tags**: unittest, workflow, integration  

```python
'Test metadata with all fields'
metadata = SkillMetadata(name='react', description='React documentation', version='2.5.0', author='Test Author', tags=['react', 'javascript', 'web'])
self.assertEqual(metadata.name, 'react')
self.assertEqual(metadata.description, 'React documentation')
self.assertEqual(metadata.version, '2.5.0')
self.assertEqual(metadata.author, 'Test Author')
self.assertEqual(metadata.tags, ['react', 'javascript', 'web'])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_base.py:30*

### test_full_metadata

**Category**: workflow  
**Description**: Workflow: Test metadata with all fields  
**Expected**: self.assertEqual(metadata.tags, ['react', 'javascript', 'web'])  
**Confidence**: 0.90  
**Tags**: unittest, workflow, integration  

```python
'Test metadata with all fields'
metadata = SkillMetadata(name='react', description='React documentation', version='2.5.0', author='Test Author', tags=['react', 'javascript', 'web'])
self.assertEqual(metadata.name, 'react')
self.assertEqual(metadata.description, 'React documentation')
self.assertEqual(metadata.version, '2.5.0')
self.assertEqual(metadata.author, 'Test Author')
self.assertEqual(metadata.tags, ['react', 'javascript', 'web'])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_base.py:30*

### test_e2e_all_platforms_from_same_skill

**Category**: workflow  
**Description**: Workflow: Test that all platforms can package the same skill  
**Expected**: self.assertTrue(str(packages['markdown']).endswith('.zip'))  
**Confidence**: 0.90  
**Tags**: unittest, workflow, integration  

```python
# Setup
'Set up test environment with sample skill directory'
self.temp_dir = tempfile.TemporaryDirectory()
self.skill_dir = Path(self.temp_dir.name) / 'test-skill'
self.skill_dir.mkdir()
self._create_sample_skill()
self.output_dir = Path(self.temp_dir.name) / 'output'
self.output_dir.mkdir()

'Test that all platforms can package the same skill'
platforms = ['claude', 'gemini', 'openai', 'markdown']
packages = {}
for platform in platforms:
    adaptor = get_adaptor(platform)
    package_path = adaptor.package(self.skill_dir, self.output_dir)
    self.assertTrue(package_path.exists(), f'Package not created for {platform}')
    packages[platform] = package_path
self.assertEqual(len(packages), 4)
self.assertTrue(str(packages['claude']).endswith('.zip'))
self.assertTrue(str(packages['gemini']).endswith('.tar.gz'))
self.assertTrue(str(packages['openai']).endswith('.zip'))
self.assertTrue(str(packages['markdown']).endswith('.zip'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_adaptors_e2e.py:129*

### test_e2e_claude_workflow

**Category**: workflow  
**Description**: Workflow: Test complete Claude workflow: package + verify structure  
**Expected**: self.assertTrue(str(package_path).endswith('.zip'))  
**Confidence**: 0.90  
**Tags**: unittest, workflow, integration  

```python
# Setup
'Set up test environment with sample skill directory'
self.temp_dir = tempfile.TemporaryDirectory()
self.skill_dir = Path(self.temp_dir.name) / 'test-skill'
self.skill_dir.mkdir()
self._create_sample_skill()
self.output_dir = Path(self.temp_dir.name) / 'output'
self.output_dir.mkdir()

'Test complete Claude workflow: package + verify structure'
adaptor = get_adaptor('claude')
package_path = adaptor.package(self.skill_dir, self.output_dir)
self.assertTrue(package_path.exists())
self.assertTrue(str(package_path).endswith('.zip'))
with zipfile.ZipFile(package_path, 'r') as zf:
    names = zf.namelist()
    self.assertIn('SKILL.md', names)
    self.assertTrue(any(('references/' in name for name in names)))
    skill_content = zf.read('SKILL.md').decode('utf-8')
    self.assertGreater(len(skill_content), 0)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_adaptors_e2e.py:155*

### test_e2e_gemini_workflow

**Category**: workflow  
**Description**: Workflow: Test complete Gemini workflow: package + verify structure  
**Expected**: self.assertTrue(str(package_path).endswith('.tar.gz'))  
**Confidence**: 0.90  
**Tags**: unittest, workflow, integration  

```python
# Setup
'Set up test environment with sample skill directory'
self.temp_dir = tempfile.TemporaryDirectory()
self.skill_dir = Path(self.temp_dir.name) / 'test-skill'
self.skill_dir.mkdir()
self._create_sample_skill()
self.output_dir = Path(self.temp_dir.name) / 'output'
self.output_dir.mkdir()

'Test complete Gemini workflow: package + verify structure'
adaptor = get_adaptor('gemini')
package_path = adaptor.package(self.skill_dir, self.output_dir)
self.assertTrue(package_path.exists())
self.assertTrue(str(package_path).endswith('.tar.gz'))
with tarfile.open(package_path, 'r:gz') as tar:
    names = tar.getnames()
    self.assertIn('system_instructions.md', names)
    self.assertTrue(any(('references/' in name for name in names)))
    self.assertIn('gemini_metadata.json', names)
    metadata_member = tar.getmember('gemini_metadata.json')
    metadata_file = tar.extractfile(metadata_member)
    metadata = json.loads(metadata_file.read().decode('utf-8'))
    self.assertEqual(metadata['platform'], 'gemini')
    self.assertEqual(metadata['name'], 'test-skill')
    self.assertIn('created_with', metadata)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_adaptors_e2e.py:182*

### test_e2e_openai_workflow

**Category**: workflow  
**Description**: Workflow: Test complete OpenAI workflow: package + verify structure  
**Expected**: self.assertTrue(str(package_path).endswith('.zip'))  
**Confidence**: 0.90  
**Tags**: unittest, workflow, integration  

```python
# Setup
'Set up test environment with sample skill directory'
self.temp_dir = tempfile.TemporaryDirectory()
self.skill_dir = Path(self.temp_dir.name) / 'test-skill'
self.skill_dir.mkdir()
self._create_sample_skill()
self.output_dir = Path(self.temp_dir.name) / 'output'
self.output_dir.mkdir()

'Test complete OpenAI workflow: package + verify structure'
adaptor = get_adaptor('openai')
package_path = adaptor.package(self.skill_dir, self.output_dir)
self.assertTrue(package_path.exists())
self.assertTrue(str(package_path).endswith('.zip'))
with zipfile.ZipFile(package_path, 'r') as zf:
    names = zf.namelist()
    self.assertIn('assistant_instructions.txt', names)
    self.assertTrue(any(('vector_store_files/' in name for name in names)))
    self.assertIn('openai_metadata.json', names)
    metadata_content = zf.read('openai_metadata.json').decode('utf-8')
    metadata = json.loads(metadata_content)
    self.assertEqual(metadata['platform'], 'openai')
    self.assertEqual(metadata['name'], 'test-skill')
    self.assertEqual(metadata['model'], 'gpt-4o')
    self.assertIn('file_search', metadata['tools'])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_adaptors_e2e.py:215*

### test_e2e_markdown_workflow

**Category**: workflow  
**Description**: Workflow: Test complete Markdown workflow: package + verify structure  
**Expected**: self.assertTrue(str(package_path).endswith('.zip'))  
**Confidence**: 0.90  
**Tags**: unittest, workflow, integration  

```python
# Setup
'Set up test environment with sample skill directory'
self.temp_dir = tempfile.TemporaryDirectory()
self.skill_dir = Path(self.temp_dir.name) / 'test-skill'
self.skill_dir.mkdir()
self._create_sample_skill()
self.output_dir = Path(self.temp_dir.name) / 'output'
self.output_dir.mkdir()

'Test complete Markdown workflow: package + verify structure'
adaptor = get_adaptor('markdown')
package_path = adaptor.package(self.skill_dir, self.output_dir)
self.assertTrue(package_path.exists())
self.assertTrue(str(package_path).endswith('.zip'))
with zipfile.ZipFile(package_path, 'r') as zf:
    names = zf.namelist()
    self.assertIn('README.md', names)
    self.assertIn('DOCUMENTATION.md', names)
    self.assertTrue(any(('references/' in name for name in names)))
    self.assertIn('metadata.json', names)
    doc_content = zf.read('DOCUMENTATION.md').decode('utf-8')
    self.assertIn('Getting Started', doc_content)
    self.assertIn('React Hooks', doc_content)
    self.assertIn('Components', doc_content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_adaptors_e2e.py:248*

### test_e2e_package_format_validation

**Category**: workflow  
**Description**: Workflow: Test that each platform creates correct package format  
**Confidence**: 0.90  
**Tags**: unittest, workflow, integration  

```python
# Setup
'Set up test environment with sample skill directory'
self.temp_dir = tempfile.TemporaryDirectory()
self.skill_dir = Path(self.temp_dir.name) / 'test-skill'
self.skill_dir.mkdir()
self._create_sample_skill()
self.output_dir = Path(self.temp_dir.name) / 'output'
self.output_dir.mkdir()

'Test that each platform creates correct package format'
test_cases = [('claude', '.zip'), ('gemini', '.tar.gz'), ('openai', '.zip'), ('markdown', '.zip')]
for platform, expected_ext in test_cases:
    adaptor = get_adaptor(platform)
    package_path = adaptor.package(self.skill_dir, self.output_dir)
    if expected_ext == '.tar.gz':
        self.assertTrue(str(package_path).endswith('.tar.gz'), f'{platform} should create .tar.gz file')
    else:
        self.assertTrue(str(package_path).endswith('.zip'), f'{platform} should create .zip file')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_adaptors_e2e.py:283*

### test_e2e_package_filename_convention

**Category**: workflow  
**Description**: Workflow: Test that package filenames follow convention  
**Confidence**: 0.90  
**Tags**: unittest, workflow, integration  

```python
# Setup
'Set up test environment with sample skill directory'
self.temp_dir = tempfile.TemporaryDirectory()
self.skill_dir = Path(self.temp_dir.name) / 'test-skill'
self.skill_dir.mkdir()
self._create_sample_skill()
self.output_dir = Path(self.temp_dir.name) / 'output'
self.output_dir.mkdir()

'Test that package filenames follow convention'
test_cases = [('claude', 'test-skill.zip'), ('gemini', 'test-skill-gemini.tar.gz'), ('openai', 'test-skill-openai.zip'), ('markdown', 'test-skill-markdown.zip')]
for platform, expected_name in test_cases:
    adaptor = get_adaptor(platform)
    package_path = adaptor.package(self.skill_dir, self.output_dir)
    self.assertEqual(package_path.name, expected_name, f'{platform} package filename incorrect')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_adaptors_e2e.py:306*

### test_e2e_all_platforms_preserve_references

**Category**: workflow  
**Description**: Workflow: Test that all platforms preserve reference files  
**Confidence**: 0.90  
**Tags**: unittest, workflow, integration  

```python
# Setup
'Set up test environment with sample skill directory'
self.temp_dir = tempfile.TemporaryDirectory()
self.skill_dir = Path(self.temp_dir.name) / 'test-skill'
self.skill_dir.mkdir()
self._create_sample_skill()
self.output_dir = Path(self.temp_dir.name) / 'output'
self.output_dir.mkdir()

'Test that all platforms preserve reference files'
ref_files = ['getting_started.md', 'hooks.md', 'components.md']
for platform in ['claude', 'gemini', 'openai', 'markdown']:
    adaptor = get_adaptor(platform)
    package_path = adaptor.package(self.skill_dir, self.output_dir)
    if platform == 'gemini':
        with tarfile.open(package_path, 'r:gz') as tar:
            names = tar.getnames()
            for ref_file in ref_files:
                self.assertTrue(any((ref_file in name for name in names)), f'{platform}: {ref_file} not found in package')
    else:
        with zipfile.ZipFile(package_path, 'r') as zf:
            names = zf.namelist()
            for ref_file in ref_files:
                if platform == 'openai':
                    self.assertTrue(any((f'vector_store_files/{ref_file}' in name for name in names)), f'{platform}: {ref_file} not found in vector_store_files/')
                else:
                    self.assertTrue(any((ref_file in name for name in names)), f'{platform}: {ref_file} not found in package')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_adaptors_e2e.py:324*

### test_e2e_metadata_consistency

**Category**: workflow  
**Description**: Workflow: Test that metadata is consistent across platforms  
**Confidence**: 0.90  
**Tags**: unittest, workflow, integration  

```python
# Setup
'Set up test environment with sample skill directory'
self.temp_dir = tempfile.TemporaryDirectory()
self.skill_dir = Path(self.temp_dir.name) / 'test-skill'
self.skill_dir.mkdir()
self._create_sample_skill()
self.output_dir = Path(self.temp_dir.name) / 'output'
self.output_dir.mkdir()

'Test that metadata is consistent across platforms'
platforms_with_metadata = ['gemini', 'openai', 'markdown']
for platform in platforms_with_metadata:
    adaptor = get_adaptor(platform)
    package_path = adaptor.package(self.skill_dir, self.output_dir)
    if platform == 'gemini':
        with tarfile.open(package_path, 'r:gz') as tar:
            metadata_member = tar.getmember('gemini_metadata.json')
            metadata_file = tar.extractfile(metadata_member)
            metadata = json.loads(metadata_file.read().decode('utf-8'))
    else:
        with zipfile.ZipFile(package_path, 'r') as zf:
            metadata_filename = f'{platform}_metadata.json' if platform == 'openai' else 'metadata.json'
            metadata_content = zf.read(metadata_filename).decode('utf-8')
            metadata = json.loads(metadata_content)
    self.assertEqual(metadata['platform'], platform)
    self.assertEqual(metadata['name'], 'test-skill')
    self.assertIn('created_with', metadata)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_adaptors_e2e.py:357*

### test_e2e_format_skill_md_differences

**Category**: workflow  
**Description**: Workflow: Test that each platform formats SKILL.md differently  
**Expected**: self.assertFalse(formats['markdown'].startswith('---'))  
**Confidence**: 0.90  
**Tags**: unittest, workflow, integration  

```python
# Setup
'Set up test environment with sample skill directory'
self.temp_dir = tempfile.TemporaryDirectory()
self.skill_dir = Path(self.temp_dir.name) / 'test-skill'
self.skill_dir.mkdir()
self._create_sample_skill()
self.output_dir = Path(self.temp_dir.name) / 'output'
self.output_dir.mkdir()

'Test that each platform formats SKILL.md differently'
metadata = SkillMetadata(name='test-skill', description='Test skill for E2E testing')
formats = {}
for platform in ['claude', 'gemini', 'openai', 'markdown']:
    adaptor = get_adaptor(platform)
    formatted = adaptor.format_skill_md(self.skill_dir, metadata)
    formats[platform] = formatted
self.assertTrue(formats['claude'].startswith('---'))
self.assertFalse(formats['gemini'].startswith('---'))
self.assertFalse(formats['markdown'].startswith('---'))
for platform, formatted in formats.items():
    self.assertIn('react', formatted.lower(), f'{platform} should contain skill content')
    self.assertGreater(len(formatted), 100, f'{platform} should have substantial content')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_adaptors_e2e.py:384*

### test_package_nonexistent_directory

**Category**: method_call  
**Description**: Test packaging a nonexistent directory  
**Expected**: self.assertIsNone(zip_path)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertFalse(success)
self.assertIsNone(zip_path)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_package_skill.py:101*

### test_package_nonexistent_directory

**Category**: method_call  
**Description**: Test packaging a nonexistent directory  
**Expected**: self.assertIsNone(zip_path)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertFalse(success)
self.assertIsNone(zip_path)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_package_skill.py:101*

### test_cors_middleware

**Category**: method_call  
**Description**: Test that CORS middleware can be added.  
**Expected**: assert len(app.user_middleware) > 0  
**Confidence**: 0.85  

```python
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
assert len(app.user_middleware) > 0
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_server_fastmcp_http.py:90*

### test_platform_info

**Category**: method_call  
**Description**: Test platform identifiers  
**Expected**: self.assertEqual(self.adaptor.PLATFORM_NAME, 'OpenAI ChatGPT')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('openai')

self.assertEqual(self.adaptor.PLATFORM, 'openai')
self.assertEqual(self.adaptor.PLATFORM_NAME, 'OpenAI ChatGPT')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_openai_adaptor.py:24*

### test_platform_info

**Category**: method_call  
**Description**: Test platform identifiers  
**Expected**: self.assertIsNotNone(self.adaptor.DEFAULT_API_ENDPOINT)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('openai')

self.assertEqual(self.adaptor.PLATFORM_NAME, 'OpenAI ChatGPT')
self.assertIsNotNone(self.adaptor.DEFAULT_API_ENDPOINT)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_openai_adaptor.py:25*

### test_validate_api_key_valid

**Category**: method_call  
**Description**: Test valid OpenAI API keys  
**Expected**: self.assertTrue(self.adaptor.validate_api_key('sk-abc123'))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('openai')

self.assertTrue(self.adaptor.validate_api_key('sk-proj-abc123'))
self.assertTrue(self.adaptor.validate_api_key('sk-abc123'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_openai_adaptor.py:30*

### test_validate_api_key_valid

**Category**: method_call  
**Description**: Test valid OpenAI API keys  
**Expected**: self.assertTrue(self.adaptor.validate_api_key('  sk-test  '))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('openai')

self.assertTrue(self.adaptor.validate_api_key('sk-abc123'))
self.assertTrue(self.adaptor.validate_api_key('  sk-test  '))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_openai_adaptor.py:31*

### test_validate_api_key_invalid

**Category**: method_call  
**Description**: Test invalid API keys  
**Expected**: self.assertFalse(self.adaptor.validate_api_key('invalid'))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('openai')

self.assertFalse(self.adaptor.validate_api_key('AIzaSyABC123'))
self.assertFalse(self.adaptor.validate_api_key('invalid'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_openai_adaptor.py:36*

### test_validate_api_key_invalid

**Category**: method_call  
**Description**: Test invalid API keys  
**Expected**: self.assertFalse(self.adaptor.validate_api_key(''))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('openai')

self.assertFalse(self.adaptor.validate_api_key('invalid'))
self.assertFalse(self.adaptor.validate_api_key(''))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_openai_adaptor.py:38*

### test_upload_invalid_file

**Category**: method_call  
**Description**: Test upload with invalid file  
**Expected**: self.assertIn('not found', result['message'].lower())  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('openai')

self.assertFalse(result['success'])
self.assertIn('not found', result['message'].lower())
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_openai_adaptor.py:113*

### test_platform_info

**Category**: method_call  
**Description**: Test platform identifiers  
**Expected**: self.assertEqual(self.adaptor.PLATFORM_NAME, 'OpenAI ChatGPT')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(self.adaptor.PLATFORM, 'openai')
self.assertEqual(self.adaptor.PLATFORM_NAME, 'OpenAI ChatGPT')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_openai_adaptor.py:24*

### test_platform_info

**Category**: method_call  
**Description**: Test platform identifiers  
**Expected**: self.assertIsNotNone(self.adaptor.DEFAULT_API_ENDPOINT)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(self.adaptor.PLATFORM_NAME, 'OpenAI ChatGPT')
self.assertIsNotNone(self.adaptor.DEFAULT_API_ENDPOINT)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_openai_adaptor.py:25*

### test_validate_api_key_valid

**Category**: method_call  
**Description**: Test valid OpenAI API keys  
**Expected**: self.assertTrue(self.adaptor.validate_api_key('sk-abc123'))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertTrue(self.adaptor.validate_api_key('sk-proj-abc123'))
self.assertTrue(self.adaptor.validate_api_key('sk-abc123'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_openai_adaptor.py:30*

### test_platform_info

**Category**: method_call  
**Description**: Test platform identifiers  
**Expected**: self.assertIn('Claude', self.adaptor.PLATFORM_NAME)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('claude')

self.assertEqual(self.adaptor.PLATFORM, 'claude')
self.assertIn('Claude', self.adaptor.PLATFORM_NAME)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_claude_adaptor.py:25*

### test_platform_info

**Category**: method_call  
**Description**: Test platform identifiers  
**Expected**: self.assertIsNotNone(self.adaptor.DEFAULT_API_ENDPOINT)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('claude')

self.assertIn('Claude', self.adaptor.PLATFORM_NAME)
self.assertIsNotNone(self.adaptor.DEFAULT_API_ENDPOINT)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_claude_adaptor.py:26*

### test_platform_info

**Category**: method_call  
**Description**: Test platform identifiers  
**Expected**: self.assertIn('anthropic.com', self.adaptor.DEFAULT_API_ENDPOINT)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('claude')

self.assertIsNotNone(self.adaptor.DEFAULT_API_ENDPOINT)
self.assertIn('anthropic.com', self.adaptor.DEFAULT_API_ENDPOINT)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_claude_adaptor.py:27*

### test_validate_api_key_valid

**Category**: method_call  
**Description**: Test valid Claude API keys  
**Expected**: self.assertTrue(self.adaptor.validate_api_key('sk-ant-api03-test'))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('claude')

self.assertTrue(self.adaptor.validate_api_key('sk-ant-abc123'))
self.assertTrue(self.adaptor.validate_api_key('sk-ant-api03-test'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_claude_adaptor.py:32*

### test_validate_api_key_valid

**Category**: method_call  
**Description**: Test valid Claude API keys  
**Expected**: self.assertTrue(self.adaptor.validate_api_key('  sk-ant-test  '))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('claude')

self.assertTrue(self.adaptor.validate_api_key('sk-ant-api03-test'))
self.assertTrue(self.adaptor.validate_api_key('  sk-ant-test  '))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_claude_adaptor.py:33*

### test_validate_api_key_invalid

**Category**: method_call  
**Description**: Test invalid API keys  
**Expected**: self.assertFalse(self.adaptor.validate_api_key('sk-proj-123'))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('claude')

self.assertFalse(self.adaptor.validate_api_key('AIzaSyABC123'))
self.assertFalse(self.adaptor.validate_api_key('sk-proj-123'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_claude_adaptor.py:38*

### test_validate_api_key_invalid

**Category**: method_call  
**Description**: Test invalid API keys  
**Expected**: self.assertFalse(self.adaptor.validate_api_key('invalid'))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('claude')

self.assertFalse(self.adaptor.validate_api_key('sk-proj-123'))
self.assertFalse(self.adaptor.validate_api_key('invalid'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_claude_adaptor.py:39*

### test_validate_api_key_invalid

**Category**: method_call  
**Description**: Test invalid API keys  
**Expected**: self.assertFalse(self.adaptor.validate_api_key(''))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('claude')

self.assertFalse(self.adaptor.validate_api_key('invalid'))
self.assertFalse(self.adaptor.validate_api_key(''))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_claude_adaptor.py:40*

### test_validate_api_key_invalid

**Category**: method_call  
**Description**: Test invalid API keys  
**Expected**: self.assertFalse(self.adaptor.validate_api_key('sk-test'))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('claude')

self.assertFalse(self.adaptor.validate_api_key(''))
self.assertFalse(self.adaptor.validate_api_key('sk-test'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_claude_adaptor.py:41*

### test_upload_invalid_file

**Category**: method_call  
**Description**: Test upload with invalid file  
**Expected**: self.assertIn('not found', result['message'].lower())  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('claude')

self.assertFalse(result['success'])
self.assertIn('not found', result['message'].lower())
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_claude_adaptor.py:195*

### test_analyze_python_workflow

**Category**: method_call  
**Description**: Test analysis of Python workflow with multiple steps  
**Expected**: self.assertIsInstance(steps[0], WorkflowStep)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.analyzer = WorkflowAnalyzer()

self.assertGreaterEqual(len(steps), 2)
self.assertIsInstance(steps[0], WorkflowStep)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_how_to_guide_builder.py:66*

### test_analyze_python_workflow

**Category**: method_call  
**Description**: Test analysis of Python workflow with multiple steps  
**Expected**: self.assertEqual(steps[0].step_number, 1)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.analyzer = WorkflowAnalyzer()

self.assertIsInstance(steps[0], WorkflowStep)
self.assertEqual(steps[0].step_number, 1)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_how_to_guide_builder.py:69*

### test_analyze_python_workflow

**Category**: method_call  
**Description**: Test analysis of Python workflow with multiple steps  
**Expected**: self.assertIsNotNone(steps[0].description)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.analyzer = WorkflowAnalyzer()

self.assertEqual(steps[0].step_number, 1)
self.assertIsNotNone(steps[0].description)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_how_to_guide_builder.py:70*

### test_analyze_python_workflow

**Category**: method_call  
**Description**: Test analysis of Python workflow with multiple steps  
**Expected**: self.assertIn('complexity_level', metadata)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.analyzer = WorkflowAnalyzer()

self.assertIsNotNone(steps[0].description)
self.assertIn('complexity_level', metadata)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_how_to_guide_builder.py:71*

### test_surface_detection_by_name

**Category**: method_call  
**Description**: Test surface detection using class name  
**Expected**: self.assertGreaterEqual(pattern.confidence, 0.6)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.detector = SingletonDetector(depth='deep')
self.recognizer = PatternRecognizer(depth='deep')

self.assertEqual(pattern.pattern_type, 'Singleton')
self.assertGreaterEqual(pattern.confidence, 0.6)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pattern_recognizer.py:48*

### test_surface_detection_by_name

**Category**: method_call  
**Description**: Test surface detection using class name  
**Expected**: self.assertIn('Singleton', pattern.class_name)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.detector = SingletonDetector(depth='deep')
self.recognizer = PatternRecognizer(depth='deep')

self.assertGreaterEqual(pattern.confidence, 0.6)
self.assertIn('Singleton', pattern.class_name)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pattern_recognizer.py:49*

### test_deep_detection_with_instance_method

**Category**: method_call  
**Description**: Test deep detection with getInstance() method  
**Expected**: self.assertEqual(report.language, 'Python')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.detector = SingletonDetector(depth='deep')
self.recognizer = PatternRecognizer(depth='deep')

self.assertIsNotNone(report)
self.assertEqual(report.language, 'Python')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pattern_recognizer.py:66*

### test_python_singleton_with_new

**Category**: method_call  
**Description**: Test Python-specific __new__ singleton pattern  
**Expected**: self.assertGreaterEqual(report.total_classes, 1)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.detector = SingletonDetector(depth='deep')
self.recognizer = PatternRecognizer(depth='deep')

self.assertIsNotNone(report)
self.assertGreaterEqual(report.total_classes, 1)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pattern_recognizer.py:84*

### test_surface_detection_by_name

**Category**: method_call  
**Description**: Test surface detection using class name  
**Expected**: self.assertIn('Factory', pattern.class_name)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.detector = FactoryDetector(depth='deep')
self.recognizer = PatternRecognizer(depth='deep')

self.assertGreaterEqual(pattern.confidence, 0.5)
self.assertIn('Factory', pattern.class_name)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pattern_recognizer.py:130*

### test_analyze_singleton_code

**Category**: method_call  
**Description**: Test end-to-end Singleton analysis  
**Expected**: self.assertEqual(report.language, 'Python')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.recognizer = PatternRecognizer(depth='deep')

self.assertEqual(report.file_path, 'config.py')
self.assertEqual(report.language, 'Python')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pattern_recognizer.py:284*

### test_analyze_singleton_code

**Category**: method_call  
**Description**: Test end-to-end Singleton analysis  
**Expected**: self.assertGreater(len(report.patterns), 0)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.recognizer = PatternRecognizer(depth='deep')

self.assertEqual(report.language, 'Python')
self.assertGreater(len(report.patterns), 0)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pattern_recognizer.py:285*

### test_analyze_singleton_code

**Category**: method_call  
**Description**: Test end-to-end Singleton analysis  
**Expected**: self.assertGreater(report.total_classes, 0)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.recognizer = PatternRecognizer(depth='deep')

self.assertGreater(len(report.patterns), 0)
self.assertGreater(report.total_classes, 0)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pattern_recognizer.py:286*

### test_python_patterns

**Category**: method_call  
**Description**: Test Python-specific patterns  
**Expected**: self.assertEqual(report.language, 'Python')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.recognizer = PatternRecognizer(depth='deep')

self.assertIsNotNone(report)
self.assertEqual(report.language, 'Python')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pattern_recognizer.py:372*

### test_python_decorator_boost

**Category**: method_call  
**Description**: Test Python @decorator syntax boost  
**Expected**: self.assertIn('Python @decorator', ' '.join(adapted.evidence))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertGreater(adapted.confidence, 0.6)
self.assertIn('Python @decorator', ' '.join(adapted.evidence))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pattern_recognizer.py:500*

### test_doc_scraper_uses_modern_commands

**Category**: method_call  
**Description**: Test doc_scraper.py uses skill-seekers commands  
**Expected**: self.assertNotIn('python3 cli/doc_scraper.py', content)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIn('skill-seekers scrape', content)
self.assertNotIn('python3 cli/doc_scraper.py', content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_cli_paths.py:30*

### test_enhance_skill_local_uses_modern_commands

**Category**: method_call  
**Description**: Test enhance_skill_local.py uses skill-seekers commands  
**Expected**: self.assertNotIn('python3 cli/enhance_skill_local.py', content)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIn('skill-seekers', content)
self.assertNotIn('python3 cli/enhance_skill_local.py', content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_cli_paths.py:49*

### test_estimate_pages_uses_modern_commands

**Category**: method_call  
**Description**: Test estimate_pages.py uses skill-seekers commands  
**Expected**: self.assertNotIn('python3 cli/estimate_pages.py', content)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIn('skill-seekers estimate', content)
self.assertNotIn('python3 cli/estimate_pages.py', content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_cli_paths.py:64*

### test_package_skill_uses_modern_commands

**Category**: method_call  
**Description**: Test package_skill.py uses skill-seekers commands  
**Expected**: self.assertNotIn('python3 cli/package_skill.py', content)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIn('skill-seekers package', content)
self.assertNotIn('python3 cli/package_skill.py', content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_cli_paths.py:79*

### test_github_scraper_uses_modern_commands

**Category**: method_call  
**Description**: Test github_scraper.py uses skill-seekers commands  
**Expected**: self.assertNotIn('python3 cli/github_scraper.py', content)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIn('skill-seekers', content)
self.assertNotIn('python3 cli/github_scraper.py', content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_cli_paths.py:94*

### test_doc_scraper_uses_modern_commands

**Category**: method_call  
**Description**: Test doc_scraper.py uses skill-seekers commands  
**Expected**: self.assertNotIn('python3 cli/doc_scraper.py', content)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIn('skill-seekers scrape', content)
self.assertNotIn('python3 cli/doc_scraper.py', content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_cli_paths.py:30*

### test_enhance_skill_local_uses_modern_commands

**Category**: method_call  
**Description**: Test enhance_skill_local.py uses skill-seekers commands  
**Expected**: self.assertNotIn('python3 cli/enhance_skill_local.py', content)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIn('skill-seekers', content)
self.assertNotIn('python3 cli/enhance_skill_local.py', content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_cli_paths.py:49*

### test_estimate_pages_uses_modern_commands

**Category**: method_call  
**Description**: Test estimate_pages.py uses skill-seekers commands  
**Expected**: self.assertNotIn('python3 cli/estimate_pages.py', content)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIn('skill-seekers estimate', content)
self.assertNotIn('python3 cli/estimate_pages.py', content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_cli_paths.py:64*

### test_package_skill_uses_modern_commands

**Category**: method_call  
**Description**: Test package_skill.py uses skill-seekers commands  
**Expected**: self.assertNotIn('python3 cli/package_skill.py', content)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIn('skill-seekers package', content)
self.assertNotIn('python3 cli/package_skill.py', content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_cli_paths.py:79*

### test_github_scraper_uses_modern_commands

**Category**: method_call  
**Description**: Test github_scraper.py uses skill-seekers commands  
**Expected**: self.assertNotIn('python3 cli/github_scraper.py', content)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIn('skill-seekers', content)
self.assertNotIn('python3 cli/github_scraper.py', content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_cli_paths.py:94*

### mock_github_repo

**Category**: method_call  
**Description**: Create mock GitHub repository structure.  
**Expected**: (tests_dir / 'test_auth.py').write_text("\ndef test_google_provider():\n    provider = google_provider('id', 'secret')\n    assert provider.name == 'google'\n\ndef test_azure_provider():\n    provider = azure_provider('tenant', 'id')\n    assert provider.name == 'azure'\n")  
**Confidence**: 0.85  
**Tags**: pytest, mock  

```python
# Setup
# Fixtures: tmp_path

tests_dir.mkdir()
(tests_dir / 'test_auth.py').write_text("\ndef test_google_provider():\n    provider = google_provider('id', 'secret')\n    assert provider.name == 'google'\n\ndef test_azure_provider():\n    provider = azure_provider('tenant', 'id')\n    assert provider.name == 'azure'\n")
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_architecture_scenarios.py:98*

### local_codebase

**Category**: method_call  
**Description**: Create local codebase for testing.  
**Expected**: (tests_dir / 'test_database.py').write_text("\ndef test_connection():\n    conn = DatabaseConnection('localhost', 5432)\n    assert conn.host == 'localhost'\n")  
**Confidence**: 0.85  
**Tags**: pytest  

```python
# Setup
# Fixtures: tmp_path

tests_dir.mkdir()
(tests_dir / 'test_database.py').write_text("\ndef test_connection():\n    conn = DatabaseConnection('localhost', 5432)\n    assert conn.host == 'localhost'\n")
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_architecture_scenarios.py:709*

### test_github_overhead_within_limits

**Category**: method_call  
**Description**: Test GitHub overhead is 20-60 lines (Architecture Section 8.3, Line 2017).  
**Expected**: assert 20 <= github_overhead <= 60, f'GitHub overhead {github_overhead} not in range 20-60'  
**Confidence**: 0.85  

```python
print(f'\nGitHub overhead: {github_overhead} lines')
assert 20 <= github_overhead <= 60, f'GitHub overhead {github_overhead} not in range 20-60'
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_architecture_scenarios.py:943*

### test_token_efficiency_calculation

**Category**: method_call  
**Description**: Calculate token efficiency with GitHub overhead.  
**Expected**: assert reduction_percent >= 29, f'Token reduction {reduction_percent:.1f}% below 29% (conservative target)'  
**Confidence**: 0.85  

```python
print('Target: 35-40%')
assert reduction_percent >= 29, f'Token reduction {reduction_percent:.1f}% below 29% (conservative target)'
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_architecture_scenarios.py:1048*

### test_detect_python_with_confidence

**Category**: method_call  
**Description**: Test Python detection returns language and confidence  
**Expected**: self.assertGreater(confidence, 0.4)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from skill_seekers.cli.pdf_extractor_poc import PDFExtractor
self.PDFExtractor = PDFExtractor

self.assertEqual(language, 'python')
self.assertGreater(confidence, 0.4)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_extractor.py:52*

### test_detect_python_with_confidence

**Category**: method_call  
**Description**: Test Python detection returns language and confidence  
**Expected**: self.assertLessEqual(confidence, 1.0)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from skill_seekers.cli.pdf_extractor_poc import PDFExtractor
self.PDFExtractor = PDFExtractor

self.assertGreater(confidence, 0.4)
self.assertLessEqual(confidence, 1.0)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_extractor.py:53*

### test_detect_javascript_with_confidence

**Category**: method_call  
**Description**: Test JavaScript detection  
**Expected**: self.assertGreater(confidence, 0.5)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from skill_seekers.cli.pdf_extractor_poc import PDFExtractor
self.PDFExtractor = PDFExtractor

self.assertEqual(language, 'javascript')
self.assertGreater(confidence, 0.5)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_extractor.py:68*

### test_detect_cpp_with_confidence

**Category**: method_call  
**Description**: Test C++ detection  
**Expected**: self.assertGreater(confidence, 0.5)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from skill_seekers.cli.pdf_extractor_poc import PDFExtractor
self.PDFExtractor = PDFExtractor

self.assertEqual(language, 'cpp')
self.assertGreater(confidence, 0.5)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_extractor.py:83*

### test_detect_unknown_low_confidence

**Category**: method_call  
**Description**: Test unknown language returns low confidence  
**Expected**: self.assertLess(confidence, 0.3)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from skill_seekers.cli.pdf_extractor_poc import PDFExtractor
self.PDFExtractor = PDFExtractor

self.assertEqual(language, 'unknown')
self.assertLess(confidence, 0.3)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_extractor.py:98*

### test_validate_python_valid

**Category**: method_call  
**Description**: Test valid Python syntax  
**Expected**: self.assertEqual(len(issues), 0)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from skill_seekers.cli.pdf_extractor_poc import PDFExtractor
self.PDFExtractor = PDFExtractor

self.assertTrue(is_valid)
self.assertEqual(len(issues), 0)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_extractor.py:140*

### test_validate_python_invalid_indentation

**Category**: method_call  
**Description**: Test invalid Python indentation  
**Expected**: self.assertGreater(len(issues), 0)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from skill_seekers.cli.pdf_extractor_poc import PDFExtractor
self.PDFExtractor = PDFExtractor

self.assertFalse(is_valid)
self.assertGreater(len(issues), 0)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_extractor.py:150*

### test_validate_python_unbalanced_brackets

**Category**: method_call  
**Description**: Test unbalanced brackets  
**Expected**: self.assertGreater(len(issues), 0)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from skill_seekers.cli.pdf_extractor_poc import PDFExtractor
self.PDFExtractor = PDFExtractor

self.assertFalse(is_valid)
self.assertGreater(len(issues), 0)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_extractor.py:160*

### test_validate_javascript_valid

**Category**: method_call  
**Description**: Test valid JavaScript syntax  
**Expected**: self.assertEqual(len(issues), 0)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from skill_seekers.cli.pdf_extractor_poc import PDFExtractor
self.PDFExtractor = PDFExtractor

self.assertTrue(is_valid)
self.assertEqual(len(issues), 0)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_extractor.py:170*

### test_validate_natural_language_fails

**Category**: method_call  
**Description**: Test natural language fails validation  
**Expected**: self.assertIn('May be natural language', ' '.join(issues))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from skill_seekers.cli.pdf_extractor_poc import PDFExtractor
self.PDFExtractor = PDFExtractor

self.assertFalse(is_valid)
self.assertIn('May be natural language', ' '.join(issues))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_extractor.py:180*

### test_detect_json_files

**Category**: method_call  
**Description**: Test detection of JSON config files  
**Expected**: self.assertTrue(any(('package.json' in f for f in filenames)))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.detector = ConfigFileDetector()
self.temp_dir = tempfile.mkdtemp()

self.assertTrue(any(('config.json' in f for f in filenames)))
self.assertTrue(any(('package.json' in f for f in filenames)))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_config_extractor.py:59*

### test_parse_json_config

**Category**: method_call  
**Description**: Test parsing JSON configuration  
**Expected**: self.assertGreater(len(config_file.settings), 0)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.parser = ConfigParser()
self.temp_dir = tempfile.mkdtemp()

self.parser.parse_config_file(config_file)
self.assertGreater(len(config_file.settings), 0)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_config_extractor.py:130*

### test_parse_env_file

**Category**: method_call  
**Description**: Test parsing .env file  
**Expected**: self.assertGreater(len(config_file.settings), 0)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.parser = ConfigParser()
self.temp_dir = tempfile.mkdtemp()

self.parser.parse_config_file(config_file)
self.assertGreater(len(config_file.settings), 0)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_config_extractor.py:185*

### test_parse_env_file

**Category**: method_call  
**Description**: Test parsing .env file  
**Expected**: self.assertEqual(db_url[0].value, 'postgresql://localhost:5432/db')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.parser = ConfigParser()
self.temp_dir = tempfile.mkdtemp()

self.assertEqual(len(db_url), 1)
self.assertEqual(db_url[0].value, 'postgresql://localhost:5432/db')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_config_extractor.py:190*

### test_parse_ini_file

**Category**: method_call  
**Description**: Test parsing INI file  
**Expected**: self.assertGreater(len(config_file.settings), 0)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.parser = ConfigParser()
self.temp_dir = tempfile.mkdtemp()

self.parser.parse_config_file(config_file)
self.assertGreater(len(config_file.settings), 0)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_config_extractor.py:213*

### test_parse_python_config

**Category**: method_call  
**Description**: Test parsing Python config module  
**Expected**: self.assertGreater(len(config_file.settings), 0)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.parser = ConfigParser()
self.temp_dir = tempfile.mkdtemp()

self.parser.parse_config_file(config_file)
self.assertGreater(len(config_file.settings), 0)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_config_extractor.py:235*

### test_parse_javascript_config

**Category**: method_call  
**Description**: Test parsing JavaScript config file  
**Expected**: self.assertIsNotNone(config_file.settings)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.parser = ConfigParser()
self.temp_dir = tempfile.mkdtemp()

self.parser.parse_config_file(config_file)
self.assertIsNotNone(config_file.settings)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_config_extractor.py:288*

### test_extract_from_directory

**Category**: method_call  
**Description**: Test extraction from directory with multiple config files  
**Expected**: self.assertEqual(result.total_files, len(result.config_files))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.extractor = ConfigExtractor()
self.temp_dir = tempfile.mkdtemp()

self.assertGreater(len(result.config_files), 0)
self.assertEqual(result.total_files, len(result.config_files))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_config_extractor.py:497*

### test_generate_markdown_output

**Category**: method_call  
**Description**: Test markdown output generation  
**Expected**: self.assertIn('config.json', markdown)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.extractor = ConfigExtractor()
self.temp_dir = tempfile.mkdtemp()

self.assertIn('Configuration Extraction Report', markdown)
self.assertIn('config.json', markdown)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_config_extractor.py:520*

### test_generate_markdown_output

**Category**: method_call  
**Description**: Test markdown output generation  
**Expected**: self.assertIn('database_config', markdown)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.extractor = ConfigExtractor()
self.temp_dir = tempfile.mkdtemp()

self.assertIn('config.json', markdown)
self.assertIn('database_config', markdown)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_config_extractor.py:521*

### test_detect_terminal_with_skill_seeker_env

**Category**: method_call  
**Description**: Test that SKILL_SEEKER_TERMINAL env var takes highest priority.  
**Expected**: self.assertEqual(detection_method, 'SKILL_SEEKER_TERMINAL')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Save original environment variables.'
self.original_skill_seeker = os.environ.get('SKILL_SEEKER_TERMINAL')
self.original_term_program = os.environ.get('TERM_PROGRAM')

self.assertEqual(terminal_app, 'Ghostty')
self.assertEqual(detection_method, 'SKILL_SEEKER_TERMINAL')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_terminal_detection.py:53*

### test_detect_terminal_with_term_program_known

**Category**: method_call  
**Description**: Test detection from TERM_PROGRAM with known terminal (iTerm).  
**Expected**: self.assertEqual(detection_method, 'TERM_PROGRAM')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Save original environment variables.'
self.original_skill_seeker = os.environ.get('SKILL_SEEKER_TERMINAL')
self.original_term_program = os.environ.get('TERM_PROGRAM')

self.assertEqual(terminal_app, 'iTerm')
self.assertEqual(detection_method, 'TERM_PROGRAM')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_terminal_detection.py:66*

### test_detect_terminal_with_term_program_ghostty

**Category**: method_call  
**Description**: Test detection from TERM_PROGRAM with Ghostty terminal.  
**Expected**: self.assertEqual(detection_method, 'TERM_PROGRAM')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Save original environment variables.'
self.original_skill_seeker = os.environ.get('SKILL_SEEKER_TERMINAL')
self.original_term_program = os.environ.get('TERM_PROGRAM')

self.assertEqual(terminal_app, 'Ghostty')
self.assertEqual(detection_method, 'TERM_PROGRAM')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_terminal_detection.py:78*

### test_detect_terminal_with_term_program_apple_terminal

**Category**: method_call  
**Description**: Test detection from TERM_PROGRAM with Apple Terminal.  
**Expected**: self.assertEqual(detection_method, 'TERM_PROGRAM')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Save original environment variables.'
self.original_skill_seeker = os.environ.get('SKILL_SEEKER_TERMINAL')
self.original_term_program = os.environ.get('TERM_PROGRAM')

self.assertEqual(terminal_app, 'Terminal')
self.assertEqual(detection_method, 'TERM_PROGRAM')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_terminal_detection.py:90*

### test_detect_terminal_with_term_program_wezterm

**Category**: method_call  
**Description**: Test detection from TERM_PROGRAM with WezTerm.  
**Expected**: self.assertEqual(detection_method, 'TERM_PROGRAM')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Save original environment variables.'
self.original_skill_seeker = os.environ.get('SKILL_SEEKER_TERMINAL')
self.original_term_program = os.environ.get('TERM_PROGRAM')

self.assertEqual(terminal_app, 'WezTerm')
self.assertEqual(detection_method, 'TERM_PROGRAM')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_terminal_detection.py:102*

### test_detect_terminal_with_term_program_unknown

**Category**: method_call  
**Description**: Test fallback behavior when TERM_PROGRAM is unknown (e.g., IDE terminals).  
**Expected**: self.assertEqual(detection_method, 'unknown TERM_PROGRAM (zed)')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Save original environment variables.'
self.original_skill_seeker = os.environ.get('SKILL_SEEKER_TERMINAL')
self.original_term_program = os.environ.get('TERM_PROGRAM')

self.assertEqual(terminal_app, 'Terminal')
self.assertEqual(detection_method, 'unknown TERM_PROGRAM (zed)')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_terminal_detection.py:114*

### test_detect_terminal_default_fallback

**Category**: method_call  
**Description**: Test default fallback when no environment variables are set.  
**Expected**: self.assertEqual(detection_method, 'default')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Save original environment variables.'
self.original_skill_seeker = os.environ.get('SKILL_SEEKER_TERMINAL')
self.original_term_program = os.environ.get('TERM_PROGRAM')

self.assertEqual(terminal_app, 'Terminal')
self.assertEqual(detection_method, 'default')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_terminal_detection.py:127*

### test_detect_terminal_priority_order

**Category**: method_call  
**Description**: Test that SKILL_SEEKER_TERMINAL takes priority over TERM_PROGRAM.  
**Expected**: self.assertEqual(detection_method, 'SKILL_SEEKER_TERMINAL')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Save original environment variables.'
self.original_skill_seeker = os.environ.get('SKILL_SEEKER_TERMINAL')
self.original_term_program = os.environ.get('TERM_PROGRAM')

self.assertEqual(terminal_app, 'Ghostty')
self.assertEqual(detection_method, 'SKILL_SEEKER_TERMINAL')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_terminal_detection.py:138*

### test_detect_terminal_whitespace_handling

**Category**: method_call  
**Description**: Test that whitespace is stripped from environment variables.  
**Expected**: self.assertEqual(detection_method, 'SKILL_SEEKER_TERMINAL')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Save original environment variables.'
self.original_skill_seeker = os.environ.get('SKILL_SEEKER_TERMINAL')
self.original_term_program = os.environ.get('TERM_PROGRAM')

self.assertEqual(terminal_app, 'Ghostty')
self.assertEqual(detection_method, 'SKILL_SEEKER_TERMINAL')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_terminal_detection.py:191*

### test_detect_terminal_empty_string_env_vars

**Category**: method_call  
**Description**: Test that empty string env vars fall through to next priority.  
**Expected**: self.assertEqual(detection_method, 'TERM_PROGRAM')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Save original environment variables.'
self.original_skill_seeker = os.environ.get('SKILL_SEEKER_TERMINAL')
self.original_term_program = os.environ.get('TERM_PROGRAM')

self.assertEqual(terminal_app, 'iTerm')
self.assertEqual(detection_method, 'TERM_PROGRAM')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_terminal_detection.py:202*

### test_c3_reference_directory_structure

**Category**: method_call  
**Description**: Test correct C3.x reference directory structure is created.  
**Expected**: assert os.path.exists(os.path.join(c3_dir, 'ARCHITECTURE.md'))  
**Confidence**: 0.85  
**Tags**: mock  

```python
# Setup
# Fixtures: mock_config, mock_c3_data, temp_dir

builder._copy_architecture_details(c3_dir, mock_c3_data.get('architecture'))
assert os.path.exists(os.path.join(c3_dir, 'ARCHITECTURE.md'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_c3_integration.py:240*

### test_class_formatting

**Category**: method_call  
**Description**: Test markdown formatting for class signatures.  
**Expected**: self.assertIn('A simple calculator class', content)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test environment'
self.temp_dir = tempfile.mkdtemp()
self.output_dir = Path(self.temp_dir) / 'api_reference'

self.assertIn('### Calculator', content)
self.assertIn('A simple calculator class', content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_api_reference_builder.py:81*

### test_class_formatting

**Category**: method_call  
**Description**: Test markdown formatting for class signatures.  
**Expected**: self.assertIn('**Inherits from**: object', content)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test environment'
self.temp_dir = tempfile.mkdtemp()
self.output_dir = Path(self.temp_dir) / 'api_reference'

self.assertIn('A simple calculator class', content)
self.assertIn('**Inherits from**: object', content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_api_reference_builder.py:82*

### test_class_formatting

**Category**: method_call  
**Description**: Test markdown formatting for class signatures.  
**Expected**: self.assertIn('##### add', content)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test environment'
self.temp_dir = tempfile.mkdtemp()
self.output_dir = Path(self.temp_dir) / 'api_reference'

self.assertIn('**Inherits from**: object', content)
self.assertIn('##### add', content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_api_reference_builder.py:83*

### test_class_formatting

**Category**: method_call  
**Description**: Test markdown formatting for class signatures.  
**Expected**: self.assertIn('Add two numbers', content)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test environment'
self.temp_dir = tempfile.mkdtemp()
self.output_dir = Path(self.temp_dir) / 'api_reference'

self.assertIn('##### add', content)
self.assertIn('Add two numbers', content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_api_reference_builder.py:84*

### test_function_formatting

**Category**: method_call  
**Description**: Test markdown formatting for function signatures.  
**Expected**: self.assertIn('### calculate_sum', content)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test environment'
self.temp_dir = tempfile.mkdtemp()
self.output_dir = Path(self.temp_dir) / 'api_reference'

self.assertIn('## Functions', content)
self.assertIn('### calculate_sum', content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_api_reference_builder.py:119*

### test_function_formatting

**Category**: method_call  
**Description**: Test markdown formatting for function signatures.  
**Expected**: self.assertIn('Calculate sum of numbers', content)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test environment'
self.temp_dir = tempfile.mkdtemp()
self.output_dir = Path(self.temp_dir) / 'api_reference'

self.assertIn('### calculate_sum', content)
self.assertIn('Calculate sum of numbers', content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_api_reference_builder.py:120*

### test_function_formatting

**Category**: method_call  
**Description**: Test markdown formatting for function signatures.  
**Expected**: self.assertIn('**Returns**: `int`', content)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test environment'
self.temp_dir = tempfile.mkdtemp()
self.output_dir = Path(self.temp_dir) / 'api_reference'

self.assertIn('Calculate sum of numbers', content)
self.assertIn('**Returns**: `int`', content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_api_reference_builder.py:121*

### test_parameter_table_generation

**Category**: method_call  
**Description**: Test parameter table formatting.  
**Expected**: self.assertIn('| Name | Type | Default | Description |', content)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test environment'
self.temp_dir = tempfile.mkdtemp()
self.output_dir = Path(self.temp_dir) / 'api_reference'

self.assertIn('**Parameters**:', content)
self.assertIn('| Name | Type | Default | Description |', content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_api_reference_builder.py:158*

### test_init_with_repo_name

**Category**: method_call  
**Description**: Test initialization with repository name  
**Expected**: self.assertEqual(scraper.name, 'react')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not PYGITHUB_AVAILABLE:
    self.skipTest('PyGithub not installed')
from skill_seekers.cli.github_scraper import GitHubScraper
self.GitHubScraper = GitHubScraper
self.temp_dir = tempfile.mkdtemp()
self.output_dir = Path(self.temp_dir)

self.assertEqual(scraper.repo_name, 'facebook/react')
self.assertEqual(scraper.name, 'react')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_github_scraper.py:59*

### test_init_with_repo_name

**Category**: method_call  
**Description**: Test initialization with repository name  
**Expected**: self.assertIsNotNone(scraper.github)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not PYGITHUB_AVAILABLE:
    self.skipTest('PyGithub not installed')
from skill_seekers.cli.github_scraper import GitHubScraper
self.GitHubScraper = GitHubScraper
self.temp_dir = tempfile.mkdtemp()
self.output_dir = Path(self.temp_dir)

self.assertEqual(scraper.name, 'react')
self.assertIsNotNone(scraper.github)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_github_scraper.py:60*

### test_init_with_repo_name

**Category**: method_call  
**Description**: Test initialization with repository name  
**Expected**: self.assertEqual(scraper.name, 'react')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(scraper.repo_name, 'facebook/react')
self.assertEqual(scraper.name, 'react')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_github_scraper.py:59*

### test_init_with_repo_name

**Category**: method_call  
**Description**: Test initialization with repository name  
**Expected**: self.assertIsNotNone(scraper.github)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(scraper.name, 'react')
self.assertIsNotNone(scraper.github)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_github_scraper.py:60*

### test_javascript_detection

**Category**: method_call  
**Description**: Test JavaScript file detection.  
**Expected**: self.assertEqual(detect_language(Path('test.jsx')), 'JavaScript')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(detect_language(Path('test.js')), 'JavaScript')
self.assertEqual(detect_language(Path('test.jsx')), 'JavaScript')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_codebase_scraper.py:40*

### test_typescript_detection

**Category**: method_call  
**Description**: Test TypeScript file detection.  
**Expected**: self.assertEqual(detect_language(Path('test.tsx')), 'TypeScript')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(detect_language(Path('test.ts')), 'TypeScript')
self.assertEqual(detect_language(Path('test.tsx')), 'TypeScript')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_codebase_scraper.py:45*

### test_cpp_detection

**Category**: method_call  
**Description**: Test C++ file detection.  
**Expected**: self.assertEqual(detect_language(Path('test.h')), 'C++')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(detect_language(Path('test.cpp')), 'C++')
self.assertEqual(detect_language(Path('test.h')), 'C++')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_codebase_scraper.py:50*

### test_cpp_detection

**Category**: method_call  
**Description**: Test C++ file detection.  
**Expected**: self.assertEqual(detect_language(Path('test.hpp')), 'C++')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(detect_language(Path('test.h')), 'C++')
self.assertEqual(detect_language(Path('test.hpp')), 'C++')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_codebase_scraper.py:51*

### test_unknown_language

**Category**: method_call  
**Description**: Test unknown file extension.  
**Expected**: self.assertEqual(detect_language(Path('test.txt')), 'Unknown')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(detect_language(Path('test.swift')), 'Unknown')
self.assertEqual(detect_language(Path('test.txt')), 'Unknown')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_codebase_scraper.py:80*

### test_normal_dir_not_excluded

**Category**: method_call  
**Description**: Test that normal directories are not excluded.  
**Expected**: self.assertFalse(should_exclude_dir('tests', DEFAULT_EXCLUDED_DIRS))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertFalse(should_exclude_dir('src', DEFAULT_EXCLUDED_DIRS))
self.assertFalse(should_exclude_dir('tests', DEFAULT_EXCLUDED_DIRS))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_codebase_scraper.py:101*

### test_walk_with_python_files

**Category**: method_call  
**Description**: Test walking directory with Python files.  
**Expected**: self.assertTrue(all((f.suffix == '.py' for f in files)))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test environment'
self.temp_dir = tempfile.mkdtemp()
self.root = Path(self.temp_dir)

self.assertEqual(len(files), 2)
self.assertTrue(all((f.suffix == '.py' for f in files)))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_codebase_scraper.py:132*

### test_walk_excludes_node_modules

**Category**: method_call  
**Description**: Test that node_modules directory is excluded.  
**Expected**: self.assertEqual(files[0].name, 'test.py')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test environment'
self.temp_dir = tempfile.mkdtemp()
self.root = Path(self.temp_dir)

self.assertEqual(len(files), 1)
self.assertEqual(files[0].name, 'test.py')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_codebase_scraper.py:148*

### test_walk_with_subdirectories

**Category**: method_call  
**Description**: Test walking nested directory structure.  
**Expected**: self.assertIn('test_module.py', filenames)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test environment'
self.temp_dir = tempfile.mkdtemp()
self.root = Path(self.temp_dir)

self.assertIn('module.py', filenames)
self.assertIn('test_module.py', filenames)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_codebase_scraper.py:167*

### test_javascript_detection

**Category**: method_call  
**Description**: Test JavaScript file detection.  
**Expected**: self.assertEqual(detect_language(Path('test.jsx')), 'JavaScript')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(detect_language(Path('test.js')), 'JavaScript')
self.assertEqual(detect_language(Path('test.jsx')), 'JavaScript')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_codebase_scraper.py:40*

### test_extract_headings_h2_to_h6

**Category**: method_call  
**Description**: Test extracting h2-h6 headings (not h1).  
**Expected**: self.assertEqual(result['headings'][0]['level'], 'h2')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test fixtures.'
from skill_seekers.cli.doc_scraper import DocToSkillConverter
self.config = {'name': 'test_md_parsing', 'base_url': 'https://example.com', 'selectors': {}, 'url_patterns': {'include': [], 'exclude': []}, 'categories': {}}
self.converter = DocToSkillConverter(self.config)

self.assertEqual(len(result['headings']), 5)
self.assertEqual(result['headings'][0]['level'], 'h2')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_markdown_parsing.py:58*

### test_extract_headings_h2_to_h6

**Category**: method_call  
**Description**: Test extracting h2-h6 headings (not h1).  
**Expected**: self.assertEqual(result['headings'][0]['text'], 'Section One')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test fixtures.'
from skill_seekers.cli.doc_scraper import DocToSkillConverter
self.config = {'name': 'test_md_parsing', 'base_url': 'https://example.com', 'selectors': {}, 'url_patterns': {'include': [], 'exclude': []}, 'categories': {}}
self.converter = DocToSkillConverter(self.config)

self.assertEqual(result['headings'][0]['level'], 'h2')
self.assertEqual(result['headings'][0]['text'], 'Section One')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_markdown_parsing.py:59*

### test_extract_code_blocks_with_language

**Category**: method_call  
**Description**: Test extracting code blocks with language tags.  
**Expected**: self.assertEqual(result['code_samples'][0]['language'], 'python')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test fixtures.'
from skill_seekers.cli.doc_scraper import DocToSkillConverter
self.config = {'name': 'test_md_parsing', 'base_url': 'https://example.com', 'selectors': {}, 'url_patterns': {'include': [], 'exclude': []}, 'categories': {}}
self.converter = DocToSkillConverter(self.config)

self.assertEqual(len(result['code_samples']), 3)
self.assertEqual(result['code_samples'][0]['language'], 'python')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_markdown_parsing.py:82*

### test_extract_code_blocks_with_language

**Category**: method_call  
**Description**: Test extracting code blocks with language tags.  
**Expected**: self.assertEqual(result['code_samples'][1]['language'], 'javascript')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test fixtures.'
from skill_seekers.cli.doc_scraper import DocToSkillConverter
self.config = {'name': 'test_md_parsing', 'base_url': 'https://example.com', 'selectors': {}, 'url_patterns': {'include': [], 'exclude': []}, 'categories': {}}
self.converter = DocToSkillConverter(self.config)

self.assertEqual(result['code_samples'][0]['language'], 'python')
self.assertEqual(result['code_samples'][1]['language'], 'javascript')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_markdown_parsing.py:83*

### test_extract_code_blocks_with_language

**Category**: method_call  
**Description**: Test extracting code blocks with language tags.  
**Expected**: self.assertEqual(result['code_samples'][2]['language'], 'unknown')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test fixtures.'
from skill_seekers.cli.doc_scraper import DocToSkillConverter
self.config = {'name': 'test_md_parsing', 'base_url': 'https://example.com', 'selectors': {}, 'url_patterns': {'include': [], 'exclude': []}, 'categories': {}}
self.converter = DocToSkillConverter(self.config)

self.assertEqual(result['code_samples'][1]['language'], 'javascript')
self.assertEqual(result['code_samples'][2]['language'], 'unknown')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_markdown_parsing.py:84*

### test_extract_content_paragraphs

**Category**: method_call  
**Description**: Test extracting paragraph content.  
**Expected**: self.assertNotIn('Short.', result['content'])  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test fixtures.'
from skill_seekers.cli.doc_scraper import DocToSkillConverter
self.config = {'name': 'test_md_parsing', 'base_url': 'https://example.com', 'selectors': {}, 'url_patterns': {'include': [], 'exclude': []}, 'categories': {}}
self.converter = DocToSkillConverter(self.config)

self.assertIn('paragraph with enough content', result['content'])
self.assertNotIn('Short.', result['content'])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_markdown_parsing.py:114*

### test_extract_markdown_style_links

**Category**: method_call  
**Description**: Test extracting [text](url) style links.  
**Expected**: self.assertIn('https://docs.example.com/api/index.md', urls)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIn('https://docs.example.com/start.md', urls)
self.assertIn('https://docs.example.com/api/index.md', urls)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_markdown_parsing.py:212*

### test_extract_markdown_style_links

**Category**: method_call  
**Description**: Test extracting [text](url) style links.  
**Expected**: self.assertIn('https://docs.example.com/advanced.md', urls)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIn('https://docs.example.com/api/index.md', urls)
self.assertIn('https://docs.example.com/advanced.md', urls)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_markdown_parsing.py:213*

### test_extract_bare_urls

**Category**: method_call  
**Description**: Test extracting bare URLs without markdown syntax.  
**Expected**: self.assertIn('https://example.com/api/reference.md', urls)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIn('https://example.com/docs/guide.md', urls)
self.assertIn('https://example.com/api/reference.md', urls)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_markdown_parsing.py:227*

### test_save_content_over_50_chars

**Category**: method_call  
**Description**: Test that pages with content >= 50 chars are saved.  
**Expected**: self.assertEqual(len(os.listdir(pages_dir)), 1)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test fixtures.'
from skill_seekers.cli.doc_scraper import DocToSkillConverter
self.config = {'name': 'test_save_filter', 'base_url': 'https://example.com', 'selectors': {}, 'url_patterns': {'include': [], 'exclude': []}, 'categories': {}}
self.converter = DocToSkillConverter(self.config)

self.assertTrue(os.path.exists(pages_dir))
self.assertEqual(len(os.listdir(pages_dir)), 1)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_markdown_parsing.py:357*

### test_exponential_backoff

**Category**: method_call  
**Description**: Test that exponential backoff delays are correct  
**Expected**: mock_sleep.assert_any_call(2)  
**Confidence**: 0.85  
**Tags**: mock  

```python
mock_sleep.assert_any_call(1)
mock_sleep.assert_any_call(2)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_llms_txt_downloader.py:102*

### test_defaults_exclude_common_dirs

**Category**: method_call  
**Description**: Test that default exclusions work correctly.  
**Expected**: self.assertTrue(scraper.should_exclude_dir('node_modules'))  
**Confidence**: 0.85  
**Tags**: unittest, mock  

```python
self.assertTrue(scraper.should_exclude_dir('venv'))
self.assertTrue(scraper.should_exclude_dir('node_modules'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_excluded_dirs_config.py:33*

### test_defaults_exclude_common_dirs

**Category**: method_call  
**Description**: Test that default exclusions work correctly.  
**Expected**: self.assertTrue(scraper.should_exclude_dir('__pycache__'))  
**Confidence**: 0.85  
**Tags**: unittest, mock  

```python
self.assertTrue(scraper.should_exclude_dir('node_modules'))
self.assertTrue(scraper.should_exclude_dir('__pycache__'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_excluded_dirs_config.py:34*

### test_defaults_exclude_common_dirs

**Category**: method_call  
**Description**: Test that default exclusions work correctly.  
**Expected**: self.assertTrue(scraper.should_exclude_dir('.git'))  
**Confidence**: 0.85  
**Tags**: unittest, mock  

```python
self.assertTrue(scraper.should_exclude_dir('__pycache__'))
self.assertTrue(scraper.should_exclude_dir('.git'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_excluded_dirs_config.py:35*

### test_defaults_exclude_common_dirs

**Category**: method_call  
**Description**: Test that default exclusions work correctly.  
**Expected**: self.assertTrue(scraper.should_exclude_dir('build'))  
**Confidence**: 0.85  
**Tags**: unittest, mock  

```python
self.assertTrue(scraper.should_exclude_dir('.git'))
self.assertTrue(scraper.should_exclude_dir('build'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_excluded_dirs_config.py:36*

### test_defaults_exclude_common_dirs

**Category**: method_call  
**Description**: Test that default exclusions work correctly.  
**Expected**: self.assertFalse(scraper.should_exclude_dir('src'))  
**Confidence**: 0.85  
**Tags**: unittest, mock  

```python
self.assertTrue(scraper.should_exclude_dir('build'))
self.assertFalse(scraper.should_exclude_dir('src'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_excluded_dirs_config.py:37*

### test_defaults_exclude_common_dirs

**Category**: method_call  
**Description**: Test that default exclusions work correctly.  
**Expected**: self.assertFalse(scraper.should_exclude_dir('tests'))  
**Confidence**: 0.85  
**Tags**: unittest, mock  

```python
self.assertFalse(scraper.should_exclude_dir('src'))
self.assertFalse(scraper.should_exclude_dir('tests'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_excluded_dirs_config.py:40*

### test_defaults_exclude_common_dirs

**Category**: method_call  
**Description**: Test that default exclusions work correctly.  
**Expected**: self.assertFalse(scraper.should_exclude_dir('docs'))  
**Confidence**: 0.85  
**Tags**: unittest, mock  

```python
self.assertFalse(scraper.should_exclude_dir('tests'))
self.assertFalse(scraper.should_exclude_dir('docs'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_excluded_dirs_config.py:41*

### test_dot_directories_always_excluded

**Category**: method_call  
**Description**: Test that directories starting with '.' are always excluded.  
**Expected**: self.assertTrue(scraper.should_exclude_dir('.cache'))  
**Confidence**: 0.85  
**Tags**: unittest, mock  

```python
self.assertTrue(scraper.should_exclude_dir('.hidden'))
self.assertTrue(scraper.should_exclude_dir('.cache'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_excluded_dirs_config.py:52*

### test_dot_directories_always_excluded

**Category**: method_call  
**Description**: Test that directories starting with '.' are always excluded.  
**Expected**: self.assertTrue(scraper.should_exclude_dir('.vscode'))  
**Confidence**: 0.85  
**Tags**: unittest, mock  

```python
self.assertTrue(scraper.should_exclude_dir('.cache'))
self.assertTrue(scraper.should_exclude_dir('.vscode'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_excluded_dirs_config.py:53*

### test_extend_with_additional_dirs

**Category**: method_call  
**Description**: Test adding custom exclusions to defaults.  
**Expected**: self.assertIn('node_modules', scraper.excluded_dirs)  
**Confidence**: 0.85  
**Tags**: unittest, mock  

```python
self.assertIn('venv', scraper.excluded_dirs)
self.assertIn('node_modules', scraper.excluded_dirs)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_excluded_dirs_config.py:71*

### test_telegram_bots_config_pattern

**Category**: method_call  
**Description**: Test the telegram-bots config pattern which uses skip_llms_txt.  
**Expected**: self.assertEqual(converter.name, 'telegram-bots')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertTrue(converter.skip_llms_txt)
self.assertEqual(converter.name, 'telegram-bots')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_skip_llms_txt.py:213*

### test_skip_llms_txt_with_multiple_start_urls

**Category**: method_call  
**Description**: Test skip_llms_txt works correctly with multiple start URLs.  
**Expected**: self.assertEqual(len(converter.pending_urls), 3)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertTrue(converter.skip_llms_txt)
self.assertEqual(len(converter.pending_urls), 3)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_skip_llms_txt.py:231*

### test_telegram_bots_config_pattern

**Category**: method_call  
**Description**: Test the telegram-bots config pattern which uses skip_llms_txt.  
**Expected**: self.assertEqual(converter.name, 'telegram-bots')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertTrue(converter.skip_llms_txt)
self.assertEqual(converter.name, 'telegram-bots')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_skip_llms_txt.py:213*

### test_skip_llms_txt_with_multiple_start_urls

**Category**: method_call  
**Description**: Test skip_llms_txt works correctly with multiple start URLs.  
**Expected**: self.assertEqual(len(converter.pending_urls), 3)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertTrue(converter.skip_llms_txt)
self.assertEqual(len(converter.pending_urls), 3)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_skip_llms_txt.py:231*

### test_force_refresh_deletes_cache

**Category**: method_call  
**Description**: Test force refresh deletes existing cache.  
**Expected**: mock_clone.assert_called_once()  
**Confidence**: 0.85  
**Tags**: mock  

```python
# Setup
# Fixtures: mock_clone, git_repo, temp_cache_dir

git_repo.clone_or_pull(source_name='test-source', git_url='https://github.com/org/repo.git', force_refresh=True)
mock_clone.assert_called_once()
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_git_repo.py:207*

### test_missing_recommended_selectors

**Category**: method_call  
**Description**: Test warning for missing recommended selectors  
**Expected**: self.assertTrue(any(('code_blocks' in warning.lower() for warning in warnings)))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertTrue(any(('title' in warning.lower() for warning in warnings)))
self.assertTrue(any(('code_blocks' in warning.lower() for warning in warnings)))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_config_validation.py:106*

### test_config_with_skip_llms_txt

**Category**: method_call  
**Description**: Test config validation accepts skip_llms_txt  
**Expected**: self.assertTrue(config.get('skip_llms_txt'))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(errors, [])
self.assertTrue(config.get('skip_llms_txt'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_config_validation.py:257*

### test_config_with_skip_llms_txt_false

**Category**: method_call  
**Description**: Test config validation accepts skip_llms_txt as False  
**Expected**: self.assertFalse(config.get('skip_llms_txt'))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(errors, [])
self.assertFalse(config.get('skip_llms_txt'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_config_validation.py:265*

### test_missing_recommended_selectors

**Category**: method_call  
**Description**: Test warning for missing recommended selectors  
**Expected**: self.assertTrue(any(('code_blocks' in warning.lower() for warning in warnings)))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertTrue(any(('title' in warning.lower() for warning in warnings)))
self.assertTrue(any(('code_blocks' in warning.lower() for warning in warnings)))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_config_validation.py:106*

### test_config_with_skip_llms_txt

**Category**: method_call  
**Description**: Test config validation accepts skip_llms_txt  
**Expected**: self.assertTrue(config.get('skip_llms_txt'))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(errors, [])
self.assertTrue(config.get('skip_llms_txt'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_config_validation.py:257*

### test_config_with_skip_llms_txt_false

**Category**: method_call  
**Description**: Test config validation accepts skip_llms_txt as False  
**Expected**: self.assertFalse(config.get('skip_llms_txt'))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(errors, [])
self.assertFalse(config.get('skip_llms_txt'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_config_validation.py:265*

### test_creates_subdirectory_per_source

**Category**: method_call  
**Description**: Test that each doc source gets its own subdirectory.  
**Expected**: self.assertTrue(os.path.exists(os.path.join(docs_dir, 'source_b')))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test fixtures.'
self.temp_dir = tempfile.mkdtemp()
self.original_dir = os.getcwd()
os.chdir(self.temp_dir)

self.assertTrue(os.path.exists(os.path.join(docs_dir, 'source_a')))
self.assertTrue(os.path.exists(os.path.join(docs_dir, 'source_b')))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_multi_source.py:138*

### test_copies_reference_files_to_source_dir

**Category**: method_call  
**Description**: Test that reference files are copied to source subdirectory.  
**Expected**: self.assertTrue(os.path.exists(os.path.join(source_dir, 'guide.md')))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test fixtures.'
self.temp_dir = tempfile.mkdtemp()
self.original_dir = os.getcwd()
os.chdir(self.temp_dir)

self.assertTrue(os.path.exists(os.path.join(source_dir, 'api.md')))
self.assertTrue(os.path.exists(os.path.join(source_dir, 'guide.md')))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_multi_source.py:250*

### test_creates_subdirectory_per_repo

**Category**: method_call  
**Description**: Test that each GitHub repo gets its own subdirectory.  
**Expected**: self.assertTrue(os.path.exists(os.path.join(github_dir, 'org_repo2')))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test fixtures.'
self.temp_dir = tempfile.mkdtemp()
self.original_dir = os.getcwd()
os.chdir(self.temp_dir)

self.assertTrue(os.path.exists(os.path.join(github_dir, 'org_repo1')))
self.assertTrue(os.path.exists(os.path.join(github_dir, 'org_repo2')))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_multi_source.py:296*

### test_creates_subdirectory_per_source

**Category**: method_call  
**Description**: Test that each doc source gets its own subdirectory.  
**Expected**: self.assertTrue(os.path.exists(os.path.join(docs_dir, 'source_b')))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertTrue(os.path.exists(os.path.join(docs_dir, 'source_a')))
self.assertTrue(os.path.exists(os.path.join(docs_dir, 'source_b')))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_multi_source.py:138*

### test_copies_reference_files_to_source_dir

**Category**: method_call  
**Description**: Test that reference files are copied to source subdirectory.  
**Expected**: self.assertTrue(os.path.exists(os.path.join(source_dir, 'guide.md')))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertTrue(os.path.exists(os.path.join(source_dir, 'api.md')))
self.assertTrue(os.path.exists(os.path.join(source_dir, 'guide.md')))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_multi_source.py:250*

### test_creates_subdirectory_per_repo

**Category**: method_call  
**Description**: Test that each GitHub repo gets its own subdirectory.  
**Expected**: self.assertTrue(os.path.exists(os.path.join(github_dir, 'org_repo2')))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertTrue(os.path.exists(os.path.join(github_dir, 'org_repo1')))
self.assertTrue(os.path.exists(os.path.join(github_dir, 'org_repo2')))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_multi_source.py:296*

### test_platform_info

**Category**: method_call  
**Description**: Test platform identifiers  
**Expected**: self.assertEqual(self.adaptor.PLATFORM_NAME, 'Generic Markdown (Universal)')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('markdown')

self.assertEqual(self.adaptor.PLATFORM, 'markdown')
self.assertEqual(self.adaptor.PLATFORM_NAME, 'Generic Markdown (Universal)')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_markdown_adaptor.py:24*

### test_platform_info

**Category**: method_call  
**Description**: Test platform identifiers  
**Expected**: self.assertIsNone(self.adaptor.DEFAULT_API_ENDPOINT)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('markdown')

self.assertEqual(self.adaptor.PLATFORM_NAME, 'Generic Markdown (Universal)')
self.assertIsNone(self.adaptor.DEFAULT_API_ENDPOINT)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_markdown_adaptor.py:25*

### test_validate_api_key

**Category**: method_call  
**Description**: Test that markdown export doesn't use API keys  
**Expected**: self.assertFalse(self.adaptor.validate_api_key('AIzaSyABC123'))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('markdown')

self.assertFalse(self.adaptor.validate_api_key('sk-ant-123'))
self.assertFalse(self.adaptor.validate_api_key('AIzaSyABC123'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_markdown_adaptor.py:31*

### test_validate_api_key

**Category**: method_call  
**Description**: Test that markdown export doesn't use API keys  
**Expected**: self.assertFalse(self.adaptor.validate_api_key('any-key'))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('markdown')

self.assertFalse(self.adaptor.validate_api_key('AIzaSyABC123'))
self.assertFalse(self.adaptor.validate_api_key('any-key'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_markdown_adaptor.py:32*

### test_validate_api_key

**Category**: method_call  
**Description**: Test that markdown export doesn't use API keys  
**Expected**: self.assertFalse(self.adaptor.validate_api_key(''))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('markdown')

self.assertFalse(self.adaptor.validate_api_key('any-key'))
self.assertFalse(self.adaptor.validate_api_key(''))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_markdown_adaptor.py:33*

### test_platform_info

**Category**: method_call  
**Description**: Test platform identifiers  
**Expected**: self.assertEqual(self.adaptor.PLATFORM_NAME, 'Generic Markdown (Universal)')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(self.adaptor.PLATFORM, 'markdown')
self.assertEqual(self.adaptor.PLATFORM_NAME, 'Generic Markdown (Universal)')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_markdown_adaptor.py:24*

### test_platform_info

**Category**: method_call  
**Description**: Test platform identifiers  
**Expected**: self.assertIsNone(self.adaptor.DEFAULT_API_ENDPOINT)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(self.adaptor.PLATFORM_NAME, 'Generic Markdown (Universal)')
self.assertIsNone(self.adaptor.DEFAULT_API_ENDPOINT)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_markdown_adaptor.py:25*

### test_validate_api_key

**Category**: method_call  
**Description**: Test that markdown export doesn't use API keys  
**Expected**: self.assertFalse(self.adaptor.validate_api_key('AIzaSyABC123'))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertFalse(self.adaptor.validate_api_key('sk-ant-123'))
self.assertFalse(self.adaptor.validate_api_key('AIzaSyABC123'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_markdown_adaptor.py:31*

### test_validate_api_key

**Category**: method_call  
**Description**: Test that markdown export doesn't use API keys  
**Expected**: self.assertFalse(self.adaptor.validate_api_key('any-key'))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertFalse(self.adaptor.validate_api_key('AIzaSyABC123'))
self.assertFalse(self.adaptor.validate_api_key('any-key'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_markdown_adaptor.py:32*

### test_validate_api_key

**Category**: method_call  
**Description**: Test that markdown export doesn't use API keys  
**Expected**: self.assertFalse(self.adaptor.validate_api_key(''))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertFalse(self.adaptor.validate_api_key('any-key'))
self.assertFalse(self.adaptor.validate_api_key(''))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_markdown_adaptor.py:33*

### test_python_function_signature_basic

**Category**: method_call  
**Description**: Test basic Python function signature extraction.  
**Expected**: self.assertEqual(len(result['functions']), 1)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test analyzer with deep analysis'
self.analyzer = CodeAnalyzer(depth='deep')

self.assertIn('functions', result)
self.assertEqual(len(result['functions']), 1)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_code_analyzer.py:39*

### test_python_function_signature_basic

**Category**: method_call  
**Description**: Test basic Python function signature extraction.  
**Expected**: self.assertEqual(len(func['parameters']), 2)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test analyzer with deep analysis'
self.analyzer = CodeAnalyzer(depth='deep')

self.assertEqual(func['name'], 'greet')
self.assertEqual(len(func['parameters']), 2)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_code_analyzer.py:43*

### test_python_function_signature_basic

**Category**: method_call  
**Description**: Test basic Python function signature extraction.  
**Expected**: self.assertEqual(func['parameters'][0]['name'], 'name')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test analyzer with deep analysis'
self.analyzer = CodeAnalyzer(depth='deep')

self.assertEqual(len(func['parameters']), 2)
self.assertEqual(func['parameters'][0]['name'], 'name')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_code_analyzer.py:44*

### test_python_function_signature_basic

**Category**: method_call  
**Description**: Test basic Python function signature extraction.  
**Expected**: self.assertEqual(func['parameters'][1]['name'], 'age')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test analyzer with deep analysis'
self.analyzer = CodeAnalyzer(depth='deep')

self.assertEqual(func['parameters'][0]['name'], 'name')
self.assertEqual(func['parameters'][1]['name'], 'age')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_code_analyzer.py:45*

### test_python_function_signature_basic

**Category**: method_call  
**Description**: Test basic Python function signature extraction.  
**Expected**: self.assertEqual(func['docstring'], 'Say hello.')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test analyzer with deep analysis'
self.analyzer = CodeAnalyzer(depth='deep')

self.assertEqual(func['parameters'][1]['name'], 'age')
self.assertEqual(func['docstring'], 'Say hello.')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_code_analyzer.py:46*

### test_python_function_with_type_hints

**Category**: method_call  
**Description**: Test Python function with type annotations.  
**Expected**: self.assertEqual(func['return_type'], 'int')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test analyzer with deep analysis'
self.analyzer = CodeAnalyzer(depth='deep')

self.assertEqual(func['name'], 'add_numbers')
self.assertEqual(func['return_type'], 'int')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_code_analyzer.py:61*

### test_python_function_with_type_hints

**Category**: method_call  
**Description**: Test Python function with type annotations.  
**Expected**: self.assertEqual(func['parameters'][0]['type_hint'], 'int')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test analyzer with deep analysis'
self.analyzer = CodeAnalyzer(depth='deep')

self.assertEqual(func['return_type'], 'int')
self.assertEqual(func['parameters'][0]['type_hint'], 'int')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_code_analyzer.py:62*

### test_python_function_with_type_hints

**Category**: method_call  
**Description**: Test Python function with type annotations.  
**Expected**: self.assertEqual(func['parameters'][1]['type_hint'], 'int')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test analyzer with deep analysis'
self.analyzer = CodeAnalyzer(depth='deep')

self.assertEqual(func['parameters'][0]['type_hint'], 'int')
self.assertEqual(func['parameters'][1]['type_hint'], 'int')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_code_analyzer.py:63*

### test_python_function_with_type_hints

**Category**: method_call  
**Description**: Test Python function with type annotations.  
**Expected**: self.assertEqual(func['docstring'], 'Add two integers.')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test analyzer with deep analysis'
self.analyzer = CodeAnalyzer(depth='deep')

self.assertEqual(func['parameters'][1]['type_hint'], 'int')
self.assertEqual(func['docstring'], 'Add two integers.')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_code_analyzer.py:64*

### test_python_function_with_defaults

**Category**: method_call  
**Description**: Test Python function with default parameter values.  
**Expected**: self.assertIsNone(func['parameters'][0]['default'])  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test analyzer with deep analysis'
self.analyzer = CodeAnalyzer(depth='deep')

self.assertEqual(func['name'], 'create_user')
self.assertIsNone(func['parameters'][0]['default'])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_code_analyzer.py:77*

### test_extract_text_with_ocr_disabled

**Category**: method_call  
**Description**: Test that OCR can be disabled  
**Expected**: mock_page.get_text.assert_called_once_with('text')  
**Confidence**: 0.85  
**Tags**: unittest, mock  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from pdf_extractor_poc import PDFExtractor
self.PDFExtractor = PDFExtractor
self.temp_dir = tempfile.mkdtemp()

self.assertEqual(text, 'This is regular text')
mock_page.get_text.assert_called_once_with('text')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_advanced_features.py:73*

### test_extract_text_with_ocr_sufficient_text

**Category**: method_call  
**Description**: Test OCR not triggered when sufficient text exists  
**Expected**: mock_page.get_pixmap.assert_not_called()  
**Confidence**: 0.85  
**Tags**: unittest, mock  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from pdf_extractor_poc import PDFExtractor
self.PDFExtractor = PDFExtractor
self.temp_dir = tempfile.mkdtemp()

self.assertEqual(len(text), 53)
mock_page.get_pixmap.assert_not_called()
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_advanced_features.py:88*

### test_ocr_unavailable_warning

**Category**: method_call  
**Description**: Test warning when OCR requested but pytesseract not available  
**Expected**: self.assertEqual(text, 'Short')  
**Confidence**: 0.85  
**Tags**: unittest, mock  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from pdf_extractor_poc import PDFExtractor
self.PDFExtractor = PDFExtractor
self.temp_dir = tempfile.mkdtemp()

self.assertIn('OCR requested but pytesseract not installed', output)
self.assertEqual(text, 'Short')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_advanced_features.py:107*

### test_ocr_extraction_triggered

**Category**: method_call  
**Description**: Test OCR extraction when text is minimal  
**Expected**: mock_page.get_pixmap.assert_called_once()  
**Confidence**: 0.85  
**Tags**: unittest, mock  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from pdf_extractor_poc import PDFExtractor
self.PDFExtractor = PDFExtractor
self.temp_dir = tempfile.mkdtemp()

self.assertEqual(text, 'OCR extracted text here')
mock_page.get_pixmap.assert_called_once()
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_advanced_features.py:132*

### test_table_extraction_disabled

**Category**: method_call  
**Description**: Test no tables extracted when disabled  
**Expected**: mock_page.find_tables.assert_not_called()  
**Confidence**: 0.85  
**Tags**: unittest, mock  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from pdf_extractor_poc import PDFExtractor
self.PDFExtractor = PDFExtractor
self.temp_dir = tempfile.mkdtemp()

self.assertEqual(tables, [])
mock_page.find_tables.assert_not_called()
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_advanced_features.py:241*

### test_table_extraction_basic

**Category**: method_call  
**Description**: Test basic table extraction  
**Expected**: self.assertEqual(tables[0]['row_count'], 2)  
**Confidence**: 0.85  
**Tags**: unittest, mock  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from pdf_extractor_poc import PDFExtractor
self.PDFExtractor = PDFExtractor
self.temp_dir = tempfile.mkdtemp()

self.assertEqual(len(tables), 1)
self.assertEqual(tables[0]['row_count'], 2)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_advanced_features.py:268*

### test_table_extraction_basic

**Category**: method_call  
**Description**: Test basic table extraction  
**Expected**: self.assertEqual(tables[0]['col_count'], 3)  
**Confidence**: 0.85  
**Tags**: unittest, mock  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from pdf_extractor_poc import PDFExtractor
self.PDFExtractor = PDFExtractor
self.temp_dir = tempfile.mkdtemp()

self.assertEqual(tables[0]['row_count'], 2)
self.assertEqual(tables[0]['col_count'], 3)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_advanced_features.py:269*

### test_table_extraction_basic

**Category**: method_call  
**Description**: Test basic table extraction  
**Expected**: self.assertEqual(tables[0]['table_index'], 0)  
**Confidence**: 0.85  
**Tags**: unittest, mock  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from pdf_extractor_poc import PDFExtractor
self.PDFExtractor = PDFExtractor
self.temp_dir = tempfile.mkdtemp()

self.assertEqual(tables[0]['col_count'], 3)
self.assertEqual(tables[0]['table_index'], 0)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_advanced_features.py:270*

### test_multiple_tables_extraction

**Category**: method_call  
**Description**: Test extraction of multiple tables from one page  
**Expected**: self.assertEqual(tables[0]['table_index'], 0)  
**Confidence**: 0.85  
**Tags**: unittest, mock  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from pdf_extractor_poc import PDFExtractor
self.PDFExtractor = PDFExtractor
self.temp_dir = tempfile.mkdtemp()

self.assertEqual(len(tables), 2)
self.assertEqual(tables[0]['table_index'], 0)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_advanced_features.py:296*

### test_multiple_tables_extraction

**Category**: method_call  
**Description**: Test extraction of multiple tables from one page  
**Expected**: self.assertEqual(tables[1]['table_index'], 1)  
**Confidence**: 0.85  
**Tags**: unittest, mock  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from pdf_extractor_poc import PDFExtractor
self.PDFExtractor = PDFExtractor
self.temp_dir = tempfile.mkdtemp()

self.assertEqual(tables[0]['table_index'], 0)
self.assertEqual(tables[1]['table_index'], 1)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_advanced_features.py:297*

### test_platform_info

**Category**: method_call  
**Description**: Test platform identifiers  
**Expected**: self.assertEqual(self.adaptor.PLATFORM_NAME, 'Google Gemini')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('gemini')

self.assertEqual(self.adaptor.PLATFORM, 'gemini')
self.assertEqual(self.adaptor.PLATFORM_NAME, 'Google Gemini')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_gemini_adaptor.py:24*

### test_platform_info

**Category**: method_call  
**Description**: Test platform identifiers  
**Expected**: self.assertIsNotNone(self.adaptor.DEFAULT_API_ENDPOINT)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('gemini')

self.assertEqual(self.adaptor.PLATFORM_NAME, 'Google Gemini')
self.assertIsNotNone(self.adaptor.DEFAULT_API_ENDPOINT)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_gemini_adaptor.py:25*

### test_validate_api_key_valid

**Category**: method_call  
**Description**: Test valid Google API key  
**Expected**: self.assertTrue(self.adaptor.validate_api_key('  AIzaSyTest  '))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('gemini')

self.assertTrue(self.adaptor.validate_api_key('AIzaSyABC123'))
self.assertTrue(self.adaptor.validate_api_key('  AIzaSyTest  '))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_gemini_adaptor.py:30*

### test_validate_api_key_invalid

**Category**: method_call  
**Description**: Test invalid API keys  
**Expected**: self.assertFalse(self.adaptor.validate_api_key('invalid'))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('gemini')

self.assertFalse(self.adaptor.validate_api_key('sk-ant-123'))
self.assertFalse(self.adaptor.validate_api_key('invalid'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_gemini_adaptor.py:35*

### test_validate_api_key_invalid

**Category**: method_call  
**Description**: Test invalid API keys  
**Expected**: self.assertFalse(self.adaptor.validate_api_key(''))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('gemini')

self.assertFalse(self.adaptor.validate_api_key('invalid'))
self.assertFalse(self.adaptor.validate_api_key(''))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_gemini_adaptor.py:36*

### test_upload_invalid_file

**Category**: method_call  
**Description**: Test upload with invalid file  
**Expected**: self.assertIn('not found', result['message'].lower())  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test adaptor'
self.adaptor = get_adaptor('gemini')

self.assertFalse(result['success'])
self.assertIn('not found', result['message'].lower())
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_gemini_adaptor.py:115*

### test_platform_info

**Category**: method_call  
**Description**: Test platform identifiers  
**Expected**: self.assertEqual(self.adaptor.PLATFORM_NAME, 'Google Gemini')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(self.adaptor.PLATFORM, 'gemini')
self.assertEqual(self.adaptor.PLATFORM_NAME, 'Google Gemini')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_gemini_adaptor.py:24*

### test_platform_info

**Category**: method_call  
**Description**: Test platform identifiers  
**Expected**: self.assertIsNotNone(self.adaptor.DEFAULT_API_ENDPOINT)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(self.adaptor.PLATFORM_NAME, 'Google Gemini')
self.assertIsNotNone(self.adaptor.DEFAULT_API_ENDPOINT)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_gemini_adaptor.py:25*

### test_validate_api_key_valid

**Category**: method_call  
**Description**: Test valid Google API key  
**Expected**: self.assertTrue(self.adaptor.validate_api_key('  AIzaSyTest  '))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertTrue(self.adaptor.validate_api_key('AIzaSyABC123'))
self.assertTrue(self.adaptor.validate_api_key('  AIzaSyTest  '))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_gemini_adaptor.py:30*

### test_validate_api_key_invalid

**Category**: method_call  
**Description**: Test invalid API keys  
**Expected**: self.assertFalse(self.adaptor.validate_api_key('invalid'))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertFalse(self.adaptor.validate_api_key('sk-ant-123'))
self.assertFalse(self.adaptor.validate_api_key('invalid'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_gemini_adaptor.py:35*

### test_init_with_name_and_pdf_path

**Category**: method_call  
**Description**: Test initialization with name and PDF path  
**Expected**: self.assertEqual(converter.pdf_path, 'test.pdf')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from skill_seekers.cli.pdf_scraper import PDFToSkillConverter
self.PDFToSkillConverter = PDFToSkillConverter
self.temp_dir = tempfile.mkdtemp()
self.output_dir = Path(self.temp_dir)

self.assertEqual(converter.name, 'test_skill')
self.assertEqual(converter.pdf_path, 'test.pdf')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_scraper.py:52*

### test_init_with_config

**Category**: method_call  
**Description**: Test initialization with config file  
**Expected**: self.assertEqual(converter.config.get('description'), 'Test skill')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from skill_seekers.cli.pdf_scraper import PDFToSkillConverter
self.PDFToSkillConverter = PDFToSkillConverter
self.temp_dir = tempfile.mkdtemp()
self.output_dir = Path(self.temp_dir)

self.assertEqual(converter.name, 'config_skill')
self.assertEqual(converter.config.get('description'), 'Test skill')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_scraper.py:67*

### test_categorize_by_keywords

**Category**: method_call  
**Description**: Test categorization using keyword matching  
**Expected**: self.assertIn('api', categories)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from skill_seekers.cli.pdf_scraper import PDFToSkillConverter
self.PDFToSkillConverter = PDFToSkillConverter
self.temp_dir = tempfile.mkdtemp()

self.assertIn('getting_started', categories)
self.assertIn('api', categories)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_scraper.py:118*

### test_categorize_by_chapters

**Category**: method_call  
**Description**: Test categorization using chapter information  
**Expected**: self.assertGreater(len(categories), 0)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from skill_seekers.cli.pdf_scraper import PDFToSkillConverter
self.PDFToSkillConverter = PDFToSkillConverter
self.temp_dir = tempfile.mkdtemp()

self.assertIsInstance(categories, dict)
self.assertGreater(len(categories), 0)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_scraper.py:138*

### test_build_skill_creates_structure

**Category**: method_call  
**Description**: Test that build_skill creates required directory structure  
**Expected**: self.assertTrue((skill_dir / 'references').exists())  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from skill_seekers.cli.pdf_scraper import PDFToSkillConverter
self.PDFToSkillConverter = PDFToSkillConverter
self.temp_dir = tempfile.mkdtemp()

self.assertTrue(skill_dir.exists())
self.assertTrue((skill_dir / 'references').exists())
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_scraper.py:192*

### test_build_skill_creates_structure

**Category**: method_call  
**Description**: Test that build_skill creates required directory structure  
**Expected**: self.assertTrue((skill_dir / 'scripts').exists())  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from skill_seekers.cli.pdf_scraper import PDFToSkillConverter
self.PDFToSkillConverter = PDFToSkillConverter
self.temp_dir = tempfile.mkdtemp()

self.assertTrue((skill_dir / 'references').exists())
self.assertTrue((skill_dir / 'scripts').exists())
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_scraper.py:193*

### test_build_skill_creates_structure

**Category**: method_call  
**Description**: Test that build_skill creates required directory structure  
**Expected**: self.assertTrue((skill_dir / 'assets').exists())  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from skill_seekers.cli.pdf_scraper import PDFToSkillConverter
self.PDFToSkillConverter = PDFToSkillConverter
self.temp_dir = tempfile.mkdtemp()

self.assertTrue((skill_dir / 'scripts').exists())
self.assertTrue((skill_dir / 'assets').exists())
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_scraper.py:194*

### test_build_skill_creates_skill_md

**Category**: method_call  
**Description**: Test that SKILL.md is created  
**Expected**: self.assertIn('Test description', content)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from skill_seekers.cli.pdf_scraper import PDFToSkillConverter
self.PDFToSkillConverter = PDFToSkillConverter
self.temp_dir = tempfile.mkdtemp()

self.assertIn('test_skill', content)
self.assertIn('Test description', content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_scraper.py:218*

### test_build_skill_creates_reference_files

**Category**: method_call  
**Description**: Test that reference files are created for categories  
**Expected**: self.assertTrue((refs_dir / 'api.md').exists())  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from skill_seekers.cli.pdf_scraper import PDFToSkillConverter
self.PDFToSkillConverter = PDFToSkillConverter
self.temp_dir = tempfile.mkdtemp()

self.assertTrue((refs_dir / 'getting_started.md').exists())
self.assertTrue((refs_dir / 'api.md').exists())
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_scraper.py:246*

### test_build_skill_creates_reference_files

**Category**: method_call  
**Description**: Test that reference files are created for categories  
**Expected**: self.assertTrue((refs_dir / 'index.md').exists())  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not PYMUPDF_AVAILABLE:
    self.skipTest('PyMuPDF not installed')
from skill_seekers.cli.pdf_scraper import PDFToSkillConverter
self.PDFToSkillConverter = PDFToSkillConverter
self.temp_dir = tempfile.mkdtemp()

self.assertTrue((refs_dir / 'api.md').exists())
self.assertTrue((refs_dir / 'index.md').exists())
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_pdf_scraper.py:247*

### test_validate_unified_sources

**Category**: method_call  
**Description**: Test source type validation  
**Expected**: assert len(validator.config['sources']) == 3  
**Confidence**: 0.85  

```python
validator.validate()
assert len(validator.config['sources']) == 3
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_unified.py:78*

### test_full_workflow_unified_config

**Category**: method_call  
**Description**: Test complete workflow with unified config  
**Expected**: assert validator.is_unified  
**Confidence**: 0.85  

```python
validator.validate()
assert validator.is_unified
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_unified.py:547*

### test_01_three_streams_present

**Category**: method_call  
**Description**: Test that all 3 streams are present and populated.  
**Expected**: assert result.code_analysis is not None, 'Code analysis missing'  
**Confidence**: 0.85  

```python
# Setup
# Fixtures: fastmcp_analysis

print('\n📊 STREAM 1: Code Analysis')
assert result.code_analysis is not None, 'Code analysis missing'
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_real_world_fastmcp.py:126*

### test_01_three_streams_present

**Category**: method_call  
**Description**: Test that all 3 streams are present and populated.  
**Expected**: assert len(files) > 0, 'No files found in code analysis'  
**Confidence**: 0.85  

```python
# Setup
# Fixtures: fastmcp_analysis

print(f'   ✅ Files analyzed: {len(files)}')
assert len(files) > 0, 'No files found in code analysis'
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_real_world_fastmcp.py:130*

### test_01_three_streams_present

**Category**: method_call  
**Description**: Test that all 3 streams are present and populated.  
**Expected**: assert result.github_docs is not None, 'GitHub docs missing'  
**Confidence**: 0.85  

```python
# Setup
# Fixtures: fastmcp_analysis

print('\n📄 STREAM 2: GitHub Documentation')
assert result.github_docs is not None, 'GitHub docs missing'
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_real_world_fastmcp.py:134*

### test_01_three_streams_present

**Category**: method_call  
**Description**: Test that all 3 streams are present and populated.  
**Expected**: assert len(readme) > 100, 'README too short (< 100 chars)'  
**Confidence**: 0.85  

```python
# Setup
# Fixtures: fastmcp_analysis

print(f'   ✅ README length: {len(readme)} chars')
assert len(readme) > 100, 'README too short (< 100 chars)'
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_real_world_fastmcp.py:139*

### test_01_three_streams_present

**Category**: method_call  
**Description**: Test that all 3 streams are present and populated.  
**Expected**: assert result.github_insights is not None, 'GitHub insights missing'  
**Confidence**: 0.85  

```python
# Setup
# Fixtures: fastmcp_analysis

print('\n🐛 STREAM 3: GitHub Insights')
assert result.github_insights is not None, 'GitHub insights missing'
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_real_world_fastmcp.py:153*

### test_01_three_streams_present

**Category**: method_call  
**Description**: Test that all 3 streams are present and populated.  
**Expected**: assert stars >= 0, 'Stars count invalid'  
**Confidence**: 0.85  

```python
# Setup
# Fixtures: fastmcp_analysis

print(f'   ✅ Description: {description}')
assert stars >= 0, 'Stars count invalid'
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_real_world_fastmcp.py:165*

### test_02_c3x_components_populated

**Category**: method_call  
**Description**: Test that C3.x components have ACTUAL data (not placeholders).  
**Expected**: assert total_c3x_items > 0, '❌ CRITICAL: No C3.x data found! This suggests placeholders are being used instead of actual analysis.'  
**Confidence**: 0.85  

```python
# Setup
# Fixtures: fastmcp_analysis

print(f'\n📊 Total C3.x items: {total_c3x_items}')
assert total_c3x_items > 0, '❌ CRITICAL: No C3.x data found! This suggests placeholders are being used instead of actual analysis.'
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_real_world_fastmcp.py:253*

### test_03_router_generation

**Category**: method_call  
**Description**: Test router generation with GitHub integration.  
**Expected**: assert 'fastmcp' in skill_md.lower(), "Router doesn't mention FastMCP"  
**Confidence**: 0.85  

```python
# Setup
# Fixtures: fastmcp_analysis, output_dir

print('\n📝 Router Content Analysis:')
assert 'fastmcp' in skill_md.lower(), "Router doesn't mention FastMCP"
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_real_world_fastmcp.py:332*

### test_04_quality_metrics

**Category**: method_call  
**Description**: Test that quality metrics meet architecture targets.  
**Expected**: assert code_files > 0, 'No code files found'  
**Confidence**: 0.85  

```python
# Setup
# Fixtures: fastmcp_analysis, output_dir

print(f'   Code files: {code_files}')
assert code_files > 0, 'No code files found'
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_real_world_fastmcp.py:406*

### test_04_quality_metrics

**Category**: method_call  
**Description**: Test that quality metrics meet architecture targets.  
**Expected**: assert readme_len > 100, 'README too short'  
**Confidence**: 0.85  

```python
# Setup
# Fixtures: fastmcp_analysis, output_dir

print(f'   README length: {readme_len} chars')
assert readme_len > 100, 'README too short'
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_real_world_fastmcp.py:411*

### test_estimate_pages_with_minimal_config

**Category**: method_call  
**Description**: Test estimation with minimal configuration  
**Expected**: self.assertIn('discovered', result)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIsInstance(result, dict)
self.assertIn('discovered', result)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_estimate_pages.py:25*

### test_estimate_pages_with_minimal_config

**Category**: method_call  
**Description**: Test estimation with minimal configuration  
**Expected**: self.assertIn('estimated_total', result)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIn('discovered', result)
self.assertIn('estimated_total', result)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_estimate_pages.py:26*

### test_estimate_pages_with_minimal_config

**Category**: method_call  
**Description**: Test estimation with minimal configuration  
**Expected**: self.assertIn('elapsed_seconds', result)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIn('estimated_total', result)
self.assertIn('elapsed_seconds', result)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_estimate_pages.py:27*

### test_estimate_pages_returns_discovered_count

**Category**: method_call  
**Description**: Test that result contains discovered page count  
**Expected**: self.assertIsInstance(result['discovered'], int)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertGreaterEqual(result['discovered'], 0)
self.assertIsInstance(result['discovered'], int)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_estimate_pages.py:37*

### test_estimate_pages_with_start_urls

**Category**: method_call  
**Description**: Test estimation with custom start_urls  
**Expected**: self.assertIn('discovered', result)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIsInstance(result, dict)
self.assertIn('discovered', result)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_estimate_pages.py:60*

### test_estimate_with_real_config_file

**Category**: method_call  
**Description**: Test estimation using a real config file (if exists)  
**Expected**: self.assertIn('discovered', result)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIsInstance(result, dict)
self.assertIn('discovered', result)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_estimate_pages.py:181*

### test_estimate_with_real_config_file

**Category**: method_call  
**Description**: Test estimation using a real config file (if exists)  
**Expected**: self.assertGreater(result['discovered'], 0)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIn('discovered', result)
self.assertGreater(result['discovered'], 0)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_estimate_pages.py:182*

### test_estimate_pages_with_minimal_config

**Category**: method_call  
**Description**: Test estimation with minimal configuration  
**Expected**: self.assertIn('discovered', result)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIsInstance(result, dict)
self.assertIn('discovered', result)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_estimate_pages.py:25*

### test_estimate_pages_with_minimal_config

**Category**: method_call  
**Description**: Test estimation with minimal configuration  
**Expected**: self.assertIn('estimated_total', result)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIn('discovered', result)
self.assertIn('estimated_total', result)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_estimate_pages.py:26*

### test_estimate_pages_with_minimal_config

**Category**: method_call  
**Description**: Test estimation with minimal configuration  
**Expected**: self.assertIn('elapsed_seconds', result)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIn('estimated_total', result)
self.assertIn('elapsed_seconds', result)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_estimate_pages.py:27*

### test_extract_instantiation

**Category**: method_call  
**Description**: Test extraction of object instantiation patterns  
**Expected**: self.assertIn('host', inst.code)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.analyzer = PythonTestAnalyzer()

self.assertIn('Database', inst.code)
self.assertIn('host', inst.code)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_test_example_extractor.py:57*

### test_extract_instantiation

**Category**: method_call  
**Description**: Test extraction of object instantiation patterns  
**Expected**: self.assertGreaterEqual(inst.confidence, 0.7)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.analyzer = PythonTestAnalyzer()

self.assertIn('host', inst.code)
self.assertGreaterEqual(inst.confidence, 0.7)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_test_example_extractor.py:58*

### test_extract_config_dict

**Category**: method_call  
**Description**: Test extraction of configuration dictionaries  
**Expected**: self.assertIn('database_url', config.code)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.analyzer = PythonTestAnalyzer()

self.assertIn('debug', config.code)
self.assertIn('database_url', config.code)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_test_example_extractor.py:105*

### test_extract_config_dict

**Category**: method_call  
**Description**: Test extraction of configuration dictionaries  
**Expected**: self.assertGreaterEqual(config.confidence, 0.7)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.analyzer = PythonTestAnalyzer()

self.assertIn('database_url', config.code)
self.assertGreaterEqual(config.confidence, 0.7)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_test_example_extractor.py:106*

### test_extract_setup_code

**Category**: method_call  
**Description**: Test extraction of setUp method context  
**Expected**: self.assertIn('APIClient', examples_with_setup[0].setup_code)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.analyzer = PythonTestAnalyzer()

self.assertGreater(len(examples_with_setup), 0)
self.assertIn('APIClient', examples_with_setup[0].setup_code)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_test_example_extractor.py:128*

### test_integration_workflow

**Category**: method_call  
**Description**: Test extraction of multi-step workflow tests  
**Expected**: self.assertIn('workflow', [tag.lower() for tag in workflow.tags])  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.analyzer = PythonTestAnalyzer()

self.assertGreaterEqual(workflow.confidence, 0.85)
self.assertIn('workflow', [tag.lower() for tag in workflow.tags])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_test_example_extractor.py:205*

### test_extract_javascript_instantiation

**Category**: method_call  
**Description**: Test JavaScript object instantiation extraction  
**Expected**: self.assertEqual(examples[0].language, 'JavaScript')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.analyzer = GenericTestAnalyzer()

self.assertGreater(len(examples), 0)
self.assertEqual(examples[0].language, 'JavaScript')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_test_example_extractor.py:261*

### test_extract_javascript_instantiation

**Category**: method_call  
**Description**: Test JavaScript object instantiation extraction  
**Expected**: self.assertIn('Database', examples[0].code)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
self.analyzer = GenericTestAnalyzer()

self.assertEqual(examples[0].language, 'JavaScript')
self.assertIn('Database', examples[0].code)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_test_example_extractor.py:262*

### test_scraping_constants_exist

**Category**: method_call  
**Description**: Test that scraping constants are defined.  
**Expected**: self.assertIsNotNone(DEFAULT_MAX_PAGES)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIsNotNone(DEFAULT_RATE_LIMIT)
self.assertIsNotNone(DEFAULT_MAX_PAGES)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_constants.py:37*

### test_scraping_constants_exist

**Category**: method_call  
**Description**: Test that scraping constants are defined.  
**Expected**: self.assertIsNotNone(DEFAULT_CHECKPOINT_INTERVAL)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIsNotNone(DEFAULT_MAX_PAGES)
self.assertIsNotNone(DEFAULT_CHECKPOINT_INTERVAL)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_constants.py:38*

### test_scraping_constants_types

**Category**: method_call  
**Description**: Test that scraping constants have correct types.  
**Expected**: self.assertIsInstance(DEFAULT_MAX_PAGES, int)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIsInstance(DEFAULT_RATE_LIMIT, (int, float))
self.assertIsInstance(DEFAULT_MAX_PAGES, int)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_constants.py:43*

### test_scraping_constants_types

**Category**: method_call  
**Description**: Test that scraping constants have correct types.  
**Expected**: self.assertIsInstance(DEFAULT_CHECKPOINT_INTERVAL, int)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIsInstance(DEFAULT_MAX_PAGES, int)
self.assertIsInstance(DEFAULT_CHECKPOINT_INTERVAL, int)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_constants.py:44*

### test_scraping_constants_ranges

**Category**: method_call  
**Description**: Test that scraping constants have sensible values.  
**Expected**: self.assertGreater(DEFAULT_MAX_PAGES, 0)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertGreater(DEFAULT_RATE_LIMIT, 0)
self.assertGreater(DEFAULT_MAX_PAGES, 0)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_constants.py:49*

### test_scraping_constants_ranges

**Category**: method_call  
**Description**: Test that scraping constants have sensible values.  
**Expected**: self.assertGreater(DEFAULT_CHECKPOINT_INTERVAL, 0)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertGreater(DEFAULT_MAX_PAGES, 0)
self.assertGreater(DEFAULT_CHECKPOINT_INTERVAL, 0)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_constants.py:50*

### test_scraping_constants_ranges

**Category**: method_call  
**Description**: Test that scraping constants have sensible values.  
**Expected**: self.assertEqual(DEFAULT_RATE_LIMIT, 0.5)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertGreater(DEFAULT_CHECKPOINT_INTERVAL, 0)
self.assertEqual(DEFAULT_RATE_LIMIT, 0.5)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_constants.py:51*

### test_scraping_constants_ranges

**Category**: method_call  
**Description**: Test that scraping constants have sensible values.  
**Expected**: self.assertEqual(DEFAULT_MAX_PAGES, 500)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(DEFAULT_RATE_LIMIT, 0.5)
self.assertEqual(DEFAULT_MAX_PAGES, 500)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_constants.py:52*

### test_scraping_constants_ranges

**Category**: method_call  
**Description**: Test that scraping constants have sensible values.  
**Expected**: self.assertEqual(DEFAULT_CHECKPOINT_INTERVAL, 1000)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(DEFAULT_MAX_PAGES, 500)
self.assertEqual(DEFAULT_CHECKPOINT_INTERVAL, 1000)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_constants.py:53*

### test_content_analysis_constants

**Category**: method_call  
**Description**: Test content analysis constants.  
**Expected**: self.assertEqual(MAX_PAGES_WARNING_THRESHOLD, 10000)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(CONTENT_PREVIEW_LENGTH, 500)
self.assertEqual(MAX_PAGES_WARNING_THRESHOLD, 10000)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_constants.py:58*

### test_github_command_has_enhancement_flags

**Category**: method_call  
**Description**: E2E: Verify --enhance-local flag exists in github command help  
**Expected**: self.assertIn('--enhance', result.stdout, 'Missing --enhance flag')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(result.returncode, 0, 'github --help should succeed')
self.assertIn('--enhance', result.stdout, 'Missing --enhance flag')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_issue_219_e2e.py:129*

### test_github_command_has_enhancement_flags

**Category**: method_call  
**Description**: E2E: Verify --enhance-local flag exists in github command help  
**Expected**: self.assertIn('--enhance-local', result.stdout, 'Missing --enhance-local flag')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIn('--enhance', result.stdout, 'Missing --enhance flag')
self.assertIn('--enhance-local', result.stdout, 'Missing --enhance-local flag')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_issue_219_e2e.py:132*

### test_github_command_has_enhancement_flags

**Category**: method_call  
**Description**: E2E: Verify --enhance-local flag exists in github command help  
**Expected**: self.assertIn('--api-key', result.stdout, 'Missing --api-key flag')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIn('--enhance-local', result.stdout, 'Missing --enhance-local flag')
self.assertIn('--api-key', result.stdout, 'Missing --api-key flag')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_issue_219_e2e.py:133*

### test_all_fixes_work_together

**Category**: method_call  
**Description**: E2E: Verify all 3 fixes work in combination  
**Expected**: self.assertIn('--enhance-local', result.stdout)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIn('--enhance', result.stdout)
self.assertIn('--enhance-local', result.stdout)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_issue_219_e2e.py:351*

### test_all_fixes_work_together

**Category**: method_call  
**Description**: E2E: Verify all 3 fixes work in combination  
**Expected**: self.assertIn('--api-key', result.stdout)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIn('--enhance-local', result.stdout)
self.assertIn('--api-key', result.stdout)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_issue_219_e2e.py:352*

### test_github_command_has_enhancement_flags

**Category**: method_call  
**Description**: E2E: Verify --enhance-local flag exists in github command help  
**Expected**: self.assertIn('--enhance', result.stdout, 'Missing --enhance flag')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(result.returncode, 0, 'github --help should succeed')
self.assertIn('--enhance', result.stdout, 'Missing --enhance flag')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_issue_219_e2e.py:129*

### test_github_command_has_enhancement_flags

**Category**: method_call  
**Description**: E2E: Verify --enhance-local flag exists in github command help  
**Expected**: self.assertIn('--enhance-local', result.stdout, 'Missing --enhance-local flag')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIn('--enhance', result.stdout, 'Missing --enhance flag')
self.assertIn('--enhance-local', result.stdout, 'Missing --enhance-local flag')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_issue_219_e2e.py:132*

### test_github_command_has_enhancement_flags

**Category**: method_call  
**Description**: E2E: Verify --enhance-local flag exists in github command help  
**Expected**: self.assertIn('--api-key', result.stdout, 'Missing --api-key flag')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIn('--enhance-local', result.stdout, 'Missing --enhance-local flag')
self.assertIn('--api-key', result.stdout, 'Missing --api-key flag')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_issue_219_e2e.py:133*

### test_all_fixes_work_together

**Category**: method_call  
**Description**: E2E: Verify all 3 fixes work in combination  
**Expected**: self.assertIn('--enhance-local', result.stdout)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIn('--enhance', result.stdout)
self.assertIn('--enhance-local', result.stdout)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_issue_219_e2e.py:351*

### test_all_fixes_work_together

**Category**: method_call  
**Description**: E2E: Verify all 3 fixes work in combination  
**Expected**: self.assertIn('--api-key', result.stdout)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIn('--enhance-local', result.stdout)
self.assertIn('--api-key', result.stdout)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_issue_219_e2e.py:352*

### test_upload_with_nonexistent_file

**Category**: method_call  
**Description**: Test upload with nonexistent file  
**Expected**: self.assertIn('not found', message.lower())  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Store original API key state'
self.original_api_key = os.environ.get('ANTHROPIC_API_KEY')

self.assertFalse(success)
self.assertIn('not found', message.lower())
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_upload_skill.py:60*

### test_upload_with_nonexistent_file

**Category**: method_call  
**Description**: Test upload with nonexistent file  
**Expected**: self.assertIn('not found', message.lower())  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertFalse(success)
self.assertIn('not found', message.lower())
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_upload_skill.py:60*

### test_format_bytes_below_1kb

**Category**: method_call  
**Description**: Test formatting bytes below 1 KB  
**Expected**: self.assertEqual(format_file_size(1023), '1023 bytes')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(format_file_size(500), '500 bytes')
self.assertEqual(format_file_size(1023), '1023 bytes')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_utilities.py:96*

### test_format_kilobytes

**Category**: method_call  
**Description**: Test formatting KB sizes  
**Expected**: self.assertEqual(format_file_size(1536), '1.5 KB')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(format_file_size(1024), '1.0 KB')
self.assertEqual(format_file_size(1536), '1.5 KB')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_utilities.py:101*

### test_format_kilobytes

**Category**: method_call  
**Description**: Test formatting KB sizes  
**Expected**: self.assertEqual(format_file_size(10240), '10.0 KB')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(format_file_size(1536), '1.5 KB')
self.assertEqual(format_file_size(10240), '10.0 KB')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_utilities.py:102*

### test_format_megabytes

**Category**: method_call  
**Description**: Test formatting MB sizes  
**Expected**: self.assertEqual(format_file_size(1572864), '1.5 MB')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(format_file_size(1048576), '1.0 MB')
self.assertEqual(format_file_size(1572864), '1.5 MB')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_utilities.py:107*

### test_format_megabytes

**Category**: method_call  
**Description**: Test formatting MB sizes  
**Expected**: self.assertEqual(format_file_size(10485760), '10.0 MB')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(format_file_size(1572864), '1.5 MB')
self.assertEqual(format_file_size(10485760), '10.0 MB')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_utilities.py:108*

### test_format_large_files

**Category**: method_call  
**Description**: Test formatting large file sizes  
**Expected**: self.assertEqual(format_file_size(1073741824), '1024.0 MB')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(format_file_size(104857600), '100.0 MB')
self.assertEqual(format_file_size(1073741824), '1024.0 MB')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_utilities.py:118*

### test_nonexistent_directory

**Category**: method_call  
**Description**: Test validation of nonexistent directory  
**Expected**: self.assertIn('not found', error.lower())  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertFalse(is_valid)
self.assertIn('not found', error.lower())
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_utilities.py:140*

### test_nonexistent_file

**Category**: method_call  
**Description**: Test validation of nonexistent file  
**Expected**: self.assertIn('not found', error.lower())  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertFalse(is_valid)
self.assertIn('not found', error.lower())
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_utilities.py:177*

### test_successful_operation_first_try

**Category**: method_call  
**Description**: Test operation that succeeds on first try  
**Expected**: self.assertEqual(call_count, 1)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(result, 'success')
self.assertEqual(call_count, 1)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_utilities.py:235*

### test_successful_operation_after_retry

**Category**: method_call  
**Description**: Test operation that fails once then succeeds  
**Expected**: self.assertEqual(call_count, 2)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(result, 'success')
self.assertEqual(call_count, 2)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_utilities.py:250*

### test_basic_metadata

**Category**: method_call  
**Description**: Test basic metadata creation  
**Expected**: self.assertEqual(metadata.description, 'Test skill description')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(metadata.name, 'test-skill')
self.assertEqual(metadata.description, 'Test skill description')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_base.py:24*

### test_basic_metadata

**Category**: method_call  
**Description**: Test basic metadata creation  
**Expected**: self.assertEqual(metadata.version, '1.0.0')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(metadata.description, 'Test skill description')
self.assertEqual(metadata.version, '1.0.0')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_base.py:25*

### test_basic_metadata

**Category**: method_call  
**Description**: Test basic metadata creation  
**Expected**: self.assertIsNone(metadata.author)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(metadata.version, '1.0.0')
self.assertIsNone(metadata.author)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_base.py:26*

### test_basic_metadata

**Category**: method_call  
**Description**: Test basic metadata creation  
**Expected**: self.assertEqual(metadata.tags, [])  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertIsNone(metadata.author)
self.assertEqual(metadata.tags, [])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_base.py:27*

### test_full_metadata

**Category**: method_call  
**Description**: Test metadata with all fields  
**Expected**: self.assertEqual(metadata.description, 'React documentation')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(metadata.name, 'react')
self.assertEqual(metadata.description, 'React documentation')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_base.py:40*

### test_full_metadata

**Category**: method_call  
**Description**: Test metadata with all fields  
**Expected**: self.assertEqual(metadata.version, '2.5.0')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(metadata.description, 'React documentation')
self.assertEqual(metadata.version, '2.5.0')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_base.py:41*

### test_full_metadata

**Category**: method_call  
**Description**: Test metadata with all fields  
**Expected**: self.assertEqual(metadata.author, 'Test Author')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(metadata.version, '2.5.0')
self.assertEqual(metadata.author, 'Test Author')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_base.py:42*

### test_full_metadata

**Category**: method_call  
**Description**: Test metadata with all fields  
**Expected**: self.assertEqual(metadata.tags, ['react', 'javascript', 'web'])  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(metadata.author, 'Test Author')
self.assertEqual(metadata.tags, ['react', 'javascript', 'web'])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_adaptors\test_base.py:43*

### test_classify_files

**Category**: method_call  
**Description**: Test classify_files separates code and docs correctly.  
**Expected**: (tmp_path / 'node_modules' / 'lib.js').write_text('// should be excluded')  
**Confidence**: 0.85  

```python
# Setup
# Fixtures: tmp_path

(tmp_path / 'node_modules').mkdir()
(tmp_path / 'node_modules' / 'lib.js').write_text('// should be excluded')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_github_fetcher.py:117*

### test_dry_run_no_directories_created

**Category**: method_call  
**Description**: Test that dry-run mode doesn't create directories  
**Expected**: self.assertFalse(skill_dir.exists(), 'Dry-run should not create skill directory')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test configuration'
self.config = {'name': 'test-dry-run', 'base_url': 'https://example.com/', 'selectors': {'main_content': 'article', 'title': 'h1', 'code_blocks': 'pre code'}, 'url_patterns': {'include': [], 'exclude': []}, 'rate_limit': 0.1, 'max_pages': 10}

self.assertFalse(data_dir.exists(), 'Dry-run should not create data directory')
self.assertFalse(skill_dir.exists(), 'Dry-run should not create skill directory')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_integration.py:43*

### test_normal_mode_creates_directories

**Category**: method_call  
**Description**: Test that normal mode creates directories  
**Expected**: self.assertTrue(skill_dir.exists(), 'Normal mode should create skill directory')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test configuration'
self.config = {'name': 'test-dry-run', 'base_url': 'https://example.com/', 'selectors': {'main_content': 'article', 'title': 'h1', 'code_blocks': 'pre code'}, 'url_patterns': {'include': [], 'exclude': []}, 'rate_limit': 0.1, 'max_pages': 10}

self.assertTrue(data_dir.exists(), 'Normal mode should create data directory')
self.assertTrue(skill_dir.exists(), 'Normal mode should create skill directory')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_integration.py:66*

### test_load_valid_config

**Category**: method_call  
**Description**: Test loading a valid configuration file  
**Expected**: self.assertEqual(loaded_config['base_url'], 'https://example.com/')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up temporary directory for test configs'
self.temp_dir = tempfile.mkdtemp()

self.assertEqual(loaded_config['name'], 'test-config')
self.assertEqual(loaded_config['base_url'], 'https://example.com/')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_integration.py:100*

### test_start_urls_fallback

**Category**: method_call  
**Description**: Test that start_urls defaults to base_url  
**Expected**: self.assertEqual(converter.pending_urls[0], 'https://example.com/')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertEqual(len(converter.pending_urls), 1)
self.assertEqual(converter.pending_urls[0], 'https://example.com/')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_integration.py:220*

### test_scraper_has_llms_txt_attributes

**Category**: method_call  
**Description**: Test that scraper has llms.txt detection attributes  
**Expected**: self.assertIsNone(scraper.llms_txt_variant)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertFalse(scraper.llms_txt_detected)
self.assertIsNone(scraper.llms_txt_variant)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_integration.py:258*

### test_scraper_has_try_llms_txt_method

**Category**: method_call  
**Description**: Test that scraper has _try_llms_txt method  
**Expected**: self.assertTrue(callable(scraper._try_llms_txt))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
self.assertTrue(hasattr(scraper, '_try_llms_txt'))
self.assertTrue(callable(scraper._try_llms_txt))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_integration.py:273*

### test_extract_empty_content

**Category**: method_call  
**Description**: Test extracting from empty HTML  
**Expected**: self.assertEqual(page['title'], '')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test converter'
config = {'name': 'test', 'base_url': 'https://example.com/', 'selectors': {'main_content': 'article', 'title': 'h1', 'code_blocks': 'pre code'}, 'rate_limit': 0.1, 'max_pages': 10}
self.converter = DocToSkillConverter(config, dry_run=True)

self.assertEqual(page['url'], 'https://example.com/test')
self.assertEqual(page['title'], '')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_integration.py:300*

### test_extract_empty_content

**Category**: method_call  
**Description**: Test extracting from empty HTML  
**Expected**: self.assertEqual(page['content'], '')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test converter'
config = {'name': 'test', 'base_url': 'https://example.com/', 'selectors': {'main_content': 'article', 'title': 'h1', 'code_blocks': 'pre code'}, 'rate_limit': 0.1, 'max_pages': 10}
self.converter = DocToSkillConverter(config, dry_run=True)

self.assertEqual(page['title'], '')
self.assertEqual(page['content'], '')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_integration.py:301*

### test_extract_empty_content

**Category**: method_call  
**Description**: Test extracting from empty HTML  
**Expected**: self.assertEqual(len(page['code_samples']), 0)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test converter'
config = {'name': 'test', 'base_url': 'https://example.com/', 'selectors': {'main_content': 'article', 'title': 'h1', 'code_blocks': 'pre code'}, 'rate_limit': 0.1, 'max_pages': 10}
self.converter = DocToSkillConverter(config, dry_run=True)

self.assertEqual(page['content'], '')
self.assertEqual(len(page['code_samples']), 0)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_integration.py:302*

### test_extract_basic_content

**Category**: method_call  
**Description**: Test extracting basic content  
**Expected**: self.assertIn('Page Title', page['title'])  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test converter'
config = {'name': 'test', 'base_url': 'https://example.com/', 'selectors': {'main_content': 'article', 'title': 'h1', 'code_blocks': 'pre code'}, 'rate_limit': 0.1, 'max_pages': 10}
self.converter = DocToSkillConverter(config, dry_run=True)

self.assertEqual(page['url'], 'https://example.com/test')
self.assertIn('Page Title', page['title'])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_integration.py:326*

### test_url_validation_no_patterns

**Category**: method_call  
**Description**: Test URL validation with no include/exclude patterns  
**Expected**: self.assertFalse(converter.is_valid_url('https://other.com/anything'))  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test converter'
self.config = {'name': 'test', 'base_url': 'https://docs.example.com/', 'url_patterns': {'include': ['/guide/', '/api/'], 'exclude': ['/blog/', '/about/']}, 'selectors': {'main_content': 'article', 'title': 'h1', 'code_blocks': 'pre code'}, 'rate_limit': 0.1, 'max_pages': 10}
self.converter = DocToSkillConverter(self.config, dry_run=True)

self.assertTrue(converter.is_valid_url('https://docs.example.com/anything'))
self.assertFalse(converter.is_valid_url('https://other.com/anything'))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_scraper_features.py:72*

### test_extract_pattern_with_example_marker

**Category**: method_call  
**Description**: Test pattern extraction with 'Example:' marker  
**Expected**: self.assertIn('example', patterns[0]['description'].lower())  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test converter'
config = {'name': 'test', 'base_url': 'https://example.com/', 'selectors': {'main_content': 'article', 'title': 'h1', 'code_blocks': 'pre'}, 'rate_limit': 0.1, 'max_pages': 10}
self.converter = DocToSkillConverter(config, dry_run=True)

self.assertGreater(len(patterns), 0)
self.assertIn('example', patterns[0]['description'].lower())
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_scraper_features.py:271*

### test_extract_pattern_with_usage_marker

**Category**: method_call  
**Description**: Test pattern extraction with 'Usage:' marker  
**Expected**: self.assertIn('usage', patterns[0]['description'].lower())  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test converter'
config = {'name': 'test', 'base_url': 'https://example.com/', 'selectors': {'main_content': 'article', 'title': 'h1', 'code_blocks': 'pre'}, 'rate_limit': 0.1, 'max_pages': 10}
self.converter = DocToSkillConverter(config, dry_run=True)

self.assertGreater(len(patterns), 0)
self.assertIn('usage', patterns[0]['description'].lower())
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_scraper_features.py:286*

### test_categorize_by_url

**Category**: method_call  
**Description**: Test categorization based on URL  
**Expected**: self.assertEqual(len(categories['api']), 1)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test converter'
config = {'name': 'test', 'base_url': 'https://example.com/', 'categories': {'getting_started': ['intro', 'tutorial', 'getting-started'], 'api': ['api', 'reference', 'class'], 'guides': ['guide', 'how-to']}, 'selectors': {'main_content': 'article', 'title': 'h1', 'code_blocks': 'pre'}, 'rate_limit': 0.1, 'max_pages': 10}
self.converter = DocToSkillConverter(config, dry_run=True)

self.assertIn('api', categories)
self.assertEqual(len(categories['api']), 1)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_scraper_features.py:334*

### test_categorize_by_title

**Category**: method_call  
**Description**: Test categorization based on title  
**Expected**: self.assertEqual(len(categories['api']), 1)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test converter'
config = {'name': 'test', 'base_url': 'https://example.com/', 'categories': {'getting_started': ['intro', 'tutorial', 'getting-started'], 'api': ['api', 'reference', 'class'], 'guides': ['guide', 'how-to']}, 'selectors': {'main_content': 'article', 'title': 'h1', 'code_blocks': 'pre'}, 'rate_limit': 0.1, 'max_pages': 10}
self.converter = DocToSkillConverter(config, dry_run=True)

self.assertIn('api', categories)
self.assertEqual(len(categories['api']), 1)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_scraper_features.py:348*

### test_categorize_to_other

**Category**: method_call  
**Description**: Test pages that don't match any category go to 'other'  
**Expected**: self.assertEqual(len(categories['other']), 1)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test converter'
config = {'name': 'test', 'base_url': 'https://example.com/', 'categories': {'getting_started': ['intro', 'tutorial', 'getting-started'], 'api': ['api', 'reference', 'class'], 'guides': ['guide', 'how-to']}, 'selectors': {'main_content': 'article', 'title': 'h1', 'code_blocks': 'pre'}, 'rate_limit': 0.1, 'max_pages': 10}
self.converter = DocToSkillConverter(config, dry_run=True)

self.assertIn('other', categories)
self.assertEqual(len(categories['other']), 1)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_scraper_features.py:376*

### test_empty_categories_removed

**Category**: method_call  
**Description**: Test empty categories are removed  
**Expected**: self.assertNotIn('guides', categories)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test converter'
config = {'name': 'test', 'base_url': 'https://example.com/', 'categories': {'getting_started': ['intro', 'tutorial', 'getting-started'], 'api': ['api', 'reference', 'class'], 'guides': ['guide', 'how-to']}, 'selectors': {'main_content': 'article', 'title': 'h1', 'code_blocks': 'pre'}, 'rate_limit': 0.1, 'max_pages': 10}
self.converter = DocToSkillConverter(config, dry_run=True)

self.assertIn('api', categories)
self.assertNotIn('guides', categories)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_scraper_features.py:392*

### test_extract_links_strips_anchor_fragments

**Category**: method_call  
**Description**: Test that anchor fragments (#anchor) are stripped from extracted links  
**Expected**: self.assertIn('https://example.com/docs/page.html', page['links'])  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test converter'
config = {'name': 'test', 'base_url': 'https://example.com/', 'selectors': {'main_content': 'article', 'title': 'h1', 'code_blocks': 'pre code'}, 'url_patterns': {'include': [], 'exclude': []}, 'rate_limit': 0.1, 'max_pages': 10}
self.converter = DocToSkillConverter(config, dry_run=True)

self.assertEqual(len(page['links']), 2)
self.assertIn('https://example.com/docs/page.html', page['links'])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_scraper_features.py:427*

### test_extract_links_strips_anchor_fragments

**Category**: method_call  
**Description**: Test that anchor fragments (#anchor) are stripped from extracted links  
**Expected**: self.assertIn('https://example.com/docs/other.html', page['links'])  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test converter'
config = {'name': 'test', 'base_url': 'https://example.com/', 'selectors': {'main_content': 'article', 'title': 'h1', 'code_blocks': 'pre code'}, 'url_patterns': {'include': [], 'exclude': []}, 'rate_limit': 0.1, 'max_pages': 10}
self.converter = DocToSkillConverter(config, dry_run=True)

self.assertIn('https://example.com/docs/page.html', page['links'])
self.assertIn('https://example.com/docs/other.html', page['links'])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_scraper_features.py:428*

### test_extract_links_no_anchor_duplicates

**Category**: method_call  
**Description**: Test that multiple anchor links to same page don't create duplicates  
**Expected**: self.assertEqual(page['links'][0], 'https://example.com/docs/api.html')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
'Set up test converter'
config = {'name': 'test', 'base_url': 'https://example.com/', 'selectors': {'main_content': 'article', 'title': 'h1', 'code_blocks': 'pre code'}, 'url_patterns': {'include': [], 'exclude': []}, 'rate_limit': 0.1, 'max_pages': 10}
self.converter = DocToSkillConverter(config, dry_run=True)

self.assertEqual(len(page['links']), 1)
self.assertEqual(page['links'][0], 'https://example.com/docs/api.html')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_scraper_features.py:447*

### test_simple_import

**Category**: method_call  
**Description**: Test simple import statement.  
**Expected**: self.assertEqual(deps[0].imported_module, 'os')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not ANALYZER_AVAILABLE:
    self.skipTest('dependency_analyzer not available')
self.analyzer = DependencyAnalyzer()

self.assertEqual(len(deps), 2)
self.assertEqual(deps[0].imported_module, 'os')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_dependency_analyzer.py:39*

### test_simple_import

**Category**: method_call  
**Description**: Test simple import statement.  
**Expected**: self.assertEqual(deps[0].import_type, 'import')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not ANALYZER_AVAILABLE:
    self.skipTest('dependency_analyzer not available')
self.analyzer = DependencyAnalyzer()

self.assertEqual(deps[0].imported_module, 'os')
self.assertEqual(deps[0].import_type, 'import')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_dependency_analyzer.py:40*

### test_simple_import

**Category**: method_call  
**Description**: Test simple import statement.  
**Expected**: self.assertFalse(deps[0].is_relative)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not ANALYZER_AVAILABLE:
    self.skipTest('dependency_analyzer not available')
self.analyzer = DependencyAnalyzer()

self.assertEqual(deps[0].import_type, 'import')
self.assertFalse(deps[0].is_relative)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_dependency_analyzer.py:41*

### test_from_import

**Category**: method_call  
**Description**: Test from...import statement.  
**Expected**: self.assertEqual(deps[0].imported_module, 'pathlib')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not ANALYZER_AVAILABLE:
    self.skipTest('dependency_analyzer not available')
self.analyzer = DependencyAnalyzer()

self.assertEqual(len(deps), 2)
self.assertEqual(deps[0].imported_module, 'pathlib')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_dependency_analyzer.py:49*

### test_from_import

**Category**: method_call  
**Description**: Test from...import statement.  
**Expected**: self.assertEqual(deps[0].import_type, 'from')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not ANALYZER_AVAILABLE:
    self.skipTest('dependency_analyzer not available')
self.analyzer = DependencyAnalyzer()

self.assertEqual(deps[0].imported_module, 'pathlib')
self.assertEqual(deps[0].import_type, 'from')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_dependency_analyzer.py:50*

### test_relative_import

**Category**: method_call  
**Description**: Test relative import.  
**Expected**: self.assertTrue(deps[0].is_relative)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not ANALYZER_AVAILABLE:
    self.skipTest('dependency_analyzer not available')
self.analyzer = DependencyAnalyzer()

self.assertEqual(len(deps), 2)
self.assertTrue(deps[0].is_relative)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_dependency_analyzer.py:58*

### test_relative_import

**Category**: method_call  
**Description**: Test relative import.  
**Expected**: self.assertEqual(deps[0].imported_module, '.')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not ANALYZER_AVAILABLE:
    self.skipTest('dependency_analyzer not available')
self.analyzer = DependencyAnalyzer()

self.assertTrue(deps[0].is_relative)
self.assertEqual(deps[0].imported_module, '.')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_dependency_analyzer.py:59*

### test_relative_import

**Category**: method_call  
**Description**: Test relative import.  
**Expected**: self.assertTrue(deps[1].is_relative)  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not ANALYZER_AVAILABLE:
    self.skipTest('dependency_analyzer not available')
self.analyzer = DependencyAnalyzer()

self.assertEqual(deps[0].imported_module, '.')
self.assertTrue(deps[1].is_relative)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_dependency_analyzer.py:60*

### test_relative_import

**Category**: method_call  
**Description**: Test relative import.  
**Expected**: self.assertEqual(deps[1].imported_module, '..common')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not ANALYZER_AVAILABLE:
    self.skipTest('dependency_analyzer not available')
self.analyzer = DependencyAnalyzer()

self.assertTrue(deps[1].is_relative)
self.assertEqual(deps[1].imported_module, '..common')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_dependency_analyzer.py:61*

### test_import_as

**Category**: method_call  
**Description**: Test import with alias.  
**Expected**: self.assertEqual(deps[0].imported_module, 'numpy')  
**Confidence**: 0.85  
**Tags**: unittest  

```python
# Setup
if not ANALYZER_AVAILABLE:
    self.skipTest('dependency_analyzer not available')
self.analyzer = DependencyAnalyzer()

self.assertEqual(len(deps), 2)
self.assertEqual(deps[0].imported_module, 'numpy')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_dependency_analyzer.py:69*

### test_get_agent_path_home_expansion

**Category**: instantiation  
**Description**: Instantiate get_agent_path: Test that ~ expands to home directory for global agents.  
**Expected**: assert path.is_absolute()  
**Confidence**: 0.80  

```python
path = get_agent_path('claude')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_install_agent.py:41*

### test_get_agent_path_project_relative

**Category**: instantiation  
**Description**: Instantiate get_agent_path: Test that project-relative paths use current directory.  
**Expected**: assert path.is_absolute()  
**Confidence**: 0.80  

```python
path = get_agent_path('cursor')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_install_agent.py:49*

### test_get_agent_path_project_relative_with_custom_root

**Category**: instantiation  
**Description**: Instantiate Path: Test project-relative paths with custom project root.  
**Expected**: assert path.is_absolute()  
**Confidence**: 0.80  

```python
custom_root = Path('/tmp/test-project')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_install_agent.py:57*

### test_get_agent_path_project_relative_with_custom_root

**Category**: instantiation  
**Description**: Instantiate get_agent_path: Test project-relative paths with custom project root.  
**Expected**: assert path.is_absolute()  
**Confidence**: 0.80  

```python
path = get_agent_path('cursor', project_root=custom_root)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_install_agent.py:58*

### test_agent_path_case_insensitive

**Category**: instantiation  
**Description**: Instantiate get_agent_path: Test that agent names are case-insensitive.  
**Expected**: assert path_lower == path_upper == path_mixed  
**Confidence**: 0.80  

```python
path_lower = get_agent_path('claude')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_install_agent.py:82*

### test_agent_path_case_insensitive

**Category**: instantiation  
**Description**: Instantiate get_agent_path: Test that agent names are case-insensitive.  
**Expected**: assert path_lower == path_upper == path_mixed  
**Confidence**: 0.80  

```python
path_upper = get_agent_path('CLAUDE')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_install_agent.py:83*

### test_agent_path_case_insensitive

**Category**: instantiation  
**Description**: Instantiate get_agent_path: Test that agent names are case-insensitive.  
**Expected**: assert path_lower == path_upper == path_mixed  
**Confidence**: 0.80  

```python
path_mixed = get_agent_path('Claude')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_install_agent.py:84*

### test_validate_valid_agent

**Category**: instantiation  
**Description**: Instantiate validate_agent_name: Test that valid agent names pass validation.  
**Expected**: assert is_valid is True  
**Confidence**: 0.80  

```python
is_valid, error = validate_agent_name('claude')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_install_agent.py:93*

### test_validate_invalid_agent_suggests_similar

**Category**: instantiation  
**Description**: Instantiate validate_agent_name: Test that similar agent names are suggested for typos.  
**Expected**: assert is_valid is False  
**Confidence**: 0.80  

```python
is_valid, error = validate_agent_name('courser')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_install_agent.py:99*

### test_validate_special_all

**Category**: instantiation  
**Description**: Instantiate validate_agent_name: Test that 'all' is a valid special agent name.  
**Expected**: assert is_valid is True  
**Confidence**: 0.80  

```python
is_valid, error = validate_agent_name('all')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_install_agent.py:105*

### test_package_valid_skill_directory

**Category**: instantiation  
**Description**: Instantiate create_test_skill_directory: Test packaging a valid skill directory  
**Confidence**: 0.80  
**Tags**: unittest  

```python
skill_dir = self.create_test_skill_directory(tmpdir)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_package_skill.py:42*

### test_package_valid_skill_directory

**Category**: instantiation  
**Description**: Instantiate package_skill: Test packaging a valid skill directory  
**Confidence**: 0.80  
**Tags**: unittest  

```python
success, zip_path = package_skill(skill_dir, open_folder_after=False, skip_quality_check=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_package_skill.py:44*

### test_package_creates_correct_zip_structure

**Category**: instantiation  
**Description**: Instantiate create_test_skill_directory: Test that packaged zip contains correct files  
**Confidence**: 0.80  
**Tags**: unittest  

```python
skill_dir = self.create_test_skill_directory(tmpdir)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_package_skill.py:57*

### test_package_creates_correct_zip_structure

**Category**: instantiation  
**Description**: Instantiate package_skill: Test that packaged zip contains correct files  
**Confidence**: 0.80  
**Tags**: unittest  

```python
success, zip_path = package_skill(skill_dir, open_folder_after=False, skip_quality_check=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_package_skill.py:59*

### test_package_excludes_backup_files

**Category**: instantiation  
**Description**: Instantiate create_test_skill_directory: Test that .backup files are excluded from zip  
**Confidence**: 0.80  
**Tags**: unittest  

```python
skill_dir = self.create_test_skill_directory(tmpdir)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_package_skill.py:79*

### test_package_excludes_backup_files

**Category**: instantiation  
**Description**: Instantiate package_skill: Test that .backup files are excluded from zip  
**Confidence**: 0.80  
**Tags**: unittest  

```python
success, zip_path = package_skill(skill_dir, open_folder_after=False, skip_quality_check=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_package_skill.py:84*

### test_package_nonexistent_directory

**Category**: instantiation  
**Description**: Instantiate package_skill: Test packaging a nonexistent directory  
**Expected**: self.assertFalse(success)  
**Confidence**: 0.80  
**Tags**: unittest  

```python
success, zip_path = package_skill('/nonexistent/path', open_folder_after=False, skip_quality_check=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_package_skill.py:97*

### test_package_directory_without_skill_md

**Category**: instantiation  
**Description**: Instantiate package_skill: Test packaging directory without SKILL.md  
**Confidence**: 0.80  
**Tags**: unittest  

```python
success, zip_path = package_skill(skill_dir, open_folder_after=False, skip_quality_check=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_package_skill.py:110*

### test_health_check_endpoint

**Category**: instantiation  
**Description**: Instantiate get: Test that health check endpoint returns correct response.  
**Confidence**: 0.80  

```python
response = client.get('/health')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_server_fastmcp_http.py:53*

### test_github_url_to_basic_analysis

**Category**: instantiation  
**Description**: Instantiate CodeStream: Test complete pipeline: GitHub URL → Basic analysis → Merged output

This tests the fast path (1-2 minutes) without C3.x analysis.  
**Expected**: assert result.source_type == 'github'  
**Confidence**: 0.80  
**Tags**: mock  

```python
# Setup
# Fixtures: mock_fetcher_class, tmp_path

code_stream = CodeStream(directory=tmp_path, files=[tmp_path / 'main.py', tmp_path / 'utils.js'])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_e2e_three_stream_pipeline.py:57*

### test_github_url_to_basic_analysis

**Category**: instantiation  
**Description**: Instantiate DocsStream: Test complete pipeline: GitHub URL → Basic analysis → Merged output

This tests the fast path (1-2 minutes) without C3.x analysis.  
**Expected**: assert result.source_type == 'github'  
**Confidence**: 0.80  
**Tags**: mock  

```python
# Setup
# Fixtures: mock_fetcher_class, tmp_path

docs_stream = DocsStream(readme='# Test Project\n\nA simple test project for demonstrating the three-stream architecture.\n\n## Installation\n\n```bash\npip install test-project\n```\n\n## Quick Start\n\n```python\nfrom test_project import hello\nhello()\n```\n', contributing='# Contributing\n\nPull requests welcome!', docs_files=[{'path': 'docs/guide.md', 'content': '# User Guide\n\nHow to use this project.'}])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_e2e_three_stream_pipeline.py:60*

### test_github_url_to_basic_analysis

**Category**: instantiation  
**Description**: Instantiate InsightsStream: Test complete pipeline: GitHub URL → Basic analysis → Merged output

This tests the fast path (1-2 minutes) without C3.x analysis.  
**Expected**: assert result.source_type == 'github'  
**Confidence**: 0.80  
**Tags**: mock  

```python
# Setup
# Fixtures: mock_fetcher_class, tmp_path

insights_stream = InsightsStream(metadata={'stars': 1234, 'forks': 56, 'language': 'Python', 'description': 'A test project'}, common_problems=[{'title': 'Installation fails on Windows', 'number': 42, 'state': 'open', 'comments': 15, 'labels': ['bug', 'windows']}, {'title': 'Import error with Python 3.6', 'number': 38, 'state': 'open', 'comments': 10, 'labels': ['bug', 'python']}], known_solutions=[{'title': 'Fixed: Module not found', 'number': 35, 'state': 'closed', 'comments': 8, 'labels': ['bug']}], top_labels=[{'label': 'bug', 'count': 25}, {'label': 'enhancement', 'count': 15}, {'label': 'documentation', 'count': 10}])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_e2e_three_stream_pipeline.py:83*

### test_github_url_to_basic_analysis

**Category**: instantiation  
**Description**: Instantiate ThreeStreamData: Test complete pipeline: GitHub URL → Basic analysis → Merged output

This tests the fast path (1-2 minutes) without C3.x analysis.  
**Expected**: assert result.source_type == 'github'  
**Confidence**: 0.80  
**Tags**: mock  

```python
# Setup
# Fixtures: mock_fetcher_class, tmp_path

three_streams = ThreeStreamData(code_stream, docs_stream, insights_stream)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_e2e_three_stream_pipeline.py:121*

### test_github_url_to_basic_analysis

**Category**: instantiation  
**Description**: Instantiate analyze: Test complete pipeline: GitHub URL → Basic analysis → Merged output

This tests the fast path (1-2 minutes) without C3.x analysis.  
**Expected**: assert result.source_type == 'github'  
**Confidence**: 0.80  
**Tags**: mock  

```python
# Setup
# Fixtures: mock_fetcher_class, tmp_path

result = analyzer.analyze(source='https://github.com/test/project', depth='basic', fetch_github_metadata=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_e2e_three_stream_pipeline.py:126*

### test_issue_categorization_by_topic

**Category**: instantiation  
**Description**: Instantiate categorize_issues_by_topic: Test that issues are correctly categorized by topic keywords.  
**Expected**: assert 'oauth' in categorized or 'auth' in categorized or 'authentication' in categorized  
**Confidence**: 0.80  

```python
categorized = categorize_issues_by_topic(problems, solutions, topics)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_e2e_three_stream_pipeline.py:207*

### test_router_generation_with_github_streams

**Category**: instantiation  
**Description**: Instantiate CodeStream: Test complete router generation workflow with GitHub streams.

Validates:
1. Router config created
2. Router SKILL.md includes GitHub metadata
3. Router SKILL.md includes README quick start
4. Router SKILL.md includes common issues
5. Routing keywords include GitHub labels (2x weight)  
**Expected**: assert generator.github_metadata is not None  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

code_stream = CodeStream(directory=tmp_path, files=[])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_e2e_three_stream_pipeline.py:262*

### test_router_generation_with_github_streams

**Category**: instantiation  
**Description**: Instantiate DocsStream: Test complete router generation workflow with GitHub streams.

Validates:
1. Router config created
2. Router SKILL.md includes GitHub metadata
3. Router SKILL.md includes README quick start
4. Router SKILL.md includes common issues
5. Routing keywords include GitHub labels (2x weight)  
**Expected**: assert generator.github_metadata is not None  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

docs_stream = DocsStream(readme='# Test Project\n\nFast and simple test framework.\n\n## Installation\n\n```bash\npip install test-project\n```\n\n## Quick Start\n\n```python\nimport testproject\ntestproject.run()\n```\n', contributing='# Contributing\n\nWelcome!', docs_files=[])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_e2e_three_stream_pipeline.py:263*

### test_router_generation_with_github_streams

**Category**: instantiation  
**Description**: Instantiate InsightsStream: Test complete router generation workflow with GitHub streams.

Validates:
1. Router config created
2. Router SKILL.md includes GitHub metadata
3. Router SKILL.md includes README quick start
4. Router SKILL.md includes common issues
5. Routing keywords include GitHub labels (2x weight)  
**Expected**: assert generator.github_metadata is not None  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

insights_stream = InsightsStream(metadata={'stars': 5000, 'forks': 250, 'language': 'Python', 'description': 'Fast test framework'}, common_problems=[{'title': 'OAuth setup fails', 'number': 150, 'state': 'open', 'comments': 30, 'labels': ['bug', 'oauth']}, {'title': 'Async deadlock', 'number': 142, 'state': 'open', 'comments': 25, 'labels': ['async', 'bug']}, {'title': 'Token refresh issue', 'number': 130, 'state': 'open', 'comments': 20, 'labels': ['oauth']}], known_solutions=[{'title': 'Fixed OAuth redirect', 'number': 120, 'state': 'closed', 'comments': 15, 'labels': ['oauth']}, {'title': 'Resolved async race', 'number': 110, 'state': 'closed', 'comments': 12, 'labels': ['async']}], top_labels=[{'label': 'oauth', 'count': 45}, {'label': 'async', 'count': 38}, {'label': 'bug', 'count': 30}])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_e2e_three_stream_pipeline.py:284*

### test_router_generation_with_github_streams

**Category**: instantiation  
**Description**: Instantiate ThreeStreamData: Test complete router generation workflow with GitHub streams.

Validates:
1. Router config created
2. Router SKILL.md includes GitHub metadata
3. Router SKILL.md includes README quick start
4. Router SKILL.md includes common issues
5. Routing keywords include GitHub labels (2x weight)  
**Expected**: assert generator.github_metadata is not None  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

github_streams = ThreeStreamData(code_stream, docs_stream, insights_stream)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_e2e_three_stream_pipeline.py:336*

### test_server_initialization

**Category**: instantiation  
**Description**: Instantiate Server: Test server initializes correctly  
**Expected**: self.assertEqual(app.name, 'test-skill-seeker')  
**Confidence**: 0.80  
**Tags**: unittest  

```python
app = mcp.server.Server('test-skill-seeker')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_mcp_server.py:61*

### test_server_initialization

**Category**: instantiation  
**Description**: Instantiate Server: Test server initializes correctly  
**Expected**: self.assertEqual(app.name, 'test-skill-seeker')  
**Confidence**: 0.80  
**Tags**: unittest  

```python
app = mcp.server.Server('test-skill-seeker')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_mcp_server.py:61*

### test_create_headers_no_token

**Category**: instantiation  
**Description**: Instantiate create_github_headers: Test header creation without token.  
**Expected**: assert headers == {}  
**Confidence**: 0.80  

```python
headers = create_github_headers(None)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_rate_limit_handler.py:25*

### test_create_headers_with_token

**Category**: instantiation  
**Description**: Instantiate create_github_headers: Test header creation with token.  
**Expected**: assert headers == {'Authorization': 'token ghp_test123'}  
**Confidence**: 0.80  

```python
headers = create_github_headers(token)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_rate_limit_handler.py:31*

### test_init_without_token

**Category**: instantiation  
**Description**: Instantiate RateLimitHandler: Test initialization without token.  
**Expected**: assert handler.token is None  
**Confidence**: 0.80  

```python
handler = RateLimitHandler(token=None, interactive=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_rate_limit_handler.py:36*

### test_init_with_token

**Category**: instantiation  
**Description**: Instantiate RateLimitHandler: Test initialization with token.  
**Expected**: assert handler.token == 'ghp_test'  
**Confidence**: 0.80  

```python
handler = RateLimitHandler(token='ghp_test', interactive=False)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_rate_limit_handler.py:43*

### test_init_with_config_strategy

**Category**: instantiation  
**Description**: Instantiate RateLimitHandler: Test initialization pulls strategy from config.  
**Expected**: assert handler.strategy == 'wait'  
**Confidence**: 0.80  
**Tags**: mock  

```python
# Setup
# Fixtures: mock_get_config

handler = RateLimitHandler(token='ghp_test', interactive=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_rate_limit_handler.py:62*

### test_extract_rate_limit_info

**Category**: instantiation  
**Description**: Instantiate int: Test extracting rate limit info from response headers.  
**Expected**: assert info['limit'] == 5000  
**Confidence**: 0.80  
**Tags**: mock  

```python
reset_time = int((datetime.now() + timedelta(minutes=30)).timestamp())
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_rate_limit_handler.py:73*

### test_extract_rate_limit_info

**Category**: instantiation  
**Description**: Instantiate extract_rate_limit_info: Test extracting rate limit info from response headers.  
**Expected**: assert info['limit'] == 5000  
**Confidence**: 0.80  
**Tags**: mock  

```python
info = handler.extract_rate_limit_info(mock_response)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_rate_limit_handler.py:80*

### test_check_upfront_no_token_declined

**Category**: instantiation  
**Description**: Instantiate RateLimitHandler: Test upfront check with no token, user declines.  
**Expected**: assert result is False  
**Confidence**: 0.80  
**Tags**: mock  

```python
# Setup
# Fixtures: mock_input

handler = RateLimitHandler(token=None, interactive=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_rate_limit_handler.py:90*

### test_check_upfront_no_token_accepted

**Category**: instantiation  
**Description**: Instantiate RateLimitHandler: Test upfront check with no token, user accepts.  
**Expected**: assert result is True  
**Confidence**: 0.80  
**Tags**: mock  

```python
# Setup
# Fixtures: mock_input

handler = RateLimitHandler(token=None, interactive=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_rate_limit_handler.py:100*

### test_check_upfront_no_token_non_interactive

**Category**: instantiation  
**Description**: Instantiate RateLimitHandler: Test upfront check with no token in non-interactive mode.  
**Expected**: assert result is True  
**Confidence**: 0.80  

```python
handler = RateLimitHandler(token=None, interactive=False)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_rate_limit_handler.py:109*

### test_scenario_1_github_three_stream_fetcher

**Category**: instantiation  
**Description**: Instantiate GitHubThreeStreamFetcher: Test GitHub three-stream fetcher with mock data.  
**Confidence**: 0.80  
**Tags**: mock  

```python
# Setup
# Fixtures: mock_github_repo, mock_github_api_data

fetcher = GitHubThreeStreamFetcher('https://github.com/jlowin/fastmcp', interactive=False)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_architecture_scenarios.py:222*

### test_scenario_1_unified_analyzer_github

**Category**: instantiation  
**Description**: Instantiate analyze: Test unified analyzer with GitHub source.  
**Confidence**: 0.80  
**Tags**: mock  

```python
# Setup
# Fixtures: mock_github_repo, mock_github_api_data

result = analyzer.analyze(source='https://github.com/jlowin/fastmcp', depth='c3x', fetch_github_metadata=True, interactive=False)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_architecture_scenarios.py:292*

### test_scenario_1_router_generation

**Category**: instantiation  
**Description**: Instantiate RouterGenerator: Test router generation with GitHub streams.  
**Expected**: assert 'fastmcp' in skill_md.lower()  
**Confidence**: 0.80  
**Tags**: mock  

```python
# Setup
# Fixtures: tmp_path

generator = RouterGenerator(config_paths=[str(config1), str(config2)], router_name='fastmcp', github_streams=mock_streams)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_architecture_scenarios.py:393*

### test_scenario_1_router_generation

**Category**: instantiation  
**Description**: Instantiate count: Test router generation with GitHub streams.  
**Expected**: assert oauth_count >= 2  
**Confidence**: 0.80  
**Tags**: mock  

```python
# Setup
# Fixtures: tmp_path

oauth_count = oauth_keywords.count('oauth')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_architecture_scenarios.py:424*

### test_scenario_1_quality_metrics

**Category**: instantiation  
**Description**: Instantiate split: Test quality metrics meet architecture targets.  
**Expected**: assert len(lines) <= 200, f'Router too large: {len(lines)} lines (max 200)'  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

lines = router_md.strip().split('\n')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_architecture_scenarios.py:463*

### test_scenario_2_issue_categorization

**Category**: instantiation  
**Description**: Instantiate categorize_issues_by_topic: Test categorizing GitHub issues by topic.  
**Expected**: assert 'oauth' in categorized  
**Confidence**: 0.80  

```python
categorized = categorize_issues_by_topic(problems, solutions, topics)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_architecture_scenarios.py:551*

### run_bootstrap

**Category**: instantiation  
**Description**: Instantiate run: Execute bootstrap script and return result  
**Confidence**: 0.80  
**Tags**: pytest  

```python
# Setup
# Fixtures: project_root

result = subprocess.run(['bash', str(script)], cwd=project_root, capture_output=True, text=True, timeout=timeout)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_bootstrap_skill_e2e.py:45*

### test_bootstrap_validates_yaml_frontmatter

**Category**: instantiation  
**Description**: Instantiate split: Verify generated SKILL.md has valid YAML frontmatter  
**Expected**: assert closing_found, 'Missing frontmatter closing delimiter'  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: run_bootstrap, output_skill_dir

lines = content.split('\n')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_bootstrap_skill_e2e.py:96*

### test_bootstrap_output_line_count

**Category**: instantiation  
**Description**: Instantiate len: Verify output SKILL.md has reasonable line count  
**Expected**: assert line_count > 100, f'SKILL.md too short: {line_count} lines'  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: run_bootstrap, output_skill_dir

line_count = len((output_skill_dir / 'SKILL.md').read_text().splitlines())
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_bootstrap_skill_e2e.py:114*

### test_skill_installable_in_venv

**Category**: instantiation  
**Description**: Instantiate run: Test skill is installable in clean virtual environment  
**Expected**: assert result.returncode == 0, f'Install failed: {result.stderr}'  
**Confidence**: 0.80  
**Tags**: pytest  

```python
# Setup
# Fixtures: run_bootstrap, output_skill_dir, tmp_path

result = subprocess.run([str(pip_path), 'install', '-e', '.'], cwd=output_skill_dir.parent.parent, capture_output=True, text=True, timeout=120)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_bootstrap_skill_e2e.py:134*

### test_skill_packageable_with_adaptors

**Category**: instantiation  
**Description**: Instantiate get_adaptor: Verify bootstrap output works with all platform adaptors  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: run_bootstrap, output_skill_dir, tmp_path

adaptor = get_adaptor('claude')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_bootstrap_skill_e2e.py:153*

### test_skill_packageable_with_adaptors

**Category**: instantiation  
**Description**: Instantiate package: Verify bootstrap output works with all platform adaptors  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: run_bootstrap, output_skill_dir, tmp_path

package_path = adaptor.package(skill_dir=output_skill_dir, output_path=tmp_path)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_bootstrap_skill_e2e.py:157*

### test_codebase_analysis_enabled_by_default

**Category**: instantiation  
**Description**: Instantiate join: Test that enable_codebase_analysis defaults to True.  
**Expected**: assert github_source.get('enable_codebase_analysis', True)  
**Confidence**: 0.80  
**Tags**: mock  

```python
# Setup
# Fixtures: mock_config, temp_dir

config_path = os.path.join(temp_dir, 'config.json')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_c3_integration.py:149*

### test_codebase_analysis_enabled_by_default

**Category**: instantiation  
**Description**: Instantiate UnifiedScraper: Test that enable_codebase_analysis defaults to True.  
**Expected**: assert github_source.get('enable_codebase_analysis', True)  
**Confidence**: 0.80  
**Tags**: mock  

```python
# Setup
# Fixtures: mock_config, temp_dir

scraper = UnifiedScraper(config_path)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_c3_integration.py:154*

### test_skip_codebase_analysis_flag

**Category**: instantiation  
**Description**: Instantiate join: Test --skip-codebase-analysis CLI flag disables analysis.  
**Expected**: assert not github_source['enable_codebase_analysis']  
**Confidence**: 0.80  
**Tags**: mock  

```python
# Setup
# Fixtures: mock_config, temp_dir

config_path = os.path.join(temp_dir, 'config.json')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_c3_integration.py:163*

### test_skip_codebase_analysis_flag

**Category**: instantiation  
**Description**: Instantiate UnifiedScraper: Test --skip-codebase-analysis CLI flag disables analysis.  
**Expected**: assert not github_source['enable_codebase_analysis']  
**Confidence**: 0.80  
**Tags**: mock  

```python
# Setup
# Fixtures: mock_config, temp_dir

scraper = UnifiedScraper(config_path)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_c3_integration.py:168*

### test_architecture_md_generation

**Category**: instantiation  
**Description**: Instantiate UnifiedSkillBuilder: Test ARCHITECTURE.md is generated with all 8 sections.  
**Expected**: assert os.path.exists(arch_file)  
**Confidence**: 0.80  
**Tags**: mock  

```python
# Setup
# Fixtures: mock_config, mock_c3_data, temp_dir

builder = UnifiedSkillBuilder(mock_config, scraped_data)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_c3_integration.py:187*

### test_architecture_md_generation

**Category**: instantiation  
**Description**: Instantiate join: Test ARCHITECTURE.md is generated with all 8 sections.  
**Expected**: assert os.path.exists(arch_file)  
**Confidence**: 0.80  
**Tags**: mock  

```python
# Setup
# Fixtures: mock_config, mock_c3_data, temp_dir

c3_dir = os.path.join(temp_dir, 'references', 'codebase_analysis')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_c3_integration.py:191*

### test_architecture_md_generation

**Category**: instantiation  
**Description**: Instantiate join: Test ARCHITECTURE.md is generated with all 8 sections.  
**Expected**: assert os.path.exists(arch_file)  
**Confidence**: 0.80  
**Tags**: mock  

```python
# Setup
# Fixtures: mock_config, mock_c3_data, temp_dir

arch_file = os.path.join(c3_dir, 'ARCHITECTURE.md')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_c3_integration.py:196*

### test_c3_reference_directory_structure

**Category**: instantiation  
**Description**: Instantiate UnifiedSkillBuilder: Test correct C3.x reference directory structure is created.  
**Expected**: assert os.path.exists(os.path.join(c3_dir, 'ARCHITECTURE.md'))  
**Confidence**: 0.80  
**Tags**: mock  

```python
# Setup
# Fixtures: mock_config, mock_c3_data, temp_dir

builder = UnifiedSkillBuilder(mock_config, scraped_data)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_c3_integration.py:228*

### test_c3_reference_directory_structure

**Category**: instantiation  
**Description**: Instantiate join: Test correct C3.x reference directory structure is created.  
**Expected**: assert os.path.exists(os.path.join(c3_dir, 'ARCHITECTURE.md'))  
**Confidence**: 0.80  
**Tags**: mock  

```python
# Setup
# Fixtures: mock_config, mock_c3_data, temp_dir

c3_dir = os.path.join(temp_dir, 'references', 'codebase_analysis')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_c3_integration.py:232*

### test_summarize_reference_basic

**Category**: instantiation  
**Description**: Instantiate LocalSkillEnhancer: Test basic summarization preserves structure  
**Expected**: assert '# Introduction' in summarized  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

enhancer = LocalSkillEnhancer(tmp_path)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_smart_summarization.py:18*

### test_summarize_reference_basic

**Category**: instantiation  
**Description**: Instantiate summarize_reference: Test basic summarization preserves structure  
**Expected**: assert '# Introduction' in summarized  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

summarized = enhancer.summarize_reference(content, target_ratio=0.3)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_smart_summarization.py:46*

### test_summarize_preserves_code_blocks

**Category**: instantiation  
**Description**: Instantiate LocalSkillEnhancer: Test that code blocks are prioritized and preserved  
**Expected**: assert summarized.count('```python') >= 2  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

enhancer = LocalSkillEnhancer(tmp_path)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_smart_summarization.py:57*

### test_summarize_preserves_code_blocks

**Category**: instantiation  
**Description**: Instantiate summarize_reference: Test that code blocks are prioritized and preserved  
**Expected**: assert summarized.count('```python') >= 2  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

summarized = enhancer.summarize_reference(content, target_ratio=0.5)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_smart_summarization.py:88*

### test_summarize_large_content

**Category**: instantiation  
**Description**: Instantiate LocalSkillEnhancer: Test summarization with very large content  
**Expected**: assert summarized_size < original_size  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

enhancer = LocalSkillEnhancer(tmp_path)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_smart_summarization.py:96*

### test_summarize_large_content

**Category**: instantiation  
**Description**: Instantiate join: Test summarization with very large content  
**Expected**: assert summarized_size < original_size  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

content = '\n'.join(sections)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_smart_summarization.py:117*

### test_summarize_large_content

**Category**: instantiation  
**Description**: Instantiate len: Test summarization with very large content  
**Expected**: assert summarized_size < original_size  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

original_size = len(content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_smart_summarization.py:118*

### test_summarize_large_content

**Category**: instantiation  
**Description**: Instantiate summarize_reference: Test summarization with very large content  
**Expected**: assert summarized_size < original_size  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

summarized = enhancer.summarize_reference(content, target_ratio=0.3)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_smart_summarization.py:121*

### test_summarize_large_content

**Category**: instantiation  
**Description**: Instantiate len: Test summarization with very large content  
**Expected**: assert summarized_size < original_size  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

summarized_size = len(summarized)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_smart_summarization.py:122*

### test_create_prompt_without_summarization

**Category**: instantiation  
**Description**: Instantiate LocalSkillEnhancer: Test prompt creation with normal-sized content  
**Expected**: assert prompt is not None  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

enhancer = LocalSkillEnhancer(skill_dir)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_smart_summarization.py:143*

### test_categorize_issues_basic

**Category**: instantiation  
**Description**: Instantiate categorize_issues_by_topic: Test basic issue categorization.  
**Expected**: assert 'oauth' in categorized  
**Confidence**: 0.80  

```python
categorized = categorize_issues_by_topic(problems, solutions, topics)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_merge_sources_github.py:54*

### test_categorize_issues_keyword_matching

**Category**: instantiation  
**Description**: Instantiate categorize_issues_by_topic: Test keyword matching in titles and labels.  
**Expected**: assert 'database' in categorized or 'other' in categorized  
**Confidence**: 0.80  

```python
categorized = categorize_issues_by_topic(problems, solutions, topics)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_merge_sources_github.py:76*

### test_categorize_issues_multi_keyword_topic

**Category**: instantiation  
**Description**: Instantiate categorize_issues_by_topic: Test topics with multiple keywords.  
**Expected**: assert 'async api' in categorized  
**Confidence**: 0.80  

```python
categorized = categorize_issues_by_topic(problems, solutions, topics)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_merge_sources_github.py:96*

### test_categorize_issues_no_match_goes_to_other

**Category**: instantiation  
**Description**: Instantiate categorize_issues_by_topic: Test that unmatched issues go to 'other' category.  
**Expected**: assert 'other' in categorized  
**Confidence**: 0.80  

```python
categorized = categorize_issues_by_topic(problems, solutions, topics)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_merge_sources_github.py:117*

### test_categorize_issues_empty_lists

**Category**: instantiation  
**Description**: Instantiate categorize_issues_by_topic: Test categorization with empty input.  
**Expected**: assert len(categorized) == 0  
**Confidence**: 0.80  

```python
categorized = categorize_issues_by_topic([], [], ['oauth'])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_merge_sources_github.py:124*

### test_generate_hybrid_content_basic

**Category**: instantiation  
**Description**: Instantiate generate_hybrid_content: Test basic hybrid content generation.  
**Expected**: assert 'api_reference' in hybrid  
**Confidence**: 0.80  

```python
hybrid = generate_hybrid_content(api_data, github_docs, github_insights, conflicts)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_merge_sources_github.py:176*

### test_generate_hybrid_content_with_conflicts

**Category**: instantiation  
**Description**: Instantiate generate_hybrid_content: Test hybrid content with conflicts.  
**Expected**: assert hybrid['conflict_summary']['total_conflicts'] == 2  
**Confidence**: 0.80  

```python
hybrid = generate_hybrid_content(api_data, github_docs, github_insights, conflicts)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_merge_sources_github.py:221*

### test_generate_hybrid_content_no_github_data

**Category**: instantiation  
**Description**: Instantiate generate_hybrid_content: Test hybrid content with no GitHub data.  
**Expected**: assert 'api_reference' in hybrid  
**Confidence**: 0.80  

```python
hybrid = generate_hybrid_content(api_data, None, None, [])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_merge_sources_github.py:234*

### test_match_issues_to_apis_basic

**Category**: instantiation  
**Description**: Instantiate _match_issues_to_apis: Test basic issue to API matching.  
**Expected**: assert 'oauth_login' in issue_links  
**Confidence**: 0.80  

```python
issue_links = _match_issues_to_apis(apis, problems, solutions)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_merge_sources_github.py:270*

### test_init_with_repo_name

**Category**: instantiation  
**Description**: Instantiate GitHubScraper: Test initialization with repository name  
**Expected**: self.assertEqual(scraper.repo_name, 'facebook/react')  
**Confidence**: 0.80  
**Tags**: unittest  

```python
# Setup
if not PYGITHUB_AVAILABLE:
    self.skipTest('PyGithub not installed')
from skill_seekers.cli.github_scraper import GitHubScraper
self.GitHubScraper = GitHubScraper
self.temp_dir = tempfile.mkdtemp()
self.output_dir = Path(self.temp_dir)

scraper = self.GitHubScraper(config)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_github_scraper.py:57*

### test_init_with_token_from_config

**Category**: instantiation  
**Description**: Instantiate GitHubScraper: Test initialization with token from config  
**Confidence**: 0.80  
**Tags**: unittest, mock  

```python
# Setup
if not PYGITHUB_AVAILABLE:
    self.skipTest('PyGithub not installed')
from skill_seekers.cli.github_scraper import GitHubScraper
self.GitHubScraper = GitHubScraper
self.temp_dir = tempfile.mkdtemp()
self.output_dir = Path(self.temp_dir)

_scraper = self.GitHubScraper(config)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_github_scraper.py:72*

### test_init_with_token_from_env

**Category**: instantiation  
**Description**: Instantiate GitHubScraper: Test initialization with token from environment variable  
**Confidence**: 0.80  
**Tags**: unittest, mock  

```python
# Setup
if not PYGITHUB_AVAILABLE:
    self.skipTest('PyGithub not installed')
from skill_seekers.cli.github_scraper import GitHubScraper
self.GitHubScraper = GitHubScraper
self.temp_dir = tempfile.mkdtemp()
self.output_dir = Path(self.temp_dir)

_scraper = self.GitHubScraper(config)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_github_scraper.py:83*

### test_init_without_token

**Category**: instantiation  
**Description**: Instantiate GitHubScraper: Test initialization without authentication  
**Confidence**: 0.80  
**Tags**: unittest, mock  

```python
# Setup
if not PYGITHUB_AVAILABLE:
    self.skipTest('PyGithub not installed')
from skill_seekers.cli.github_scraper import GitHubScraper
self.GitHubScraper = GitHubScraper
self.temp_dir = tempfile.mkdtemp()
self.output_dir = Path(self.temp_dir)

scraper = self.GitHubScraper(config)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_github_scraper.py:94*

### test_token_priority_env_over_config

**Category**: instantiation  
**Description**: Instantiate GitHubScraper: Test that GITHUB_TOKEN env var takes priority over config  
**Confidence**: 0.80  
**Tags**: unittest, mock  

```python
# Setup
if not PYGITHUB_AVAILABLE:
    self.skipTest('PyGithub not installed')
from skill_seekers.cli.github_scraper import GitHubScraper
self.GitHubScraper = GitHubScraper
self.temp_dir = tempfile.mkdtemp()
self.output_dir = Path(self.temp_dir)

scraper = self.GitHubScraper(config)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_github_scraper.py:107*

### test_extract_readme_success

**Category**: instantiation  
**Description**: Instantiate GitHubScraper: Test successful README extraction  
**Confidence**: 0.80  
**Tags**: unittest, mock  

```python
# Setup
if not PYGITHUB_AVAILABLE:
    self.skipTest('PyGithub not installed')
from skill_seekers.cli.github_scraper import GitHubScraper
self.GitHubScraper = GitHubScraper

scraper = self.GitHubScraper(config)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_github_scraper.py:130*

### test_mcp_directory_structure

**Category**: instantiation  
**Description**: Instantiate Path: Test that MCP directory structure is correct (new src/ layout)  
**Expected**: assert mcp_dir.exists(), 'src/skill_seekers/mcp/ directory should exist'  
**Confidence**: 0.80  

```python
mcp_dir = Path('src/skill_seekers/mcp')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_setup_scripts.py:242*

### test_mcp_directory_structure

**Category**: instantiation  
**Description**: Instantiate Path: Test that MCP directory structure is correct (new src/ layout)  
**Confidence**: 0.80  

```python
old_mcp = Path('mcp')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_setup_scripts.py:249*

### test_mcp_directory_structure

**Category**: instantiation  
**Description**: Instantiate Path: Test that MCP directory structure is correct (new src/ layout)  
**Confidence**: 0.80  

```python
old_skill_seeker_mcp = Path('skill_seeker_mcp')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_setup_scripts.py:250*

### test_bash_syntax_valid

**Category**: instantiation  
**Description**: Instantiate run: Test that setup_mcp.sh has valid bash syntax  
**Expected**: assert result.returncode == 0, f'Bash syntax error: {result.stderr}'  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: script_path

result = subprocess.run(['bash', '-n', str(script_path)], capture_output=True, text=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_setup_scripts.py:36*

### test_references_correct_mcp_directory

**Category**: instantiation  
**Description**: Instantiate findall: Test that script references src/skill_seekers/mcp/ (v2.4.0 MCP 2025 upgrade)  
**Expected**: assert len(old_mcp_refs) == 0, f"Found {len(old_mcp_refs)} references to old 'mcp/' directory: {old_mcp_refs}"  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: script_content

old_mcp_refs = re.findall('(?:^|[^a-z_])(?<!/)mcp/(?!\\.json)', script_content, re.MULTILINE)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_setup_scripts.py:42*

### test_references_correct_mcp_directory

**Category**: instantiation  
**Description**: Instantiate findall: Test that script references src/skill_seekers/mcp/ (v2.4.0 MCP 2025 upgrade)  
**Expected**: assert len(old_mcp_refs) == 0, f"Found {len(old_mcp_refs)} references to old 'mcp/' directory: {old_mcp_refs}"  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: script_content

old_skill_seeker_refs = re.findall('skill_seeker_mcp/', script_content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_setup_scripts.py:45*

### test_references_correct_mcp_directory

**Category**: instantiation  
**Description**: Instantiate findall: Test that script references src/skill_seekers/mcp/ (v2.4.0 MCP 2025 upgrade)  
**Expected**: assert len(new_refs) >= 2, f"Expected at least 2 references to 'skill_seekers.mcp' module, found {len(new_refs)}"  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: script_content

new_refs = re.findall('skill_seekers\\.mcp', script_content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_setup_scripts.py:57*

### test_requirements_txt_path

**Category**: instantiation  
**Description**: Instantiate findall: Test that script uses pip install -e . (v2.0.0 modern packaging)  
**Expected**: assert len(old_skill_seeker_refs) == 0, f"Should NOT reference 'skill_seeker_mcp/requirements.txt' (found {len(old_skill_seeker_refs)})"  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: script_content

old_skill_seeker_refs = re.findall('skill_seeker_mcp/requirements\\.txt', script_content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_setup_scripts.py:77*

### test_requirements_txt_path

**Category**: instantiation  
**Description**: Instantiate findall: Test that script uses pip install -e . (v2.0.0 modern packaging)  
**Expected**: assert len(old_skill_seeker_refs) == 0, f"Should NOT reference 'skill_seeker_mcp/requirements.txt' (found {len(old_skill_seeker_refs)})"  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: script_content

old_mcp_refs = re.findall('(?<!skill_seeker_)mcp/requirements\\.txt', script_content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_setup_scripts.py:78*

### test_auto_mode_with_api_key

**Category**: instantiation  
**Description**: Instantiate GuideEnhancer: Test auto mode detects API when key present and library available  
**Confidence**: 0.80  
**Tags**: mock  

```python
enhancer = GuideEnhancer(mode='auto')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_guide_enhancer.py:37*

### test_auto_mode_without_api_key

**Category**: instantiation  
**Description**: Instantiate GuideEnhancer: Test auto mode falls back to LOCAL when no API key  
**Confidence**: 0.80  
**Tags**: mock  

```python
enhancer = GuideEnhancer(mode='auto')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_guide_enhancer.py:47*

### test_explicit_api_mode

**Category**: instantiation  
**Description**: Instantiate GuideEnhancer: Test explicit API mode  
**Expected**: assert enhancer.mode in ['api', 'none']  
**Confidence**: 0.80  

```python
enhancer = GuideEnhancer(mode='api')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_guide_enhancer.py:52*

### test_explicit_local_mode

**Category**: instantiation  
**Description**: Instantiate GuideEnhancer: Test explicit LOCAL mode  
**Expected**: assert enhancer.mode in ['local', 'none']  
**Confidence**: 0.80  

```python
enhancer = GuideEnhancer(mode='local')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_guide_enhancer.py:57*

### test_explicit_none_mode

**Category**: instantiation  
**Description**: Instantiate GuideEnhancer: Test explicit none mode  
**Expected**: assert enhancer.mode == 'none'  
**Confidence**: 0.80  

```python
enhancer = GuideEnhancer(mode='none')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_guide_enhancer.py:62*

### test_claude_cli_check

**Category**: instantiation  
**Description**: Instantiate GuideEnhancer: Test Claude CLI availability check  
**Expected**: assert enhancer.mode in ['local', 'api', 'none']  
**Confidence**: 0.80  

```python
enhancer = GuideEnhancer(mode='local')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_guide_enhancer.py:67*

### test_enhance_step_descriptions_empty_list

**Category**: instantiation  
**Description**: Instantiate GuideEnhancer: Test with empty steps list  
**Expected**: assert result == []  
**Confidence**: 0.80  

```python
enhancer = GuideEnhancer(mode='none')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_guide_enhancer.py:77*

### test_enhance_step_descriptions_empty_list

**Category**: instantiation  
**Description**: Instantiate enhance_step_descriptions: Test with empty steps list  
**Expected**: assert result == []  
**Confidence**: 0.80  

```python
result = enhancer.enhance_step_descriptions(steps)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_guide_enhancer.py:79*

### test_enhance_step_descriptions_none_mode

**Category**: instantiation  
**Description**: Instantiate GuideEnhancer: Test step descriptions in none mode returns empty  
**Expected**: assert result == []  
**Confidence**: 0.80  

```python
enhancer = GuideEnhancer(mode='none')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_guide_enhancer.py:84*

### test_enhance_step_descriptions_none_mode

**Category**: instantiation  
**Description**: Instantiate enhance_step_descriptions: Test step descriptions in none mode returns empty  
**Expected**: assert result == []  
**Confidence**: 0.80  

```python
result = enhancer.enhance_step_descriptions(steps)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_guide_enhancer.py:91*

### test_detect_from_html_swift_class

**Category**: instantiation  
**Description**: Instantiate BeautifulSoup: Test HTML element with Swift CSS class  
**Expected**: assert lang == 'swift'  
**Confidence**: 0.80  

```python
soup = BeautifulSoup(html, 'html.parser')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_swift_detection.py:48*

### test_detect_from_html_swift_class

**Category**: instantiation  
**Description**: Instantiate find: Test HTML element with Swift CSS class  
**Expected**: assert lang == 'swift'  
**Confidence**: 0.80  

```python
elem = soup.find('code')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_swift_detection.py:49*

### test_detect_from_html_swift_class

**Category**: instantiation  
**Description**: Instantiate detect_from_html: Test HTML element with Swift CSS class  
**Expected**: assert lang == 'swift'  
**Confidence**: 0.80  

```python
lang, confidence = detector.detect_from_html(elem, 'let x = 5')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_swift_detection.py:51*

### test_func_with_return_type

**Category**: instantiation  
**Description**: Instantiate detect_from_code: Test Swift function with return type  
**Expected**: assert lang == 'swift'  
**Confidence**: 0.80  

```python
lang, confidence = detector.detect_from_code(code)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_swift_detection.py:67*

### test_struct_declaration

**Category**: instantiation  
**Description**: Instantiate detect_from_code: Test Swift struct declaration  
**Expected**: assert lang == 'swift'  
**Confidence**: 0.80  

```python
lang, confidence = detector.detect_from_code(code)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_swift_detection.py:80*

### test_protocol_declaration

**Category**: instantiation  
**Description**: Instantiate detect_from_code: Test Swift protocol declaration  
**Expected**: assert lang == 'swift'  
**Confidence**: 0.80  

```python
lang, confidence = detector.detect_from_code(code)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_swift_detection.py:93*

### test_extension_declaration

**Category**: instantiation  
**Description**: Instantiate detect_from_code: Test Swift extension  
**Expected**: assert lang == 'swift'  
**Confidence**: 0.80  

```python
lang, confidence = detector.detect_from_code(code)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_swift_detection.py:107*

### test_guard_let_unwrapping

**Category**: instantiation  
**Description**: Instantiate detect_from_code: Test Swift guard let optional unwrapping  
**Expected**: assert lang == 'swift'  
**Confidence**: 0.80  

```python
lang, confidence = detector.detect_from_code(code)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_swift_detection.py:122*

### test_successful_download

**Category**: instantiation  
**Description**: Instantiate LlmsTxtDownloader: Test successful download with valid markdown content  
**Expected**: assert content is not None  
**Confidence**: 0.80  
**Tags**: mock  

```python
downloader = LlmsTxtDownloader('https://example.com/llms.txt')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_llms_txt_downloader.py:10*

### test_timeout_with_retry

**Category**: instantiation  
**Description**: Instantiate LlmsTxtDownloader: Test timeout scenario with retry logic  
**Expected**: assert content is None  
**Confidence**: 0.80  
**Tags**: mock  

```python
downloader = LlmsTxtDownloader('https://example.com/llms.txt', max_retries=2)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_llms_txt_downloader.py:31*

### test_empty_content_rejection

**Category**: instantiation  
**Description**: Instantiate LlmsTxtDownloader: Test rejection of content shorter than 100 chars  
**Expected**: assert content is None  
**Confidence**: 0.80  
**Tags**: mock  

```python
downloader = LlmsTxtDownloader('https://example.com/llms.txt')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_llms_txt_downloader.py:46*

### test_non_markdown_rejection

**Category**: instantiation  
**Description**: Instantiate LlmsTxtDownloader: Test rejection of content that doesn't look like markdown  
**Expected**: assert content is None  
**Confidence**: 0.80  
**Tags**: mock  

```python
downloader = LlmsTxtDownloader('https://example.com/llms.txt')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_llms_txt_downloader.py:60*

### test_http_error_handling

**Category**: instantiation  
**Description**: Instantiate LlmsTxtDownloader: Test handling of HTTP errors (404, 500, etc.)  
**Expected**: assert content is None  
**Confidence**: 0.80  
**Tags**: mock  

```python
downloader = LlmsTxtDownloader('https://example.com/llms.txt', max_retries=2)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_llms_txt_downloader.py:74*

### test_http_error_handling

**Category**: instantiation  
**Description**: Instantiate HTTPError: Test handling of HTTP errors (404, 500, etc.)  
**Expected**: assert content is None  
**Confidence**: 0.80  
**Tags**: mock  

```python
mock_response.raise_for_status.side_effect = requests.HTTPError('404 Not Found')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_llms_txt_downloader.py:77*

### test_exponential_backoff

**Category**: instantiation  
**Description**: Instantiate LlmsTxtDownloader: Test that exponential backoff delays are correct  
**Expected**: assert content is None  
**Confidence**: 0.80  
**Tags**: mock  

```python
downloader = LlmsTxtDownloader('https://example.com/llms.txt', max_retries=3)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_llms_txt_downloader.py:91*

### test_markdown_validation

**Category**: instantiation  
**Description**: Instantiate LlmsTxtDownloader: Test markdown pattern detection  
**Expected**: assert downloader._is_markdown('# Header')  
**Confidence**: 0.80  

```python
downloader = LlmsTxtDownloader('https://example.com/llms.txt')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_llms_txt_downloader.py:108*

### test_custom_timeout

**Category**: instantiation  
**Description**: Instantiate LlmsTxtDownloader: Test custom timeout parameter  
**Expected**: assert content is not None  
**Confidence**: 0.80  
**Tags**: mock  

```python
downloader = LlmsTxtDownloader('https://example.com/llms.txt', timeout=10)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_llms_txt_downloader.py:124*

### test_router_generator_init

**Category**: instantiation  
**Description**: Instantiate RouterGenerator: Test router generator initialization.  
**Expected**: assert generator.router_name == 'test'  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

generator = RouterGenerator([str(config_path1), str(config_path2)])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_generate_router_github.py:45*

### test_infer_router_name

**Category**: instantiation  
**Description**: Instantiate RouterGenerator: Test router name inference from sub-skill names.  
**Expected**: assert generator.router_name == 'fastmcp'  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

generator = RouterGenerator([str(config_path1), str(config_path2)])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_generate_router_github.py:64*

### test_extract_routing_keywords_basic

**Category**: instantiation  
**Description**: Instantiate RouterGenerator: Test basic keyword extraction without GitHub.  
**Expected**: assert 'test-oauth' in routing  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

generator = RouterGenerator([str(config_path)])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_generate_router_github.py:80*

### test_router_with_github_metadata

**Category**: instantiation  
**Description**: Instantiate CodeStream: Test router generator with GitHub metadata.  
**Expected**: assert generator.github_metadata is not None  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

code_stream = CodeStream(directory=tmp_path, files=[])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_generate_router_github.py:107*

### test_router_with_github_metadata

**Category**: instantiation  
**Description**: Instantiate DocsStream: Test router generator with GitHub metadata.  
**Expected**: assert generator.github_metadata is not None  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

docs_stream = DocsStream(readme='# Test Project\n\nA test OAuth library.', contributing=None, docs_files=[])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_generate_router_github.py:108*

### test_router_with_github_metadata

**Category**: instantiation  
**Description**: Instantiate InsightsStream: Test router generator with GitHub metadata.  
**Expected**: assert generator.github_metadata is not None  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

insights_stream = InsightsStream(metadata={'stars': 1234, 'forks': 56, 'language': 'Python', 'description': 'OAuth helper'}, common_problems=[{'title': 'OAuth fails on redirect', 'number': 42, 'state': 'open', 'comments': 15, 'labels': ['bug', 'oauth']}], known_solutions=[], top_labels=[{'label': 'oauth', 'count': 20}, {'label': 'bug', 'count': 10}])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_generate_router_github.py:111*

### test_router_with_github_metadata

**Category**: instantiation  
**Description**: Instantiate ThreeStreamData: Test router generator with GitHub metadata.  
**Expected**: assert generator.github_metadata is not None  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

github_streams = ThreeStreamData(code_stream, docs_stream, insights_stream)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_generate_router_github.py:130*

### test_router_with_github_metadata

**Category**: instantiation  
**Description**: Instantiate RouterGenerator: Test router generator with GitHub metadata.  
**Expected**: assert generator.github_metadata is not None  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

generator = RouterGenerator([str(config_path)], github_streams=github_streams)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_generate_router_github.py:133*

### test_extract_keywords_with_github_labels

**Category**: instantiation  
**Description**: Instantiate CodeStream: Test keyword extraction with GitHub issue labels (2x weight).  
**Expected**: assert oauth_count >= 4  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

code_stream = CodeStream(directory=tmp_path, files=[])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_generate_router_github.py:154*

### test_extract_keywords_with_github_labels

**Category**: instantiation  
**Description**: Instantiate DocsStream: Test keyword extraction with GitHub issue labels (2x weight).  
**Expected**: assert oauth_count >= 4  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

docs_stream = DocsStream(readme=None, contributing=None, docs_files=[])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_generate_router_github.py:155*

### test_cli_validation_error_no_config

**Category**: instantiation  
**Description**: Instantiate run: E2E test: CLI validation error (no config provided)  
**Expected**: assert result.returncode != 0  
**Confidence**: 0.80  

```python
result = subprocess.run([sys.executable, '-m', 'skill_seekers.cli.install_skill'], capture_output=True, text=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_install_skill_e2e.py:355*

### test_cli_help

**Category**: instantiation  
**Description**: Instantiate run: E2E test: CLI help command  
**Expected**: assert result.returncode == 0  
**Confidence**: 0.80  

```python
result = subprocess.run([sys.executable, '-m', 'skill_seekers.cli.install_skill', '--help'], capture_output=True, text=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_install_skill_e2e.py:370*

### test_cli_via_unified_command

**Category**: instantiation  
**Description**: Instantiate run: E2E test: Using 'skill-seekers install' unified CLI

Note: Skipped because subprocess execution has asyncio.run() issues.
The functionality is already tested in test_cli_full_workflow_mocked
via direct function calls.  
**Expected**: assert result.returncode == 0 or 'DRY RUN' in result.stdout, f'Unified CLI failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}'  
**Confidence**: 0.80  
**Tags**: pytest, mock, async  

```python
# Setup
# Fixtures: test_config_file

result = subprocess.run(['skill-seekers', 'install', '--config', test_config_file, '--dry-run'], capture_output=True, text=True, timeout=30)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_install_skill_e2e.py:438*

### real_test_config

**Category**: instantiation  
**Description**: Instantiate Path: Create a real minimal config that can be scraped  
**Confidence**: 0.80  
**Tags**: pytest  

```python
# Setup
# Fixtures: tmp_path

test_config_path = Path('configs/test-manual.json')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_install_skill_e2e.py:459*

### test_init_creates_config_dir

**Category**: instantiation  
**Description**: Instantiate SourceManager: Test that initialization creates config directory.  
**Expected**: assert config_dir.exists()  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

manager = SourceManager(config_dir=str(config_dir))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_source_manager.py:34*

### test_init_creates_registry_file

**Category**: instantiation  
**Description**: Instantiate SourceManager: Test that initialization creates registry file.  
**Expected**: assert registry_file.exists()  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: temp_config_dir

_manager = SourceManager(config_dir=str(temp_config_dir))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_source_manager.py:41*

### test_init_preserves_existing_registry

**Category**: instantiation  
**Description**: Instantiate SourceManager: Test that initialization doesn't overwrite existing registry.  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: temp_config_dir

_manager = SourceManager(config_dir=str(temp_config_dir))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_source_manager.py:64*

### test_add_source_minimal

**Category**: instantiation  
**Description**: Instantiate add_source: Test adding source with minimal parameters.  
**Expected**: assert source['name'] == 'team'  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: source_manager

source = source_manager.add_source(name='team', git_url='https://github.com/myorg/configs.git')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_source_manager.py:84*

### test_add_source_full_parameters

**Category**: instantiation  
**Description**: Instantiate add_source: Test adding source with all parameters.  
**Expected**: assert source['name'] == 'company'  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: source_manager

source = source_manager.add_source(name='company', git_url='https://gitlab.company.com/platform/configs.git', source_type='gitlab', token_env='CUSTOM_TOKEN', branch='develop', priority=1, enabled=False)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_source_manager.py:100*

### test_add_source_normalizes_name

**Category**: instantiation  
**Description**: Instantiate add_source: Test that source names are normalized to lowercase.  
**Expected**: assert source['name'] == 'myteam'  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: source_manager

source = source_manager.add_source(name='MyTeam', git_url='https://github.com/org/repo.git')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_source_manager.py:119*

### test_add_source_valid_name_with_hyphens

**Category**: instantiation  
**Description**: Instantiate add_source: Test that source names with hyphens are allowed.  
**Expected**: assert source['name'] == 'team-alpha'  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: source_manager

source = source_manager.add_source(name='team-alpha', git_url='https://github.com/org/repo.git')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_source_manager.py:137*

### test_add_source_valid_name_with_underscores

**Category**: instantiation  
**Description**: Instantiate add_source: Test that source names with underscores are allowed.  
**Expected**: assert source['name'] == 'team_alpha'  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: source_manager

source = source_manager.add_source(name='team_alpha', git_url='https://github.com/org/repo.git')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_source_manager.py:145*

### test_add_source_strips_git_url

**Category**: instantiation  
**Description**: Instantiate add_source: Test that git URLs are stripped of whitespace.  
**Expected**: assert source['git_url'] == 'https://github.com/org/repo.git'  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: source_manager

source = source_manager.add_source(name='team', git_url='  https://github.com/org/repo.git  ')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_source_manager.py:158*

### test_default_skip_llms_txt_is_false

**Category**: instantiation  
**Description**: Instantiate DocToSkillConverter: Test that skip_llms_txt defaults to False when not specified.  
**Expected**: self.assertFalse(converter.skip_llms_txt)  
**Confidence**: 0.80  
**Tags**: unittest  

```python
converter = DocToSkillConverter(config, dry_run=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_skip_llms_txt.py:29*

### test_skip_llms_txt_can_be_set_true

**Category**: instantiation  
**Description**: Instantiate DocToSkillConverter: Test that skip_llms_txt can be explicitly set to True.  
**Expected**: self.assertTrue(converter.skip_llms_txt)  
**Confidence**: 0.80  
**Tags**: unittest  

```python
converter = DocToSkillConverter(config, dry_run=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_skip_llms_txt.py:41*

### test_skip_llms_txt_can_be_set_false

**Category**: instantiation  
**Description**: Instantiate DocToSkillConverter: Test that skip_llms_txt can be explicitly set to False.  
**Expected**: self.assertFalse(converter.skip_llms_txt)  
**Confidence**: 0.80  
**Tags**: unittest  

```python
converter = DocToSkillConverter(config, dry_run=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_skip_llms_txt.py:53*

### test_llms_txt_tried_when_not_skipped

**Category**: instantiation  
**Description**: Instantiate DocToSkillConverter: Test that _try_llms_txt is called when skip_llms_txt is False.  
**Confidence**: 0.80  
**Tags**: unittest, mock  

```python
converter = DocToSkillConverter(config, dry_run=False)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_skip_llms_txt.py:73*

### test_llms_txt_skipped_when_skip_true

**Category**: instantiation  
**Description**: Instantiate DocToSkillConverter: Test that _try_llms_txt is NOT called when skip_llms_txt is True.  
**Confidence**: 0.80  
**Tags**: unittest, mock  

```python
converter = DocToSkillConverter(config, dry_run=False)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_skip_llms_txt.py:98*

### test_llms_txt_skipped_in_dry_run_mode

**Category**: instantiation  
**Description**: Instantiate DocToSkillConverter: Test that _try_llms_txt is NOT called in dry-run mode regardless of skip setting.  
**Confidence**: 0.80  
**Tags**: unittest, mock  

```python
converter = DocToSkillConverter(config, dry_run=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_skip_llms_txt.py:123*

### test_checker_detects_missing_skill_md

**Category**: instantiation  
**Description**: Instantiate SkillQualityChecker: Test that checker detects missing SKILL.md  
**Confidence**: 0.80  
**Tags**: unittest  

```python
checker = SkillQualityChecker(skill_dir)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_quality_checker.py:42*

### test_checker_detects_missing_references

**Category**: instantiation  
**Description**: Instantiate create_test_skill: Test that checker warns about missing references  
**Confidence**: 0.80  
**Tags**: unittest  

```python
skill_dir = self.create_test_skill(tmpdir, skill_md, create_references=False)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_quality_checker.py:60*

### test_checker_detects_missing_references

**Category**: instantiation  
**Description**: Instantiate SkillQualityChecker: Test that checker warns about missing references  
**Confidence**: 0.80  
**Tags**: unittest  

```python
checker = SkillQualityChecker(skill_dir)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_quality_checker.py:62*

### test_checker_detects_invalid_frontmatter

**Category**: instantiation  
**Description**: Instantiate create_test_skill: Test that checker detects invalid YAML frontmatter  
**Confidence**: 0.80  
**Tags**: unittest  

```python
skill_dir = self.create_test_skill(tmpdir, skill_md)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_quality_checker.py:76*

### test_checker_detects_invalid_frontmatter

**Category**: instantiation  
**Description**: Instantiate SkillQualityChecker: Test that checker detects invalid YAML frontmatter  
**Confidence**: 0.80  
**Tags**: unittest  

```python
checker = SkillQualityChecker(skill_dir)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_quality_checker.py:78*

### test_checker_detects_missing_name_field

**Category**: instantiation  
**Description**: Instantiate create_test_skill: Test that checker detects missing name field in frontmatter  
**Confidence**: 0.80  
**Tags**: unittest  

```python
skill_dir = self.create_test_skill(tmpdir, skill_md)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_quality_checker.py:94*

### test_checker_detects_missing_name_field

**Category**: instantiation  
**Description**: Instantiate SkillQualityChecker: Test that checker detects missing name field in frontmatter  
**Confidence**: 0.80  
**Tags**: unittest  

```python
checker = SkillQualityChecker(skill_dir)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_quality_checker.py:96*

### test_checker_detects_code_without_language

**Category**: instantiation  
**Description**: Instantiate create_test_skill: Test that checker warns about code blocks without language tags  
**Confidence**: 0.80  
**Tags**: unittest  

```python
skill_dir = self.create_test_skill(tmpdir, skill_md)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_quality_checker.py:118*

### test_checker_detects_code_without_language

**Category**: instantiation  
**Description**: Instantiate SkillQualityChecker: Test that checker warns about code blocks without language tags  
**Confidence**: 0.80  
**Tags**: unittest  

```python
checker = SkillQualityChecker(skill_dir)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_quality_checker.py:120*

### test_checker_approves_good_skill

**Category**: instantiation  
**Description**: Instantiate create_test_skill: Test that checker gives high score to well-formed skill  
**Confidence**: 0.80  
**Tags**: unittest  

```python
skill_dir = self.create_test_skill(tmpdir, skill_md)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_quality_checker.py:164*

### test_init_with_custom_cache_dir

**Category**: instantiation  
**Description**: Instantiate GitConfigRepo: Test initialization with custom cache directory.  
**Expected**: assert repo.cache_dir == temp_cache_dir  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: temp_cache_dir

repo = GitConfigRepo(cache_dir=str(temp_cache_dir))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_git_repo.py:35*

### test_inject_token_https

**Category**: instantiation  
**Description**: Instantiate inject_token: Test token injection into HTTPS URL.  
**Expected**: assert result == 'https://ghp_testtoken123@github.com/org/repo.git'  
**Confidence**: 0.80  

```python
result = GitConfigRepo.inject_token(url, token)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_git_repo.py:101*

### test_inject_token_ssh_to_https

**Category**: instantiation  
**Description**: Instantiate inject_token: Test SSH URL conversion to HTTPS with token.  
**Expected**: assert result == 'https://ghp_testtoken123@github.com/org/repo.git'  
**Confidence**: 0.80  

```python
result = GitConfigRepo.inject_token(url, token)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_git_repo.py:109*

### test_inject_token_with_port

**Category**: instantiation  
**Description**: Instantiate inject_token: Test token injection with custom port.  
**Expected**: assert result == 'https://token123@gitlab.example.com:8443/org/repo.git'  
**Confidence**: 0.80  

```python
result = GitConfigRepo.inject_token(url, token)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_git_repo.py:117*

### test_inject_token_gitlab_ssh

**Category**: instantiation  
**Description**: Instantiate inject_token: Test GitLab SSH URL conversion.  
**Expected**: assert result == 'https://glpat-token123@gitlab.com/group/project.git'  
**Confidence**: 0.80  

```python
result = GitConfigRepo.inject_token(url, token)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_git_repo.py:125*

### test_clone_new_repo

**Category**: instantiation  
**Description**: Instantiate clone_or_pull: Test cloning a new repository.  
**Expected**: assert result == git_repo.cache_dir / 'test-source'  
**Confidence**: 0.80  
**Tags**: mock  

```python
# Setup
# Fixtures: mock_clone, git_repo

result = git_repo.clone_or_pull(source_name='test-source', git_url='https://github.com/org/repo.git')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_git_repo.py:137*

### test_pull_existing_repo

**Category**: instantiation  
**Description**: Instantiate clone_or_pull: Test pulling updates to existing repository.  
**Expected**: assert result == repo_path  
**Confidence**: 0.80  
**Tags**: mock  

```python
# Setup
# Fixtures: mock_repo_class, git_repo, temp_cache_dir

result = git_repo.clone_or_pull(source_name='test-source', git_url='https://github.com/org/repo.git')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_git_repo.py:164*

### test_pull_with_token_update

**Category**: instantiation  
**Description**: Instantiate clone_or_pull: Test pulling with token updates remote URL.  
**Expected**: mock_origin.set_url.assert_called_once()  
**Confidence**: 0.80  
**Tags**: mock  

```python
# Setup
# Fixtures: mock_repo_class, git_repo, temp_cache_dir

_result = git_repo.clone_or_pull(source_name='test-source', git_url='https://github.com/org/repo.git', token='ghp_token123')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_git_repo.py:185*

### test_clone_auth_failure_error

**Category**: instantiation  
**Description**: Instantiate GitCommandError: Test authentication failure error handling.  
**Confidence**: 0.80  
**Tags**: mock  

```python
# Setup
# Fixtures: mock_clone, git_repo

mock_clone.side_effect = GitCommandError('clone', 128, stderr='fatal: Authentication failed')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_git_repo.py:234*

### test_bootstrap_script_runs

**Category**: instantiation  
**Description**: Instantiate run: Test that bootstrap script runs successfully.

Note: This test is slow as it runs full codebase analysis.
Run with: pytest -m slow  
**Expected**: assert result.returncode == 0, f'Script failed: {result.stderr}'  
**Confidence**: 0.80  
**Tags**: pytest  

```python
# Setup
# Fixtures: project_root

result = subprocess.run(['bash', str(script)], cwd=project_root, capture_output=True, text=True, timeout=600)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_bootstrap_skill.py:63*

### test_single_worker_default

**Category**: instantiation  
**Description**: Instantiate DocToSkillConverter: Test default is single-worker mode  
**Confidence**: 0.80  
**Tags**: unittest  

```python
# Setup
'Save original working directory'
self.original_cwd = os.getcwd()

converter = DocToSkillConverter(config, dry_run=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_parallel_scraping.py:35*

### test_multiple_workers_creates_lock

**Category**: instantiation  
**Description**: Instantiate DocToSkillConverter: Test multiple workers creates thread lock  
**Confidence**: 0.80  
**Tags**: unittest  

```python
# Setup
'Save original working directory'
self.original_cwd = os.getcwd()

converter = DocToSkillConverter(config, dry_run=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_parallel_scraping.py:51*

### test_workers_from_config

**Category**: instantiation  
**Description**: Instantiate DocToSkillConverter: Test workers parameter is read from config  
**Confidence**: 0.80  
**Tags**: unittest  

```python
# Setup
'Save original working directory'
self.original_cwd = os.getcwd()

converter = DocToSkillConverter(config, dry_run=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_parallel_scraping.py:66*

### test_unlimited_with_none

**Category**: instantiation  
**Description**: Instantiate DocToSkillConverter: Test max_pages: None enables unlimited mode  
**Confidence**: 0.80  
**Tags**: unittest  

```python
# Setup
'Save original working directory'
self.original_cwd = os.getcwd()

converter = DocToSkillConverter(config, dry_run=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_parallel_scraping.py:92*

### test_unlimited_with_minus_one

**Category**: instantiation  
**Description**: Instantiate DocToSkillConverter: Test max_pages: -1 enables unlimited mode  
**Confidence**: 0.80  
**Tags**: unittest  

```python
# Setup
'Save original working directory'
self.original_cwd = os.getcwd()

converter = DocToSkillConverter(config, dry_run=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_parallel_scraping.py:106*

### test_limited_mode_default

**Category**: instantiation  
**Description**: Instantiate DocToSkillConverter: Test default max_pages is limited  
**Confidence**: 0.80  
**Tags**: unittest  

```python
# Setup
'Save original working directory'
self.original_cwd = os.getcwd()

converter = DocToSkillConverter(config, dry_run=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_parallel_scraping.py:119*

### test_limited_mode_default

**Category**: instantiation  
**Description**: Instantiate get: Test default max_pages is limited  
**Confidence**: 0.80  
**Tags**: unittest  

```python
# Setup
'Save original working directory'
self.original_cwd = os.getcwd()

max_pages = converter.config.get('max_pages', 500)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_parallel_scraping.py:120*

### test_rate_limit_from_config

**Category**: instantiation  
**Description**: Instantiate DocToSkillConverter: Test rate_limit is read from config  
**Confidence**: 0.80  
**Tags**: unittest  

```python
# Setup
'Save original working directory'
self.original_cwd = os.getcwd()

converter = DocToSkillConverter(config, dry_run=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_parallel_scraping.py:147*

### test_rate_limit_default

**Category**: instantiation  
**Description**: Instantiate DocToSkillConverter: Test default rate_limit is 0.5  
**Confidence**: 0.80  
**Tags**: unittest  

```python
# Setup
'Save original working directory'
self.original_cwd = os.getcwd()

converter = DocToSkillConverter(config, dry_run=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_parallel_scraping.py:160*

### test_zero_rate_limit_disables

**Category**: instantiation  
**Description**: Instantiate DocToSkillConverter: Test rate_limit: 0 disables rate limiting  
**Confidence**: 0.80  
**Tags**: unittest  

```python
# Setup
'Save original working directory'
self.original_cwd = os.getcwd()

converter = DocToSkillConverter(config, dry_run=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_parallel_scraping.py:174*

### test_valid_minimal_config

**Category**: instantiation  
**Description**: Instantiate validate_config: Test valid minimal configuration  
**Expected**: self.assertIsInstance(errors, list)  
**Confidence**: 0.80  
**Tags**: unittest  

```python
errors, _ = validate_config(config)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_config_validation.py:23*

### test_valid_complete_config

**Category**: instantiation  
**Description**: Instantiate validate_config: Test valid complete configuration  
**Expected**: self.assertEqual(len(errors), 0, f'Valid config should have no errors, got: {errors}')  
**Confidence**: 0.80  
**Tags**: unittest  

```python
errors, _ = validate_config(config)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_config_validation.py:43*

### test_missing_name

**Category**: instantiation  
**Description**: Instantiate validate_config: Test missing required field 'name'  
**Expected**: self.assertTrue(any(('name' in error.lower() for error in errors)))  
**Confidence**: 0.80  
**Tags**: unittest  

```python
errors, _ = validate_config(config)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_config_validation.py:49*

### test_missing_base_url

**Category**: instantiation  
**Description**: Instantiate validate_config: Test missing required field 'base_url'  
**Expected**: self.assertTrue(any(('base_url' in error.lower() for error in errors)))  
**Confidence**: 0.80  
**Tags**: unittest  

```python
errors, _ = validate_config(config)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_config_validation.py:55*

### test_scraped_data_uses_list_structure

**Category**: instantiation  
**Description**: Instantiate UnifiedScraper: Test that scraped_data uses list for each source type.  
**Confidence**: 0.80  
**Tags**: unittest  

```python
scraper = UnifiedScraper(config)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_multi_source.py:35*

### test_source_counters_initialized_to_zero

**Category**: instantiation  
**Description**: Instantiate UnifiedScraper: Test that source counters start at zero.  
**Confidence**: 0.80  
**Tags**: unittest  

```python
scraper = UnifiedScraper(config)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_multi_source.py:57*

### test_empty_lists_initially

**Category**: instantiation  
**Description**: Instantiate UnifiedScraper: Test that source lists are empty initially.  
**Confidence**: 0.80  
**Tags**: unittest  

```python
scraper = UnifiedScraper(config)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_multi_source.py:79*

### test_creates_subdirectory_per_source

**Category**: instantiation  
**Description**: Instantiate join: Test that each doc source gets its own subdirectory.  
**Expected**: self.assertTrue(os.path.exists(os.path.join(docs_dir, 'source_a')))  
**Confidence**: 0.80  
**Tags**: unittest  

```python
# Setup
'Set up test fixtures.'
self.temp_dir = tempfile.mkdtemp()
self.original_dir = os.getcwd()
os.chdir(self.temp_dir)

refs_dir1 = os.path.join(self.temp_dir, 'refs1')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_multi_source.py:108*

### test_async_mode_default_false

**Category**: instantiation  
**Description**: Instantiate DocToSkillConverter: Test async mode is disabled by default  
**Confidence**: 0.80  
**Tags**: unittest  

```python
# Setup
'Save original working directory'
self.original_cwd = os.getcwd()

converter = DocToSkillConverter(config, dry_run=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_async_scraping.py:39*

### test_async_mode_enabled_from_config

**Category**: instantiation  
**Description**: Instantiate DocToSkillConverter: Test async mode can be enabled via config  
**Confidence**: 0.80  
**Tags**: unittest  

```python
# Setup
'Save original working directory'
self.original_cwd = os.getcwd()

converter = DocToSkillConverter(config, dry_run=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_async_scraping.py:57*

### test_async_mode_with_workers

**Category**: instantiation  
**Description**: Instantiate DocToSkillConverter: Test async mode works with multiple workers  
**Confidence**: 0.80  
**Tags**: unittest  

```python
# Setup
'Save original working directory'
self.original_cwd = os.getcwd()

converter = DocToSkillConverter(config, dry_run=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_async_scraping.py:75*

### test_scrape_page_async_exists

**Category**: instantiation  
**Description**: Instantiate DocToSkillConverter: Test scrape_page_async method exists  
**Confidence**: 0.80  
**Tags**: unittest  

```python
# Setup
'Set up test fixtures'
self.original_cwd = os.getcwd()

converter = DocToSkillConverter(config, dry_run=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_async_scraping.py:104*

### test_scrape_all_async_exists

**Category**: instantiation  
**Description**: Instantiate DocToSkillConverter: Test scrape_all_async method exists  
**Confidence**: 0.80  
**Tags**: unittest  

```python
# Setup
'Set up test fixtures'
self.original_cwd = os.getcwd()

converter = DocToSkillConverter(config, dry_run=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_async_scraping.py:121*

### test_scrape_all_routes_to_async_when_enabled

**Category**: instantiation  
**Description**: Instantiate DocToSkillConverter: Test scrape_all calls async version when async_mode=True  
**Confidence**: 0.80  
**Tags**: unittest, mock  

```python
# Setup
'Set up test fixtures'
self.original_cwd = os.getcwd()

converter = DocToSkillConverter(config, dry_run=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_async_scraping.py:152*

### test_scrape_all_uses_sync_when_async_disabled

**Category**: instantiation  
**Description**: Instantiate DocToSkillConverter: Test scrape_all uses sync version when async_mode=False  
**Confidence**: 0.80  
**Tags**: unittest, mock  

```python
# Setup
'Set up test fixtures'
self.original_cwd = os.getcwd()

converter = DocToSkillConverter(config, dry_run=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_async_scraping.py:177*

### test_async_dry_run_completes

**Category**: instantiation  
**Description**: Instantiate DocToSkillConverter: Test async dry run completes without errors  
**Confidence**: 0.80  
**Tags**: unittest, mock  

```python
# Setup
'Set up test fixtures'
self.original_cwd = os.getcwd()

converter = DocToSkillConverter(config, dry_run=True)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_async_scraping.py:217*

### test_async_handles_http_errors

**Category**: instantiation  
**Description**: Instantiate DocToSkillConverter: Test async scraping handles HTTP errors gracefully  
**Confidence**: 0.80  
**Tags**: unittest, mock  

```python
# Setup
'Set up test fixtures'
self.original_cwd = os.getcwd()

converter = DocToSkillConverter(config, dry_run=False)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_async_scraping.py:254*

### test_async_handles_http_errors

**Category**: instantiation  
**Description**: Instantiate Semaphore: Test async scraping handles HTTP errors gracefully  
**Confidence**: 0.80  
**Tags**: unittest, mock  

```python
# Setup
'Set up test fixtures'
self.original_cwd = os.getcwd()

semaphore = asyncio.Semaphore(2)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_async_scraping.py:260*

### test_cli_accepts_target_flag

**Category**: instantiation  
**Description**: Instantiate parse_args: Test that CLI accepts --target flag  
**Confidence**: 0.80  
**Tags**: unittest  

```python
args = parser.parse_args(['--config', 'test'])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_install_multiplatform.py:36*

### test_cli_accepts_target_flag

**Category**: instantiation  
**Description**: Instantiate parse_args: Test that CLI accepts --target flag  
**Confidence**: 0.80  
**Tags**: unittest  

```python
args = parser.parse_args(['--config', 'test', '--target', platform])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_install_multiplatform.py:32*

### test_cli_accepts_target_flag

**Category**: instantiation  
**Description**: Instantiate parse_args: Test that CLI accepts --target flag  
**Confidence**: 0.80  
**Tags**: unittest  

```python
args = parser.parse_args(['--config', 'test'])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_install_multiplatform.py:36*

### test_cli_accepts_target_flag

**Category**: instantiation  
**Description**: Instantiate parse_args: Test that CLI accepts --target flag  
**Confidence**: 0.80  
**Tags**: unittest  

```python
args = parser.parse_args(['--config', 'test', '--target', platform])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_install_multiplatform.py:32*

### test_validate_existing_unified_configs

**Category**: instantiation  
**Description**: Instantiate validate_config: Test that all existing unified configs are valid  
**Confidence**: 0.80  

```python
validator = validate_config(str(config_path))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\src\skill_seekers\cli\test_unified_simple.py:35*

### test_backward_compatibility

**Category**: instantiation  
**Description**: Instantiate validate_config: Test that legacy configs still work  
**Confidence**: 0.80  

```python
validator = validate_config(str(config_path))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\src\skill_seekers\cli\test_unified_simple.py:52*

### test_create_temp_unified_config

**Category**: instantiation  
**Description**: Instantiate validate_config: Test creating a unified config from scratch  
**Confidence**: 0.80  

```python
validator = validate_config(config_path)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\src\skill_seekers\cli\test_unified_simple.py:85*

### test_mixed_source_types

**Category**: instantiation  
**Description**: Instantiate validate_config: Test config with documentation, GitHub, and PDF sources  
**Confidence**: 0.80  

```python
validator = validate_config(config_path)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\src\skill_seekers\cli\test_unified_simple.py:114*

### test_config_validation_errors

**Category**: instantiation  
**Description**: Instantiate validate_config: Test that invalid configs are rejected  
**Confidence**: 0.80  

```python
_validator = validate_config(config_path)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\src\skill_seekers\cli\test_unified_simple.py:145*

### test_detect_llms_txt_variants

**Category**: instantiation  
**Description**: Instantiate LlmsTxtDetector: Test detection of llms.txt file variants  
**Confidence**: 0.80  
**Tags**: mock  

```python
detector = LlmsTxtDetector('https://hono.dev/docs')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_llms_txt_detector.py:8*

### test_detect_no_llms_txt

**Category**: instantiation  
**Description**: Instantiate LlmsTxtDetector: Test detection when no llms.txt file exists  
**Confidence**: 0.80  
**Tags**: mock  

```python
detector = LlmsTxtDetector('https://example.com/docs')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_llms_txt_detector.py:25*

### test_url_parsing_with_complex_paths

**Category**: instantiation  
**Description**: Instantiate LlmsTxtDetector: Test URL parsing handles non-standard paths correctly  
**Confidence**: 0.80  
**Tags**: mock  

```python
detector = LlmsTxtDetector('https://example.com/docs/v2/guide')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_llms_txt_detector.py:40*

### test_detect_all_variants

**Category**: instantiation  
**Description**: Instantiate LlmsTxtDetector: Test detecting all llms.txt variants  
**Confidence**: 0.80  
**Tags**: mock  

```python
detector = LlmsTxtDetector('https://hono.dev/docs')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_llms_txt_detector.py:58*

### test_detect_unified_format

**Category**: instantiation  
**Description**: Instantiate ConfigValidator: Test unified format detection  
**Confidence**: 0.80  

```python
validator = ConfigValidator(config_path)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_unified.py:48*

### test_detect_unified_format

**Category**: instantiation  
**Description**: Instantiate ConfigValidator: Test unified format detection  
**Confidence**: 0.80  

```python
validator = ConfigValidator(config_path)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_unified.py:59*

### test_validate_unified_sources

**Category**: instantiation  
**Description**: Instantiate ConfigValidator: Test source type validation  
**Expected**: assert len(validator.config['sources']) == 3  
**Confidence**: 0.80  

```python
validator = ConfigValidator(config)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_unified.py:77*

### test_validate_invalid_source_type

**Category**: instantiation  
**Description**: Instantiate ConfigValidator: Test invalid source type raises error  
**Confidence**: 0.80  

```python
validator = ConfigValidator(config)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_unified.py:90*

### test_needs_api_merge

**Category**: instantiation  
**Description**: Instantiate ConfigValidator: Test API merge detection  
**Expected**: assert validator.needs_api_merge()  
**Confidence**: 0.80  

```python
validator = ConfigValidator(config_needs_merge)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_unified.py:107*

### test_needs_api_merge

**Category**: instantiation  
**Description**: Instantiate ConfigValidator: Test API merge detection  
**Expected**: assert not validator.needs_api_merge()  
**Confidence**: 0.80  

```python
validator = ConfigValidator(config_no_merge)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_unified.py:117*

### test_backward_compatibility

**Category**: instantiation  
**Description**: Instantiate ConfigValidator: Test legacy config conversion  
**Expected**: assert 'sources' in unified  
**Confidence**: 0.80  

```python
validator = ConfigValidator(legacy_config)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_unified.py:131*

### test_detect_from_html_with_css_class

**Category**: instantiation  
**Description**: Instantiate BeautifulSoup: Test HTML element with CSS class  
**Expected**: assert lang == 'python'  
**Confidence**: 0.80  

```python
soup = BeautifulSoup(html, 'html.parser')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_language_detector.py:83*

### test_detect_from_html_with_css_class

**Category**: instantiation  
**Description**: Instantiate find: Test HTML element with CSS class  
**Expected**: assert lang == 'python'  
**Confidence**: 0.80  

```python
elem = soup.find('code')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_language_detector.py:84*

### test_detect_from_html_with_css_class

**Category**: instantiation  
**Description**: Instantiate detect_from_html: Test HTML element with CSS class  
**Expected**: assert lang == 'python'  
**Confidence**: 0.80  

```python
lang, confidence = detector.detect_from_html(elem, 'print("hello")')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_language_detector.py:86*

### test_detect_from_html_with_parent_class

**Category**: instantiation  
**Description**: Instantiate BeautifulSoup: Test parent <pre> element with CSS class  
**Expected**: assert lang == 'java'  
**Confidence**: 0.80  

```python
soup = BeautifulSoup(html, 'html.parser')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_language_detector.py:96*

### test_detect_from_html_with_parent_class

**Category**: instantiation  
**Description**: Instantiate find: Test parent <pre> element with CSS class  
**Expected**: assert lang == 'java'  
**Confidence**: 0.80  

```python
elem = soup.find('code')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_language_detector.py:97*

### test_detect_from_html_with_parent_class

**Category**: instantiation  
**Description**: Instantiate detect_from_html: Test parent <pre> element with CSS class  
**Expected**: assert lang == 'java'  
**Confidence**: 0.80  

```python
lang, confidence = detector.detect_from_html(elem, 'System.out.println("hello");')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_language_detector.py:99*

### test_unity_monobehaviour_detection

**Category**: instantiation  
**Description**: Instantiate detect_from_code: Test Unity MonoBehaviour class detection  
**Expected**: assert lang == 'csharp'  
**Confidence**: 0.80  

```python
lang, confidence = detector.detect_from_code(code)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_language_detector.py:124*

### test_unity_lifecycle_methods

**Category**: instantiation  
**Description**: Instantiate detect_from_code: Test Unity lifecycle method detection  
**Expected**: assert lang == 'csharp'  
**Confidence**: 0.80  

```python
lang, confidence = detector.detect_from_code(code)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_language_detector.py:140*

### test_unity_coroutine_detection

**Category**: instantiation  
**Description**: Instantiate detect_from_code: Test Unity coroutine detection  
**Expected**: assert lang == 'csharp'  
**Confidence**: 0.80  

```python
lang, confidence = detector.detect_from_code(code)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_language_detector.py:155*

### test_parse_markdown_sections

**Category**: instantiation  
**Description**: Instantiate LlmsTxtParser: Test parsing markdown into page sections  
**Expected**: assert len(pages) >= 2  
**Confidence**: 0.80  

```python
parser = LlmsTxtParser(sample_content)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_llms_txt_parser.py:27*

### test_upload_without_api_key

**Category**: instantiation  
**Description**: Instantiate create_test_zip: Test that upload fails gracefully without API key  
**Confidence**: 0.80  
**Tags**: unittest  

```python
# Setup
'Store original API key state'
self.original_api_key = os.environ.get('ANTHROPIC_API_KEY')

zip_path = self.create_test_zip(tmpdir)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_upload_skill.py:46*

### test_upload_without_api_key

**Category**: instantiation  
**Description**: Instantiate upload_skill_api: Test that upload fails gracefully without API key  
**Confidence**: 0.80  
**Tags**: unittest  

```python
# Setup
'Store original API key state'
self.original_api_key = os.environ.get('ANTHROPIC_API_KEY')

success, message = upload_skill_api(zip_path)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_upload_skill.py:48*

### test_upload_with_nonexistent_file

**Category**: instantiation  
**Description**: Instantiate upload_skill_api: Test upload with nonexistent file  
**Expected**: self.assertFalse(success)  
**Confidence**: 0.80  
**Tags**: unittest  

```python
# Setup
'Store original API key state'
self.original_api_key = os.environ.get('ANTHROPIC_API_KEY')

success, message = upload_skill_api('/nonexistent/file.zip')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_upload_skill.py:58*

### test_upload_with_invalid_zip

**Category**: instantiation  
**Description**: Instantiate upload_skill_api: Test upload with invalid zip file (not a zip)  
**Confidence**: 0.80  
**Tags**: unittest  

```python
# Setup
'Store original API key state'
self.original_api_key = os.environ.get('ANTHROPIC_API_KEY')

success, message = upload_skill_api(tmpfile.name)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_upload_skill.py:72*

### test_upload_accepts_path_object

**Category**: instantiation  
**Description**: Instantiate create_test_zip: Test that upload_skill_api accepts Path objects  
**Confidence**: 0.80  
**Tags**: unittest  

```python
# Setup
'Store original API key state'
self.original_api_key = os.environ.get('ANTHROPIC_API_KEY')

zip_path = self.create_test_zip(tmpdir)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_upload_skill.py:84*

### test_upload_accepts_path_object

**Category**: instantiation  
**Description**: Instantiate upload_skill_api: Test that upload_skill_api accepts Path objects  
**Confidence**: 0.80  
**Tags**: unittest  

```python
# Setup
'Store original API key state'
self.original_api_key = os.environ.get('ANTHROPIC_API_KEY')

success, message = upload_skill_api(Path(zip_path))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_upload_skill.py:88*

### test_cli_help_output

**Category**: instantiation  
**Description**: Instantiate run: Test that skill-seekers upload --help works  
**Confidence**: 0.80  
**Tags**: unittest  

```python
result = subprocess.run(['skill-seekers', 'upload', '--help'], capture_output=True, text=True, timeout=5)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_upload_skill.py:101*

### test_cli_executes_without_errors

**Category**: instantiation  
**Description**: Instantiate run: Test that skill-seekers-upload entry point works  
**Confidence**: 0.80  
**Tags**: unittest  

```python
result = subprocess.run(['skill-seekers-upload', '--help'], capture_output=True, text=True, timeout=5)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_upload_skill.py:117*

### test_code_stream

**Category**: instantiation  
**Description**: Instantiate CodeStream: Test CodeStream data class.  
**Expected**: assert code_stream.directory == Path('/tmp/repo')  
**Confidence**: 0.80  

```python
code_stream = CodeStream(directory=Path('/tmp/repo'), files=[Path('/tmp/repo/src/main.py')])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_github_fetcher.py:29*

### test_docs_stream

**Category**: instantiation  
**Description**: Instantiate DocsStream: Test DocsStream data class.  
**Expected**: assert docs_stream.readme == '# README'  
**Confidence**: 0.80  

```python
docs_stream = DocsStream(readme='# README', contributing='# Contributing', docs_files=[{'path': 'docs/guide.md', 'content': '# Guide'}])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_github_fetcher.py:35*

### test_insights_stream

**Category**: instantiation  
**Description**: Instantiate InsightsStream: Test InsightsStream data class.  
**Expected**: assert insights_stream.metadata['stars'] == 1234  
**Confidence**: 0.80  

```python
insights_stream = InsightsStream(metadata={'stars': 1234, 'forks': 56}, common_problems=[{'title': 'Bug', 'number': 42}], known_solutions=[{'title': 'Fix', 'number': 35}], top_labels=[{'label': 'bug', 'count': 10}])
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_github_fetcher.py:46*

### test_three_stream_data

**Category**: instantiation  
**Description**: Instantiate ThreeStreamData: Test ThreeStreamData combination.  
**Expected**: assert isinstance(three_streams.code_stream, CodeStream)  
**Confidence**: 0.80  

```python
three_streams = ThreeStreamData(code_stream=CodeStream(Path('/tmp'), []), docs_stream=DocsStream(None, None, []), insights_stream=InsightsStream({}, [], [], []))
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_github_fetcher.py:59*

### test_parse_https_url

**Category**: instantiation  
**Description**: Instantiate GitHubThreeStreamFetcher: Test parsing HTTPS GitHub URLs.  
**Expected**: assert fetcher.owner == 'facebook'  
**Confidence**: 0.80  

```python
fetcher = GitHubThreeStreamFetcher('https://github.com/facebook/react')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_github_fetcher.py:74*

### test_parse_https_url_with_git

**Category**: instantiation  
**Description**: Instantiate GitHubThreeStreamFetcher: Test parsing HTTPS URLs with .git suffix.  
**Expected**: assert fetcher.owner == 'facebook'  
**Confidence**: 0.80  

```python
fetcher = GitHubThreeStreamFetcher('https://github.com/facebook/react.git')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_github_fetcher.py:80*

### test_parse_git_url

**Category**: instantiation  
**Description**: Instantiate GitHubThreeStreamFetcher: Test parsing git@ URLs.  
**Expected**: assert fetcher.owner == 'facebook'  
**Confidence**: 0.80  

```python
fetcher = GitHubThreeStreamFetcher('git@github.com:facebook/react.git')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_github_fetcher.py:86*

### test_github_token_from_env

**Category**: instantiation  
**Description**: Instantiate GitHubThreeStreamFetcher: Test GitHub token loaded from environment.  
**Expected**: assert fetcher.github_token == 'test_token'  
**Confidence**: 0.80  
**Tags**: mock  

```python
fetcher = GitHubThreeStreamFetcher('https://github.com/facebook/react')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_github_fetcher.py:98*

### test_classify_files

**Category**: instantiation  
**Description**: Instantiate GitHubThreeStreamFetcher: Test classify_files separates code and docs correctly.  
**Expected**: assert 'main.py' in code_paths  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

fetcher = GitHubThreeStreamFetcher('https://github.com/test/repo')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_github_fetcher.py:120*

### test_analysis_result_basic

**Category**: instantiation  
**Description**: Instantiate AnalysisResult: Test basic AnalysisResult creation.  
**Expected**: assert result.code_analysis == {'files': []}  
**Confidence**: 0.80  

```python
result = AnalysisResult(code_analysis={'files': []}, source_type='local', analysis_depth='basic')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_unified_analyzer.py:33*

### test_analysis_result_with_github

**Category**: instantiation  
**Description**: Instantiate AnalysisResult: Test AnalysisResult with GitHub data.  
**Expected**: assert result.github_docs is not None  
**Confidence**: 0.80  

```python
result = AnalysisResult(code_analysis={'files': []}, github_docs={'readme': '# README'}, github_insights={'metadata': {'stars': 1234}}, source_type='github', analysis_depth='c3x')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_unified_analyzer.py:44*

### test_basic_analysis_local

**Category**: instantiation  
**Description**: Instantiate analyze: Test basic analysis on local directory.  
**Expected**: assert result.source_type == 'local'  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

result = analyzer.analyze(source=str(tmp_path), depth='basic')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_unified_analyzer.py:92*

### test_list_files

**Category**: instantiation  
**Description**: Instantiate list_files: Test file listing.  
**Expected**: assert len(files) == 3  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

files = analyzer.list_files(tmp_path)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_unified_analyzer.py:107*

### test_get_directory_structure

**Category**: instantiation  
**Description**: Instantiate get_directory_structure: Test directory structure extraction.  
**Expected**: assert structure['type'] == 'directory'  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

structure = analyzer.get_directory_structure(tmp_path)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_unified_analyzer.py:123*

### test_extract_imports_python

**Category**: instantiation  
**Description**: Instantiate extract_imports: Test Python import extraction.  
**Expected**: assert '.py' in imports  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

imports = analyzer.extract_imports(tmp_path)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_unified_analyzer.py:146*

### test_extract_imports_javascript

**Category**: instantiation  
**Description**: Instantiate extract_imports: Test JavaScript import extraction.  
**Expected**: assert '.js' in imports  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

imports = analyzer.extract_imports(tmp_path)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_unified_analyzer.py:164*

### test_find_entry_points

**Category**: instantiation  
**Description**: Instantiate find_entry_points: Test entry point detection.  
**Expected**: assert 'main.py' in entry_points  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

entry_points = analyzer.find_entry_points(tmp_path)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_unified_analyzer.py:177*

### test_compute_statistics

**Category**: instantiation  
**Description**: Instantiate compute_statistics: Test statistics computation.  
**Expected**: assert stats['total_files'] == 3  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

stats = analyzer.compute_statistics(tmp_path)
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_unified_analyzer.py:190*

### test_c3x_analysis_local

**Category**: instantiation  
**Description**: Instantiate analyze: Test C3.x analysis on local directory with actual components.  
**Expected**: assert result.source_type == 'local'  
**Confidence**: 0.80  

```python
# Setup
# Fixtures: tmp_path

result = analyzer.analyze(source=str(tmp_path), depth='c3x')
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_unified_analyzer.py:209*

### mock_git_repo

**Category**: config  
**Description**: Configuration example: Create a mock git repository with config files.  
**Confidence**: 0.75  
**Tags**: pytest, mock  

```python
# Setup
# Fixtures: temp_dirs

react_config = {'name': 'react', 'description': 'React framework', 'base_url': 'https://react.dev/'}
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_mcp_git_sources.py:45*

### mock_git_repo

**Category**: config  
**Description**: Configuration example: Create a mock git repository with config files.  
**Confidence**: 0.75  
**Tags**: pytest, mock  

```python
# Setup
# Fixtures: temp_dirs

vue_config = {'name': 'vue', 'description': 'Vue framework', 'base_url': 'https://vuejs.org/'}
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_mcp_git_sources.py:52*

### test_config_file

**Category**: config  
**Description**: Configuration example: Create a minimal test config file  
**Confidence**: 0.75  
**Tags**: pytest  

```python
# Setup
# Fixtures: tmp_path

config = {'name': 'test-e2e', 'description': 'Test skill for E2E testing', 'base_url': 'https://example.com/docs/', 'selectors': {'main_content': 'article', 'title': 'title', 'code_blocks': 'pre'}, 'url_patterns': {'include': ['/docs/'], 'exclude': ['/search', '/404']}, 'categories': {'getting_started': ['intro', 'start'], 'api': ['api', 'reference']}, 'rate_limit': 0.1, 'max_pages': 5}
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_install_skill_e2e.py:67*

### test_config_file

**Category**: config  
**Description**: Configuration example: Create a minimal test config file  
**Confidence**: 0.75  
**Tags**: pytest  

```python
# Setup
# Fixtures: tmp_path

config = {'name': 'test-cli-e2e', 'description': 'Test skill for CLI E2E testing', 'base_url': 'https://example.com/docs/', 'selectors': {'main_content': 'article', 'title': 'title', 'code_blocks': 'pre'}, 'url_patterns': {'include': ['/docs/'], 'exclude': []}, 'categories': {}, 'rate_limit': 0.1, 'max_pages': 3}
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_install_skill_e2e.py:317*

### real_test_config

**Category**: config  
**Description**: Configuration example: Create a real minimal config that can be scraped  
**Confidence**: 0.75  
**Tags**: pytest  

```python
# Setup
# Fixtures: tmp_path

config = {'name': 'test-real-e2e', 'description': 'Real E2E test', 'base_url': 'https://httpbin.org/html', 'selectors': {'main_content': 'body', 'title': 'title', 'code_blocks': 'code'}, 'url_patterns': {'include': [], 'exclude': []}, 'categories': {}, 'rate_limit': 0.5, 'max_pages': 1}
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_install_skill_e2e.py:464*

### test_create_temp_unified_config

**Category**: config  
**Description**: Configuration example: Test creating a unified config from scratch  
**Confidence**: 0.75  

```python
config = {'name': 'test_unified', 'description': 'Test unified config', 'merge_mode': 'rule-based', 'sources': [{'type': 'documentation', 'base_url': 'https://example.com/docs', 'extract_api': True, 'max_pages': 50}, {'type': 'github', 'repo': 'test/repo', 'include_code': True, 'code_analysis_depth': 'surface'}]}
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\src\skill_seekers\cli\test_unified_simple.py:59*

### test_mixed_source_types

**Category**: config  
**Description**: Configuration example: Test config with documentation, GitHub, and PDF sources  
**Confidence**: 0.75  

```python
config = {'name': 'test_mixed', 'description': 'Test mixed sources', 'merge_mode': 'rule-based', 'sources': [{'type': 'documentation', 'base_url': 'https://example.com'}, {'type': 'github', 'repo': 'test/repo'}, {'type': 'pdf', 'path': '/path/to/manual.pdf'}]}
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\src\skill_seekers\cli\test_unified_simple.py:97*

### test_config_validation_errors

**Category**: config  
**Description**: Configuration example: Test that invalid configs are rejected  
**Confidence**: 0.75  

```python
config = {'name': 'test', 'description': 'Test', 'sources': [{'type': 'invalid_type', 'url': 'https://example.com'}]}
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\src\skill_seekers\cli\test_unified_simple.py:131*

### sample_config

**Category**: config  
**Description**: Configuration example: Create a sample config file.  
**Confidence**: 0.75  
**Tags**: pytest  

```python
# Setup
# Fixtures: temp_dirs

config_data = {'name': 'test-framework', 'description': 'Test framework for testing', 'base_url': 'https://test-framework.dev/', 'selectors': {'main_content': 'article', 'title': 'h1', 'code_blocks': 'pre'}, 'url_patterns': {'include': ['/docs/'], 'exclude': ['/blog/', '/search/']}, 'categories': {'getting_started': ['introduction', 'getting-started'], 'api': ['api', 'reference']}, 'rate_limit': 0.5, 'max_pages': 100}
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_mcp_fastmcp.py:64*

### unified_config

**Category**: config  
**Description**: Configuration example: Create a sample unified config file.  
**Confidence**: 0.75  
**Tags**: pytest  

```python
# Setup
# Fixtures: temp_dirs

config_data = {'name': 'test-unified', 'description': 'Test unified scraping', 'merge_mode': 'rule-based', 'sources': [{'type': 'documentation', 'base_url': 'https://example.com/docs/', 'extract_api': True, 'max_pages': 10}, {'type': 'github', 'repo': 'test/repo', 'extract_readme': True}]}
```

*Source: C:\Users\user\Documents\Python\DataVue-App\temp_skills\tests\test_mcp_fastmcp.py:86*

