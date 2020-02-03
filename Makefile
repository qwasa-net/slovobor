SHELL := /bin/bash
TIMESTAMP := $(shell date +"%Y%m%d-%H%M")

MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
MAKEFILE_DIR := $(dir $(MAKEFILE_PATH))
HOME_PATH := $(MAKEFILE_DIR)
MENAME ?= $(shell basename "$(MAKEFILE_DIR)")

SSH_KEY ?= keys/_ssh/slovobor.tktk.in-id_rsa
SSH_OPTS ?= -p222
SSH ?= ssh -i $(SSH_KEY) $(SSH_OPTS)
TARGET ?= slovobor.tktk.in@tktk.in
TARGET_PATH ?= /home/slovobor.tktk.in

YANDEX_METRIKA_ID ?= $(shell cat keys/_YANDEX_METRIKA_ID 2>/dev/null)
GOOGLE_TRACKING_ID ?= $(shell cat keys/_GOOGLE_TRACKING_ID 2>/dev/null)

WIKIFILENAME ?= ruwiktionary-latest-pages-articles-multistream.xml.bz2
WIKIURL ?= "https://dumps.wikimedia.org/ruwiktionary/latest/$(WIKIFILENAME)"

DEPLOY_ABLES := www slovobor server data requirements.txt Makefile config.template.json

.PHONY: help

help:
	-@grep -E "^[a-z_0-9]+:" "$(strip $(MAKEFILE_LIST))" | grep '##' | sed 's/:.*##/## —/ig' | column -t -s '##'

deploy_remote: deploy_remote_files deploy_remote_install deploy_remote_install_system init_db deploy_remote_reload ## (1)+(2)+(3)+(4)

deploy_remote_update: deploy_remote_files deploy_remote_reload  ## (2)+(3)

deploy_remote_files: cleanpy ## (1) copy (updated) files to TARGET (with rsync)
	rsync -e "$(SSH)" \
	--recursive \
	--update \
	--verbose \
	--delete \
	--exclude=__pycache__ \
	$(DEPLOY_ABLES) \
	"$(TARGET):$(TARGET_PATH)"

deploy_remote_install: ## (2) create running environment on TARGET
	$(SSH) $(TARGET) make -f "$(TARGET_PATH)/Makefile" install_env

install_env:
	mkdir -pv "$(TARGET_PATH)"
	mkdir -pv "$(TARGET_PATH)/_logs"
	touch "$(TARGET_PATH)/_redis.pid" "$(TARGET_PATH)/_celery_worker.pid"
	test -f "$(TARGET_PATH)/_env/bin/python" || python3 -m venv "$(TARGET_PATH)/_env"
	"$(TARGET_PATH)/_env/bin/pip" install -U -r "$(TARGET_PATH)/requirements.txt"
	test -f "$(TARGET_PATH)/_config.json" || echo "{}" > "$(TARGET_PATH)/_config.json"
	chmod 600 "$(TARGET_PATH)/_config.json"

deploy_remote_install_system: ## (2-config+su) copy config files for system services (uwsgi and systemd)
	-@echo "======================================"
	-@echo "========= MANUAL DEPLOY START ========"
	-@echo "======================================"
	-@echo "========== [1] INIT DATABASE ========="
	-@echo "========== [2] EDIT CONFIG ==========="
	-@echo "vim $(TARGET_PATH)/_config.json"
	-@echo "========== [3] SUDO =================="
	-@echo "# ln -sf $(TARGET_PATH)/server/uwsgi/* /etc/uwsgi/apps-enabled/"
	-@echo "ln -sf $(TARGET_PATH)/server/uwsgi/* /etc/uwsgi-emperor/vassals/"
	-@echo "# ln -sf $(TARGET_PATH)/server/systemd/* /etc/systemd/system/"
	-@echo "ln -sf $(TARGET_PATH)/server/nginx.conf /etc/nginx/sites-enabled/slovobor.tktk.in.conf"
	-@echo "ln -sf $(TARGET_PATH)/server/logrotate.conf /etc/logrotate.d/slovobor"
	-@echo "systemctl link $(TARGET_PATH)/server/systemd/*"
	-@echo "systemctl reload nginx"
	-@echo "# systemctl restart uwsgi.service"
	-@echo "systemctl restart uwsgi-emperor.service"
	-@echo "systemctl daemon-reload"
	-@echo "systemctl enable slovobor-celery"
	-@echo "systemctl enable slovobor-redis"
	-@echo "systemctl restart slovobor-celery"
	-@echo "systemctl restart slovobor-redis"
	-@echo "======================================"
	sleep 1

init_db: ## (3) init database
	ls -ltr $(HOME_PATH)/slovobor/tools/dbbuilder/
	-@echo "========== ERROR: database auto deploy not implemented! (yet?) ====="
	-@echo "please run:"
	-@echo "> mysql < slovobor/tools/dbbuilder/create_tables.sql"
	-@echo "> mysql < slovobor/tools/dbbuilder/create_procedure.sql"
	-@echo ">bunzip2 -c < data/data-latest.sql.bz2 | mysql"
	sleep 1

deploy_remote_reload: ## (4) reload services on TARGET
	$(SSH) $(TARGET) 'touch --no-create \
	/home/slovobor.tktk.in/server/uwsgi/slovobor-tgbot.ini \
	/home/slovobor.tktk.in/server/uwsgi/slovobor-web.ini'
	-@echo sudo systemctl restart slovobor-celery
	-@echo sudo systemctl restart slovobor-redis

build_db: ## (0) build database files
	cd $(HOME_PATH);
	-@echo wget $(WIKIURL) -c -O "$(HOME_PATH)/data/$(WIKIFILENAME)"
	test -f "$(HOME_PATH)/data/$(WIKIFILENAME)" || exit 1 # wiki file not found
	bunzip2 -c < $(HOME_PATH)/data/ruwiktionary-latest-pages-articles-multistream.xml.bz2 | \
	$(HOME_PATH)/_env/bin/python slovobor/tools/dbbuilder/parse_wiktionary_to_json.py - "data/data-${TIMESTAMP}.json";
	$(HOME_PATH)/_env/bin/python slovobor/tools/dbbuilder/json_to_insert_sql.py "data/data-${TIMESTAMP}.json"
	bzip2 "data/data-${TIMESTAMP}.json"
	bzip2 "data/data-${TIMESTAMP}.sql"
	ln -sf "data-${TIMESTAMP}.json.bz2" "data/data-latest.json.bz2"
	ln -sf "data-${TIMESTAMP}.sql.bz2" "data/data-latest.sql.bz2"

build_web: ## (0) build web page (frontend)
	env -v \
	YANDEX_METRIKA_ID=$(YANDEX_METRIKA_ID) \
	GOOGLE_TRACKING_ID="'$(GOOGLE_TRACKING_ID)'" \
	NODE_ENV=production \
	./node_modules/.bin/webpack

run_static_web:  ## (DEV) run local test server for frontend
	cd "$(HOME_PATH)/www" && python3 -m http.server

local_env_install: back_env_install front_env_install  ## (DEV) install local environment
	mkdir -pv "$(HOME_PATH)/_logs"

back_env_install:
	cd $(HOME_PATH)
	python3 -m venv $(HOME_PATH)/_env
	$(HOME_PATH)/_env/bin/pip install -U -r requirements.txt

front_env_install:
	npm install npm@latest
	./node_modules/.bin/npm install

front_env_update:
	./node_modules/.bin/npm update
	./node_modules/.bin/npm audit fix

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
