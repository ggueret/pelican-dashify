lint:
	docker run -e "TOXENV=flake8" -v "${CURDIR}:/usr/src/app" ggueret/pelican-dashify flake8

test:
	docker run -e "TOXENV=${TOXENV}" -v "${CURDIR}:/usr/src/app" ggueret/pelican-dashify pytest

build:
	docker build -t ggueret/pelican-dashify .

push:
	docker push ggueret/pelican-dashify

shell:
	docker run -v "${CURDIR}:/usr/src/app" -ti ggueret/pelican-dashify /bin/bash
