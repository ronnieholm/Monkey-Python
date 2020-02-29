default: test mypy mylint repl

repl:
	python3 main.py

test:
	python3 -m unittest *_test.py

mypy:
	# Or use --strict, a superset of --disallow-untyped-defs
	# Use tools such as MonkeyType or pyannotate to generate initial hints
	mypy --disallow-untyped-defs *.py

lint:
	pylint *.py

clean:
	rm -fr __pycache__
	rm -fr .mypy_cache
	rm -fr venv