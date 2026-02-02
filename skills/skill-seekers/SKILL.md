---
name: skill-seekers
description: Generate LLM skills from documentation, codebases, and GitHub repositories
---

# Skill Seekers

## Prerequisites

```bash
pip install skill-seekers
# Or: uv pip install skill-seekers
```

## Commands

| Source | Command |
|--------|---------|
| Local code | `skill-seekers-codebase --directory ./path` |
| Docs URL | `skill-seekers scrape --url https://...` |
| GitHub | `skill-seekers github --repo owner/repo` |
| PDF | `skill-seekers pdf --file doc.pdf` |

## Quick Start

```bash
# Analyze local codebase
skill-seekers-codebase --directory /path/to/project --output output/my-skill/

# Package for Claude
yes | skill-seekers package output/my-skill/ --no-open
```

## Options

| Flag | Description |
|------|-------------|
| `--depth surface/deep/full` | Analysis depth |
| `--skip-patterns` | Skip pattern detection |
| `--skip-test-examples` | Skip test extraction |
| `--ai-mode none/api/local` | AI enhancement |

---

# temp_skills Codebase

## Description

Local codebase analysis and documentation generated from code analysis.

**Path:** `C:\Users\user\Documents\Python\DataVue-App\temp_skills`
**Files Analyzed:** 140
**Languages:** Python
**Analysis Depth:** deep

## When to Use This Skill

Use this skill when you need to:
- Understand the codebase architecture and design patterns
- Find implementation examples and usage patterns
- Review API documentation extracted from code
- Check configuration patterns and best practices
- Explore test examples and real-world usage
- Navigate the codebase structure efficiently

## ??Quick Reference

### Codebase Statistics

**Languages:**
- **Python**: 140 files (100.0%)

**Analysis Performed:**
- ??API Reference (C2.5)
- ??Dependency Graph (C2.6)
- ??Design Patterns (C3.1)
- ??Test Examples (C3.2)
- ??Configuration Patterns (C3.4)
- ??Architectural Analysis (C3.7)

### ?Ž¨ Design Patterns Detected

*From C3.1 codebase analysis (confidence > 0.7)*

- **Factory**: 44 instances
- **Strategy**: 28 instances
- **Observer**: 8 instances
- **Builder**: 6 instances
- **Command**: 3 instances

*Total: 90 high-confidence patterns*

*See `references/patterns/` for complete pattern analysis*

## ?? Code Examples

*High-quality examples extracted from test files (C3.2)*

**Instantiate InsightsStream: Test complete pipeline: GitHub URL ??Basic analysis ??Merged output

This tests the fast path (1-2 minutes) without C3.x analysis.** (complexity: 1.00)

```python
insights_stream = InsightsStream(metadata={'stars': 1234, 'forks': 56, 'language': 'Python', 'description': 'A test project'}, common_problems=[{'title': 'Installation fails on Windows', 'number': 42, 'state': 'open', 'comments': 15, 'labels': ['bug', 'windows']}, {'title': 'Import error with Python 3.6', 'number': 38, 'state': 'open', 'comments': 10, 'labels': ['bug', 'python']}], known_solutions=[{'title': 'Fixed: Module not found', 'number': 35, 'state': 'closed', 'comments': 8, 'labels': ['bug']}], top_labels=[{'label': 'bug', 'count': 25}, {'label': 'enhancement', 'count': 15}, {'label': 'documentation', 'count': 10}])
```

**Instantiate InsightsStream: Test complete router generation workflow with GitHub streams.

Validates:
1. Router config created
2. Router SKILL.md includes GitHub metadata
3. Router SKILL.md includes README quick start
4. Router SKILL.md includes common issues
5. Routing keywords include GitHub labels (2x weight)** (complexity: 1.00)

```python
insights_stream = InsightsStream(metadata={'stars': 5000, 'forks': 250, 'language': 'Python', 'description': 'Fast test framework'}, common_problems=[{'title': 'OAuth setup fails', 'number': 150, 'state': 'open', 'comments': 30, 'labels': ['bug', 'oauth']}, {'title': 'Async deadlock', 'number': 142, 'state': 'open', 'comments': 25, 'labels': ['async', 'bug']}, {'title': 'Token refresh issue', 'number': 130, 'state': 'open', 'comments': 20, 'labels': ['oauth']}], known_solutions=[{'title': 'Fixed OAuth redirect', 'number': 120, 'state': 'closed', 'comments': 15, 'labels': ['oauth']}, {'title': 'Resolved async race', 'number': 110, 'state': 'closed', 'comments': 12, 'labels': ['async']}], top_labels=[{'label': 'oauth', 'count': 45}, {'label': 'async', 'count': 38}, {'label': 'bug', 'count': 30}])
```

**Workflow: Test complete pipeline with three-stream data.** (complexity: 1.00)

```python
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

**Workflow: Test integration with actual code analyzer output format.** (complexity: 1.00)

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
self.assertIn('add(a: float, b: float) ??float', py_content)
js_file = next((f for f in generated.values() if f.name == 'utils.md'))
js_content = js_file.read_text()
self.assertIn('formatDate', js_content)
self.assertIn('**Language**: JavaScript', js_content)
```

**Workflow: Test integration with actual code analyzer output format.** (complexity: 1.00)

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
self.assertIn('add(a: float, b: float) ??float', py_content)
js_file = next((f for f in generated.values() if f.name == 'utils.md'))
js_content = js_file.read_text()
self.assertIn('formatDate', js_content)
self.assertIn('**Language**: JavaScript', js_content)
```

**Workflow: E2E Test 1: Direct git URL workflow (no source registration)

Steps:
1. Clone repository via direct git URL
2. List available configs
3. Fetch specific config
4. Verify config content** (complexity: 1.00)

```python
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

**Workflow: E2E Test 2: Complete workflow with source registration

Steps:
1. Add source to registry
2. List sources
3. Get source details
4. Clone via source name
5. Fetch config
6. Update source (re-add with different priority)
7. Remove source
8. Verify removal** (complexity: 1.00)

```python
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

**Workflow: E2E Test 3: Multiple sources with priority resolution

Steps:
1. Add multiple sources with different priorities
2. Verify sources are sorted by priority
3. Enable/disable sources
4. List enabled sources only** (complexity: 1.00)

```python
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

**Workflow: E2E Test 4: Pull updates from existing repository

Steps:
1. Clone repository
2. Add new commit to original repo
3. Pull updates
4. Verify new config is available** (complexity: 1.00)

```python
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

**Workflow: E2E Test 5: Force refresh (delete and re-clone)

Steps:
1. Clone repository
2. Modify local cache manually
3. Force refresh
4. Verify cache was reset** (complexity: 1.00)

```python
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

*See `references/test_examples/` for all extracted examples*

## ?™ï? Configuration Patterns

*From C3.4 configuration analysis*

**Configuration Files Analyzed:** 18
**Total Settings:** 144
**Patterns Detected:** 0

**Configuration Types:**
- unknown: 18 files

*See `references/config_patterns/` for detailed configuration analysis*

## ?? Available References

This skill includes detailed reference documentation:

- **API Reference**: `references/api_reference/` - Complete API documentation
- **Dependencies**: `references/dependencies/` - Dependency graph and analysis
- **Patterns**: `references/patterns/` - Detected design patterns
- **Examples**: `references/test_examples/` - Usage examples from tests
- **Configuration**: `references/config_patterns/` - Configuration patterns

---

**Generated by Skill Seeker** | Codebase Analyzer with C3.x Analysis
