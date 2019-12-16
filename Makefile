GITHUB_USER=jayfk
GITHUB_REPO=statuspage
GITHUB_RELEASE := $(shell which github-release)
all: osx linux

release:
ifndef version
    $(error version is undefined. usage: make release version=x.x)
endif

ifndef GITHUB_TOKEN
    $(error GITHUB_TOKEN is undefined.)
endif

ifndef GITHUB_RELEASE
    $(error no github-release binary found)
endif
	sed -i '' 's/__version__ = "[^0-9.]*\([0-9.]*\).*"/__version__ = "$(version)"/' statuspage/statuspage.py
	sed -i '' 's/__version__ = "[^0-9.]*\([0-9.]*\).*"/__version__ = "$(version)"/' setup.py
	git commit -a -m 'new release $(version)'
	git tag $(version)
	git push origin master --tags
	make all
	#python setup.py sdist bdist_wheel upload
	#github-release release --user $(GITHUB_USER) --repo $(GITHUB_REPO) --tag $(version) --name $(version)
	#github-release upload --user $(GITHUB_USER) --repo $(GITHUB_REPO) --tag $(version) --name 'statuspage-darwin-64' --file dist/statuspage-darwin-64
	#github-release upload --user $(GITHUB_USER) --repo $(GITHUB_REPO) --tag $(version) --name 'statuspage-linux-64' --file dist/statuspage-linux-64
	

osx:
	pip install -r requirements/base.txt
	pip install -r requirements/dev.txt
	pyinstaller statuspage/statuspage.spec
	mv dist/statuspage dist/statuspage-darwin-64

linux:

	docker run -e LC_ALL="C.UTF-8" -e LANG="C.UTF-8" -v $(shell pwd):/app -w=/app -it python:3.5 bash -c "pip install -r requirements/base.txt && pip install -r requirements/dev.txt && pyinstaller statuspage/statuspage.spec"
	mv dist/statuspage dist/statuspage-linux-64

