# Quickstart

## 1) Flash firmware

```bash
cd firmware
pio run -t upload
```

## 2) Install host runtime

```bash
cd host
python -m venv .venv
. .venv/bin/activate
pip install -e .
```

## 3) Run example

```bash
cd ..
python examples/tilt_tone.py --port COM3
```
