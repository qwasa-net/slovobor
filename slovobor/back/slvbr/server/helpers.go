package server

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"time"

	"math/rand"

	"slvbr.back/slovobor"
)

var TG_API_URL string = "https://api.telegram.org/bot%s/sendMessage"
var TG_HELLO string = "Привет, %s!\nЭто *Словобор*, я умею составлять слова из слов — отправьте *ЗНАК ВОПРОСА* и *СЛОВО*, например:\n*?* _мама мыла раму_\n*?* _мороженое_\n…"
var TG_NOTHING_FOUND = []string{
	"Ничего не нашлось!",
	"У меня нет слов, извините!",
}
var TG_MUMBLE = []string{
	"ы?",
	"продолжайте!",
	"хотите посоставлять слова? отправьте мне *ЗНАК ВОПРОСА* и *СЛОВО*",
	"давайте перейдём к составлению слов — отправьте мне *ЗНАК ВОПРОСА* и *СЛОВО*",
	"меньше слов — чтобы было больше слов! отправьте мне *ЗНАК ВОПРОСА* и *СЛОВО*",
}

type TGHookMessage struct {
	MessageID int `json:"message_id"`
	From      struct {
		ID           int    `json:"id"`
		IsBot        bool   `json:"is_bot"`
		FirstName    string `json:"first_name"`
		LastName     string `json:"last_name"`
		Username     string `json:"username"`
		LanguageCode string `json:"language_code"`
	} `json:"from"`
	Chat struct {
		ID        int    `json:"id"`
		FirstName string `json:"first_name"`
		LastName  string `json:"last_name"`
		Username  string `json:"username"`
		Type      string `json:"type"`
	} `json:"chat"`
	Date int    `json:"date"`
	Text string `json:"text"`
}

type TGHookUpdate struct {
	UpdateID int           `json:"update_id"`
	Message  TGHookMessage `json:"message"`
}

type TGPostMessage struct {
	Method    string `json:"method"`
	ChatID    int    `json:"chat_id"`
	ReplyTo   int    `json:"reply_to_message_id,omitempty"`
	Text      string `json:"text"`
	ParseMode string `json:"parse_mode,omitempty"`
}

func queryDB(db *slovobor.DB, q string, opts slovobor.TagsOpts, limit int) []string {

	var foundCount int = 0
	var foundAll []uint

	tagLine, tagged := db.StringToTagLine(q, opts)
	if tagged == 0 {
		return nil
	}

	tm_a := time.Now()
	foundCount, foundAll = db.QueryTocFitAll(tagLine, 0, limit)
	tm_b := time.Now()

	words := make([]string, 0, foundCount)
	for _, lineNo := range foundAll {
		word := db.GetRecordText(uint(lineNo))
		words = append(words, word)
	}

	log.Println("QueryRecordFitAll:", foundCount, tm_b.Sub(tm_a))

	return words

}

func sendTGMessage(token string, tgrsp *TGPostMessage) {
	url := fmt.Sprintf(TG_API_URL, token)
	payload, _ := json.Marshal(tgrsp)
	mime := "application/json"
	rsp, err := http.Post(url, mime, bytes.NewReader(payload))
	if err != nil {
		log.Println(err)
		return
	}
	log.Printf("sendTGMessage: {%x} [%s]\n", len(payload), rsp.Status)
	if rsp.StatusCode != http.StatusOK {
		defer rsp.Body.Close()
		body, _ := io.ReadAll(rsp.Body)
		log.Println(string(body))
	}
}

func firstNonEmpty(values ...string) string {
	for _, v := range values {
		if v != "" {
			return v
		}
	}
	return ""
}

func randomChoice(ss []string) string {
	if len(ss) == 0 {
		return ""
	}
	return ss[rand.Intn(len(ss))]
}
