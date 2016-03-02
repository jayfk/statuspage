bundle:
	pip install -r requirements/base.txt
	pip install -r requirements/dev.txt
	pyinstaller statuspage.spec
