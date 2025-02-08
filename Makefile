SHELL := /bin/bash
TIMESTAMP := $(shell date +"%Y%m%d-%H%M")

MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
MAKEFILE_DIR := $(dir $(MAKEFILE_PATH))
HOME_PATH := $(MAKEFILE_DIR)
MENAME ?= $(shell basename "$(MAKEFILE_DIR)")

PYTHON_VENV ?= $(HOME_PATH)/_venv
PYTHON ?= $(PYTHON_VENV)/bin/python

SSH_KEY ?= _keys/_ssh/slovobor.tktk.in-id_rsa
SSH_OPTS ?= -p222
SSH ?= ssh -i $(SSH_KEY) $(SSH_OPTS)
TARGET_USER ?= slovobor.tktk.in
TARGET_USER_GROUP ?= www-data
TARGET ?= $(TARGET_USER)@tktk.in
TARGET_PATH ?= /home/$(TARGET_USER)

YANDEX_METRIKA_ID ?= $(shell cat _keys/_YANDEX_METRIKA_ID 2>/dev/null)
GOOGLE_TRACKING_ID ?= $(shell cat _keys/_GOOGLE_TRACKING_ID 2>/dev/null)

WIKIFILENAME ?= ruwiktionary-latest-pages-articles-multistream.xml.bz2
WIKIURL ?= "https://dumps.wikimedia.org/ruwiktionary/latest/$(WIKIFILENAME)"

BACK_EXE_PATH := $(HOME_PATH)/slvbr.back

DEPLOY_ABLES := www deploy data/db Makefile config.template.env _keys/_config.env $(BACK_EXE_PATH)

.PHONY: help

help:
	-@grep -E "^[a-z_0-9]+:" "$(strip $(MAKEFILE_LIST))" | grep '##' | sed 's/:.*##/## —/ig' | column -t -s '##'
	@echo "  "
	@echo "> make build_tools_install build_db_ruwiki build_back build_front deploy_remote"


build_tools_install: ## (DEV) install local environment
	mkdir -pv "$(HOME_PATH)/_logs"
	# database tools
	python3 -m venv --clear "$(PYTHON_VENV)"
	$(PYTHON) -m pip install -U -r requirements.txt
	# frontend tools
	npm install npm@^11.1.0
	./node_modules/.bin/npm install


build_db_ruwiki: DB_LANG ?= ru
build_db_ruwiki: DB_SRC_PATH ?= $(HOME_PATH)/data/src/$(WIKIFILENAME)
build_db_ruwiki: DB_PARSED_PATH ?= $(HOME_PATH)/data/src/$(DB_LANG)-parsed.json
build_db_ruwiki: DB_COMPILED_PATH ?= $(HOME_PATH)/data/db/$(DB_LANG).slvbr.db
build_db_ruwiki: ## (0) build database files

	# download wiki XML
	-@echo wget $(WIKIURL) -c -O "$(DB_SRC_PATH)"
	test -f "$(DB_SRC_PATH)" || exit 1 # wiki file not found

	# wiki XML → JSON
	$(PYTHON) \
		slovobor/tools/dbbuilder/parse_ruwiktionary_to_json.py \
		--lang $(DB_LANG) \
		"$(DB_SRC_PATH)" \
		"$(DB_PARSED_PATH)"
	bzip2 --verbose --force "$(DB_PARSED_PATH)"

	# JSON → DB
	$(PYTHON) \
		slovobor/tools/dbbuilder/dbcompiler.py \
		--min-length 2 \
		--tags-language $(DB_LANG) \
		--morph NVA \
		--encoding cp1251 \
		--best-tag-order \
		"$(DB_PARSED_PATH).bz2" "$(DB_COMPILED_PATH)"


build_back: ## (0) build backend
	cd "$(HOME_PATH)/slovobor/back/slvbr" &&\
	CGO_ENABLED=0 GOOS=linux \
	go build -v -ldflags="-s -w" -o "$(BACK_EXE_PATH)" .
	ls -l "$(BACK_EXE_PATH)"


build_back_image: ## (X) build backend docker image
	cd "$(HOME_PATH)/slovobor/back/" &&\
	DOCKER_BUILDKIT=1 BUILDKIT_PROGRESS=plain \
	docker build \
	-f "$(HOME_PATH)/slovobor/back/dockerfile" \
	-t slvbr \
	"$(HOME_PATH)/slovobor/back/"


build_front: ## (0) build web page (frontend)
	env -v \
	YANDEX_METRIKA_ID=$(YANDEX_METRIKA_ID) \
	GOOGLE_TRACKING_ID="'$(GOOGLE_TRACKING_ID)'" \
	NODE_ENV=production \
	./node_modules/.bin/npx webpack --config webpack.config.js


deploy_remote: cleanpy deploy_remote_install deploy_remote_files deploy_remote_reload ## (1)+(2)+(3)


deploy_remote_update: cleanpy deploy_remote_files deploy_remote_reload  ## (2)+(3)


deploy_remote_install: SSH_AUTH_KEY := $(shell cat _keys/_ssh/slovobor.tktk.in-id_rsa.pub 2>/dev/null)
deploy_remote_install: ## (1) create user, install services (sudo)
	$(SSH) "$(TARGET)" "\
	sudo useradd -d $(TARGET_PATH) -m -g $(TARGET_USER_GROUP) -s /bin/false $(TARGET_USER); \
	sudo mkdir -pv '$(TARGET_PATH)/.ssh/'; \
	sudo echo '$(SSH_AUTH_KEY)' > '$(TARGET_PATH)/.ssh/authorized_keys'; \
	sudo mkdir -pv '$(TARGET_PATH)/_logs' '$(TARGET_PATH)/db'; \
	sudo touch '$(TARGET_PATH)/_config.env'; \
	sudo ln -sfv $(TARGET_PATH)/deploy/slovobor.service /etc/systemd/system/;\
	sudo ln -sfv $(TARGET_PATH)/deploy/nginx.conf /etc/nginx/sites-enabled/slovobor.conf;\
	sudo ln -sfv $(TARGET_PATH)/deploy/logrotate.conf /etc/logrotate.d/slovobor.conf;\
	sudo chown -Rc $(TARGET_USER):$(TARGET_USER_GROUP) $(TARGET_PATH); \
	sudo chmod -Rc 750 $(TARGET_PATH); \
	"


deploy_remote_files: ## (2) copy updated files to TARGET (rsync)
	rsync -e "$(SSH)" \
	--chown $(TARGET_USER):$(TARGET_USER_GROUP) \
	--ignore-missing-args \
	--recursive \
	--verbose \
	--delete \
	--exclude=__pycache__ \
	--exclude=*.bz2 \
	$(DEPLOY_ABLES) \
	"$(TARGET):$(TARGET_PATH)"


deploy_remote_reload: ## (3) reload services on TARGET (sudo)
	$(SSH) "$(TARGET)" "\
	sudo chown -Rc $(TARGET_USER):$(TARGET_USER_GROUP) $(TARGET_PATH); \
	sudo chmod -Rc 750 $(TARGET_PATH); \
	sudo systemctl reload nginx; \
	sudo systemctl daemon-reload; \
	sudo systemctl restart slovobor; \
	"


cleanpy:
	find $(HOME_PATH) -iname *.pyc -delete
	find $(HOME_PATH) -iname *.pyo -delete


bak:
	tar cv \
	--exclude=_kakas \
	--exclude=_env \
	--exclude='logs/*.log' \
	--exclude='_logs/*.log' \
	--exclude='data/*xml.bz2' \
	--exclude=_test \
	--exclude=node_modules \
	./ | bzip2 -c > "../${MENAME}-${TIMESTAMP}.tar.bz2"
