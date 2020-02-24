default: test mypy mylint repl

repl:
	python3 main.py

test:
	python3 -m unittest *_test.py

mypy:
	mypy *.py

lint:
	pylint *.py

clean:
	rm -fr __pycache__
	rm -fr .mypy_cache
	rm -fr venv