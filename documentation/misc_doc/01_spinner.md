# Spinner Usage

The spinner is a rolling animation of 1 caracter that indicates that the program is still alive,
usefull for long processes or api calls.

**Exemple**:
```python
	import time
	from silly_engine.components.spinner import run_with_spinner

	def long_task(seconds):
		time.sleep(seconds)
		return "done"

	result = run_with_spinner(long_task, 2)
	print(result)
```