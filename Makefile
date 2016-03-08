all: osx linux

osx:
	pip install -r requirements/base.txt
	pip install -r requirements/dev.txt
	pyinstaller statuspage.spec
	mv dist/statuspage dist/statuspage_osx

linux:

	docker run -e LC_ALL="C.UTF-8" -e LANG="C.UTF-8" -v $(shell pwd):/app -w=/app -it python:3.5 bash -c "pip install -r requirements/base.txt && pip install -r requirements/dev.txt && pyinstaller statuspage.spec"
	mv dist/statuspage dist/statuspage_linux

