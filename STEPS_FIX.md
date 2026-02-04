# STEPS ISSUE - ROOT CAUSE AND FIX

## Why Steps Are Still 25

The backend process that's running was started **BEFORE** you changed config.py from 25 to 15.

Python loads config.py when the module is imported. The old running process still has the old value (25) cached in memory.

## How to Fix

### Step 1: Kill the old backend process
```powershell
# Find the Python process running app.py
tasklist | findstr python

# Kill it (replace XXXX with PID)
taskkill /pid XXXX /f
```

### Step 2: Clear Python cache
```powershell
# Clear __pycache__ directories
cd "C:\Users\Yasir\OneDrive\Desktop\AIML-FINAL\textile_generator_backend"
Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force
```

### Step 3: Restart backend
```powershell
cd "C:\Users\Yasir\OneDrive\Desktop\AIML-FINAL\textile_generator_backend"
python app.py
```

### Step 4: Verify new config is loaded
In backend console, you should see logs when generating that show step count.
Or in the logs, look for how many steps are being processed (should be 15, not 25).

## Config.py Location

**File**: `textile_generator_backend/config.py` (Line 29)
```python
# Generation defaults
DEFAULT_STEPS = 15  # Reduced for faster generation
```

## How It's Used

**File**: `textile_generator_backend/app/routes/generation.py`
- Line 183: `num_inference_steps=app.config['DEFAULT_STEPS']`
- Line 195: `num_inference_steps=app.config['DEFAULT_STEPS']`
- Line 206: `num_inference_steps=app.config['DEFAULT_STEPS']`

When backend is restarted, it will read config.py and use 15 steps.

## Frontend Override

The frontend also specifies steps in Generator.tsx line 146:
```typescript
num_inference_steps: 15,
```

This is sent to the backend, but the backend's `app.config['DEFAULT_STEPS']` takes precedence if different.

To use frontend's value instead of config, modify `generation.py` to use:
```python
num_inference_steps = data.get('num_inference_steps', app.config['DEFAULT_STEPS'])
```

Then frontend can override per-request.
