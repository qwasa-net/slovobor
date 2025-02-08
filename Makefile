SHELL := /bin/bash
TIMESTAMP := $(shell date +"%Y%m%d-%H%M")

MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
MAKEFILE_DIR := $(dir $(MAKEFILE_PATH))
HOME_PATH := $(MAKEFILE_DIR)
MENAME ?= $(shell basename "$(MAKEFILE_DIR)")

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


deploy_remote: cleanpy deploy_remote_install deploy_remote_files deploy_remote_reload ## (1)+(2)+(3)


deploy_remote_update: cleanpy deploy_remote_files deploy_remote_reload  ## (2)+(3)


deploy_remote_install: SSH_AUTH_KEY := $(shell cat _keys/_ssh/slovobor.tktk.in-id_rsa.pub 2>/dev/null)
deploy_remote_install: ## (1) create user, install services (sudo)
	$(SSH) "$(TARGET)" "\
	sudo useradd -d $(TARGET_PATH) -m -g $(TARGET_USER_GROUP) -s /bin/false $(TARGET_USER) || true; \
	sudo mkdir -p '$(TARGET_PATH)/.ssh/'; \
	sudo echo '$(SSH_AUTH_KEY)' > '$(TARGET_PATH)/.ssh/authorized_keys'; \
	sudo mkdir -pv '$(TARGET_PATH)/_logs' '$(TARGET_PATH)/db'; \
	sudo touch '$(TARGET_PATH)/_config.env'; \
	sudo ln -sf $(TARGET_PATH)/deploy/slovobor.service /etc/systemd/system/;\
	sudo ln -sf $(TARGET_PATH)/deploy/nginx.conf /etc/nginx/sites-enabled/slovobor.conf;\
	sudo ln -sf $(TARGET_PATH)/deploy/logrotate.conf /etc/logrotate.d/slovobor.conf;\
	sudo chown -R $(TARGET_USER):$(TARGET_USER_GROUP) $(TARGET_PATH); \
	sudo chmod -R 750 $(TARGET_PATH); \
	"

deploy_remote_files: ## (2) copy updated files to TARGET (with rsync)
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


deploy_remote_reload: ## (3) reload services on TARGET
	$(SSH) "$(TARGET)" "\
	sudo systemctl reload nginx; \
	sudo systemctl daemon-reload; \
	sudo systemctl restart slovobor; \
	"

build_db_ruwiki: DB_LANG ?= ru
build_db_ruwiki: DB_SRC_PATH ?= $(HOME_PATH)/data/src/$(WIKIFILENAME)
build_db_ruwiki: DB_PARSED_PATH ?= $(HOME_PATH)/data/src/$(DB_LANG)-parsed.json
build_db_ruwiki: DB_COMPILED_PATH ?= $(HOME_PATH)/data/db/$(DB_LANG).slvbr.db
build_db_ruwiki: ## (0) build database files

	# download wiki XML
	-@echo wget $(WIKIURL) -c -O "$(DB_SRC_PATH)"
	test -f "$(DB_SRC_PATH)" || exit 1 # wiki file not found

	# wiki XML → JSON
	$(HOME_PATH)/_env/bin/python \
		slovobor/tools/dbbuilder/parse_ruwiktionary_to_json.py \
		--lang $(DB_LANG) \
		"$(DB_SRC_PATH)" \
		"$(DB_PARSED_PATH)"
	bzip2 "$(DB_PARSED_PATH)"

	# JSON → DB
	$(HOME_PATH)/_env/bin/python \
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
	cd "$(HOME_PATH)/slovobor/slvbr" &&\
	DOCKER_BUILDKIT=1 BUILDKIT_PROGRESS=plain \
	docker build \
	-f "$(HOME_PATH)/slovobor/slvbr/dockerfile" \
	-t slvbr \
	"$(HOME_PATH)/slovobor/slvbr"


build_front: ## (0) build web page (frontend)
	env -v \
	YANDEX_METRIKA_ID=$(YANDEX_METRIKA_ID) \
	GOOGLE_TRACKING_ID="'$(GOOGLE_TRACKING_ID)'" \
	NODE_ENV=production \
	./node_modules/.bin/webpack


run_static_web:  ## (DEV) run local test server for frontend
	cd "$(HOME_PATH)/www" && python3 -m http.server


local_env_install: back_env_install front_env_install  ## (DEV) install local environment
	mkdir -pv "$(HOME_PATH)/_logs"
	python3 -m venv --clear "$(HOME_PATH)/_env"
	"$(HOME_PATH)/_env/bin/pip3" install -U -r requirements.txt


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
