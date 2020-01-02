lint:
	docker run -e "TOXENV=flake8" -v "${CURDIR}:/usr/src/app" ggueret/pelican-dashify

test:
	docker run -e "TOXENV=${TOXENV}" -v "${CURDIR}:/usr/src/app" ggueret/pelican-dashify

build:
	docker build -t ggueret/pelican-dashify .

push:
	docker push ggueret/pelican-dashify
