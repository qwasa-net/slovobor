const slovobor = {

    input: null,
    output: null,
    form: null,
    status: null,

    words: null,
    word: null,

    tm: null,

    state: "init",

    STATUS_MESSAGES: {
        "init": "Начинаю …",
        "wait": "Подождите, я думаю …",
        "error": "Ой! Что-то пошло не так …",
        "ready": "Готов!",
        "found": "Нашлось: ",
        "found0": "Ничего не нашлось!"
    },

    RAMDOM_WORDS: [
        "вечность",
        "енот-полоскун",
        "ехал Грека через реку",
        "мама мыла раму",
        "игра в слова",
        "на дворе трава, на траве дрова",
        "The quick brown fox",
        "rain in spain",
        "hotel california",
    ],

    API_URL: "/q",

    MAX_LENGTH: 40,
    MIN_LENGTH: 4,

    init: function () {
        if (typeof WEB_API_URL !== "undefined" && WEB_API_URL) {
            this.API_URL = WEB_API_URL;
        }
        this.input = document.getElementById("sl_input");
        this.output = document.getElementById("sl_output");
        this.form = document.getElementById("sl_form");
        this.status = document.getElementById("sl_status");
        if (this.form && this.input && this.output && this.status && this.state == "init") {
            this.form.onsubmit = (ev) => { this.post_word(ev); return false; };
            this.form.onreset = (ev) => { this.input.value = ""; this.input.focus(); return false; };
            this.clear_output();
            this.input.focus();
            this.state = "init";
            this.status.textContent = this.STATUS_MESSAGES[this.state] || "";
            clearTimeout(this.tm);
            this.tm = setTimeout(() => {
                this.init_random_word();
                this.input.focus();
            }, 200);
        } else {
            this.oops();
        }
    },

    init_random_word: function () {
        this.state = "ready";
        if (window.location.hash.length > 1) {
            let hash = window.location.hash.substring(1);
            this.input.value = decodeURIComponent(hash);
            window.location.hash = "#";
        } else {
            this.input.value = this.RAMDOM_WORDS[Math.floor(Math.random() * this.RAMDOM_WORDS.length)];
        }
        this.post_word();
    },

    post_word: function () {

        if (this.state !== "ready" ||
            this.input.value.length < this.MIN_LENGTH) {
            return;
        }

        this.state = "wait";
        this.status.textContent = this.STATUS_MESSAGES[this.state] || "";
        this.clear_output();
        this.input.blur();

        this.word = String(this.input.value).substring(0, this.MAX_LENGTH).toLowerCase();
        this.input.value = this.word;

        let els = this.form.elements;
        let offensive = String(els["cb_offensive"] && els["cb_offensive"].checked && 1 || 0);
        let nouns = String(els["cb_nouns"] && els["cb_nouns"].checked && 1 || 0);

        let req = {
            "method": "post",
            "headers": { "Content-Type": "application/x-www-form-urlencoded" },
            "body": "q=" + this.word + "&o=" + offensive + "&n=" + nouns
        };

        fetch(this.API_URL, req)
            .then((rsp) => {
                rsp.json()
                    .then((data) => {
                        this.read_words(data);
                    })
                    .catch((e) => {
                        this.oops(); // bad json
                    });
            })
            .catch((e) => {
                this.oops(); // bad fetch
            });

    },

    read_words: function (data) {

        if (!data || !data.q) {
            this.oops();
            return;
        }

        this.state = "ready";
        let c = Number(data.c) || 0;

        if (c > 0 && data.w.length > 0) {
            let words = data.w.split(",");
            this.words = words.sort(this._words_cmp);
            this.clear_output();

            for (let i = 0; i < this.words.length; i++) {
                let el = document.createElement("span");
                el.textContent = this.words[i];
                this.output.appendChild(el);
            }
        }

        if (c > 0) {
            this.status.textContent = this.STATUS_MESSAGES["found"] + c.toString();
        } else {
            this.status.textContent = this.STATUS_MESSAGES["found0"];
        }

    },

    oops: function () {
        this.state = "error";
        this.status.textContent = this.STATUS_MESSAGES[this.state];
        clearTimeout(this.tm);
        this.tm = setTimeout(() => { this.init(); }, 9999);
    },

    clear_output: function () {
        while (this.output.firstChild) {
            this.output.removeChild(this.output.firstChild);
        }
    },

    _words_cmp: function (a, b) {
        if (a.length == b.length)
            return a.localeCompare(b); // (a > b);
        else if (a.length > b.length)
            return -1;
        return 1;
    }

};

window.addEventListener("load", (e) => { slovobor.init(); });
