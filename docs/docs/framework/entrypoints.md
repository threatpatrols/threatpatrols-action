# API Documentation

## API Entrypoint
::: threatpatrols_action.api

#### Example API entrypoint
```python
from threatpatrols_action.api import load_api_app

from . import config
from .action.action import dev_sample

entrypoint = load_api_app(config=config, action=dev_sample)
```

---

## CLI Entrypoint
::: threatpatrols_action.cli

#### Example CLI entrypoint
```python
from threatpatrols_action.cli import load_cli_app

from . import config
from .action.action import dev_sample

entrypoint = load_cli_app(config=config, action=dev_sample)
```
