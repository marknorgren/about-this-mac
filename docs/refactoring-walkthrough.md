# Reducing Complexity: A Philosophy of Software Design in Practice

*2026-03-05T01:42:58Z by Showboat dev*
<!-- showboat-id: a5a039f7-ea52-491b-acd0-352185fefb4b -->

This walkthrough documents the refactoring of **about-this-mac** guided by John Ousterhout's *A Philosophy of Software Design* (APoSD). Each change is traced to a specific principle from the book, with before/after code to show the improvement.

## The Refactoring at a Glance

The codebase suffered from several complexity symptoms (Ch. 2: *The Nature of Complexity*):

- **Change amplification**: formatting logic scattered across the gatherer class and presentation layer
- **Cognitive load**: callers had to know which methods to call on which objects; the gatherer's inheritance tree hid surprise responsibilities
- **Unknown unknowns**: calling `format_simple_output(data)` silently triggered a subprocess call — nowhere in the signature does that show

Seven distinct improvements were made, each targeting a root cause identified in APoSD.

## 1. Composition Over Inheritance (Ch. 4: *Modules Should Be Deep*)

> *The

## 2. Formatting as Pure Functions (Ch. 5: *Information Hiding and Leakage*)

> *"If a piece of information is needed in several places, that's a sign it should be encapsulated in a single location."*

### Before

`format_simple_output` and `format_public_output` lived as methods on `MacInfoGatherer`. This caused **information leakage**: the formatter needed a live gatherer reference to call `_get_model_info()` and `_get_release_date()` — triggering subprocess calls during what looked like pure data formatting.

```python
# hardware_info.py — BEFORE
class MacInfoGatherer(BatteryInfoGatherer):
    def format_simple_output(self, data: Dict[str, Any]) -> str:
        _, model_size, _ = self._get_model_info()     # subprocess!
        release_date, _, _ = self._get_release_date() # subprocess!
        ...
```

### After

The methods moved to `utils/formatting.py` as pure functions that read only from the `data` dict. The necessary fields (`model_size`, `release_date`, `model_year`) are gathered once in `get_hardware_info()` and stored in `HardwareInfo`.

```python
# utils/formatting.py — AFTER
def format_output_as_simple(data: Dict[str, Any]) -> str:
    hw = _coerce_dict(data.get("hardware"))
    model_size = _stringify(hw.get("model_size"), default="")
    release_date = _stringify(hw.get("release_date"), default="")
    ...  # no subprocess, no gatherer reference
```

This is APoSD's *temporal decomposition* anti-pattern fixed: data gathering and presentation are now separate responsibilities.

## 3. Uptime at the Presentation Layer (Ch. 7: *Pulling Complexity Downward*)

> *"It is more important for a module to have a simple interface than a simple implementation."*

### Before

`_get_uptime()` formatted the string itself — days/hours/minutes logic lived inside the data gatherer. Any formatter that wanted to display uptime differently had no way to do so without re-running the system call.

```python
# hardware_info.py — BEFORE
def _get_uptime(self) -> str:
    ...
    days = uptime_seconds // 86400
    parts = []
    if days > 0:
        parts.append(f"{days} {'day' if days == 1 else 'days'}")
    ...
    return " ".join(parts)

@dataclass
class HardwareInfo:
    uptime: str  # already formatted, no way back to raw seconds
```

### After

The gatherer stores raw seconds. Formatting happens at the presentation layer in `format_uptime()`, which any formatter can call.

```python
# hardware_info.py — AFTER
@dataclass
class HardwareInfo:
    uptime: Optional[int]  # seconds since boot, None if unknown

def _get_uptime(self) -> Optional[int]:
    ...
    return int(time.time()) - boot_timestamp

# utils/formatting.py — presentation layer
def format_uptime(uptime_seconds: int) -> str:
    days = uptime_seconds // 86400
    ...
```

This follows APoSD's advice to push complexity downward into the module that owns the data, while exposing a simpler interface upward. The dataclass now holds a value that can be used, tested, or formatted in multiple ways.

## 4. Caching the Permission Check (Ch. 7: *Pulling Complexity Downward*)

> *"Pull complexity downward... If the alternative is to raise an exception, it is almost always better to handle it internally."*

### Before

`_check_permissions()` ran `system_profiler SPHardwareDataType` to verify access, then discarded the output. `get_hardware_info()` immediately ran the same command again.

```python
# BEFORE — two identical subprocess calls at startup
def _check_permissions(self) -> bool:
    subprocess.run(["system_profiler", "SPHardwareDataType", "-json"], check=True)
    return True

def get_hardware_info(self) -> HardwareInfo:
    hw_info = self._run_command(
        ["system_profiler", "SPHardwareDataType", "-json"], privileged=True
    )  # duplicate call!
```

### After

The permission check caches its output. `get_hardware_info()` reuses it and clears the cache to allow GC.

```python
# AFTER — one subprocess call
def _check_permissions(self) -> bool:
    result = subprocess.run(
        ["system_profiler", "SPHardwareDataType", "-json"],
        capture_output=True, text=True, check=True,
    )
    self._cached_hw_json = result.stdout.strip()  # save the work
    return True

def get_hardware_info(self) -> HardwareInfo:
    hw_info = self._cached_hw_json or self._run_command(...)
    self._cached_hw_json = ""  # allow GC
```

The complexity of "run once, use twice" is now entirely inside the class. Callers see no difference.

## 5. Decoupling Raw Commands from the Gatherer (Ch. 5: *Information Leakage*)

> *"Information leakage occurs when the same knowledge is used in multiple places. Any time you see information repeated across modules, ask yourself how to reorganize so it lives in just one place."*

### Before

`commands/raw.py` called `gatherer.run_command()` and `gatherer.get_sysctl_value()` — public pass-through wrappers that existed solely to expose private internals:

```python
# hardware_info.py — BEFORE (pass-through wrappers, APoSD red flag)
def run_command(self, command: List[str], privileged: bool = False) -> str:
    return self._run_command(command, privileged=privileged)

def get_sysctl_value(self, key: str) -> str:
    return self._get_sysctl_value(key)
```

```python
# commands/raw.py — BEFORE
def _get_hardware_info(gatherer: MacInfoGatherer) -> List[str]:
    return [
        gatherer.run_command(["system_profiler", "SPHardwareDataType"], privileged=True),
        f"hw.model: {gatherer.get_sysctl_value('hw.model')}",
    ]
```

### After

`raw.py` imports `run_command` and `get_sysctl_value` directly from `utils/command`. The gatherer no longer leaks its internal command-running machinery:

```python
# commands/raw.py — AFTER
from about_this_mac.utils.command import get_sysctl_value, run_command

def _get_hardware_info(perms: bool) -> List[str]:
    return [
        _run_cmd(["system_profiler", "SPHardwareDataType"], privileged=True, has_full_permissions=perms),
        f"hw.model: {get_sysctl_value('hw.model')}",
    ]
```

The gatherer's two pass-through methods were deleted entirely. APoSD calls these "pass-through methods" — they add interface complexity without adding functionality.

## 6. Specific Exception Types (Ch. 10: *Define Errors Out of Existence*)

> *"The best way to reduce the complexity damage from exception handling is to reduce the number of places where exceptions have to be handled."*

### Before

Bare `except:` clauses silently swallow **all** exceptions — including `KeyboardInterrupt` and `SystemExit`. This is an unknown unknown: callers can't know what went wrong or that it went wrong at all.

```python
# BEFORE
try:
    power_mode = self._run_command(["pmset", "-g"])
    low_power_mode = "lowpowermode 1" in power_mode.lower()
except:   # catches everything including Ctrl-C
    pass

try:
    ...bluetooth parsing...
except:
    pass
```

### After

Each `except` names only the exceptions that can actually occur from the operation in question. This documents the failure modes and lets unexpected errors propagate.

```python
# AFTER
try:
    power_mode = self._run_command(["pmset", "-g"])
    low_power_mode = "lowpowermode 1" in power_mode.lower()
except OSError:
    # pmset may not be available; default to low power mode off.
    pass

try:
    ...bluetooth parsing...
except (json.JSONDecodeError, KeyError, IndexError) as exc:
    logger.debug("Failed to parse Bluetooth information: %s", exc)
```

APoSD goes further and advises designing errors *out of existence* where possible — the `Optional[int]` uptime sentinel (returning `None` instead of raising) is an example of this.

## 7. Verifying the Refactoring Didn't Break Anything

All 44 tests pass and the linter scores 10.00/10 after every change — a prerequisite for calling any refactoring safe.

```bash
uv run pytest -q tests/ 2>&1 | grep -oE '[0-9]+ passed'
```

```output
44 passed
```

```bash
uv run pylint src tests 2>&1 | grep -oE 'rated at [0-9.]+/[0-9]+'
```

```output
rated at 10.00/10
```
