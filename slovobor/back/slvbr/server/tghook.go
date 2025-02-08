package server

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sort"
	"strings"
	"unicode"

	"slvbr.back/slovobor"
)

func (s *Server) tgHookHandler(rsp http.ResponseWriter, req *http.Request) {

	valid := s.validateTGHook(rsp, req)
	if !valid {
		return
	}

	msg := s.parseTGMessage(rsp, req)
	if msg == nil {
		return
	}

	real, query := s.parseTGMessageText(msg)
	log.Printf("tgHookHandler: real=%t query=%s", real, query)

	if !real {
		s.processTGHookHello(rsp, msg, query)
	} else {
		s.processTGHookQuery(rsp, msg, query)
	}

}

func (s *Server) validateTGHook(rsp http.ResponseWriter, req *http.Request) bool {
	// POST
	if req.Method != http.MethodPost {
		http.Error(rsp, "Method not allowed", http.StatusMethodNotAllowed)
		return false
	}
	// JSON
	if req.Header.Get("Content-Type") != "application/json" {
		http.Error(rsp, "Bad request", http.StatusBadRequest)
		return false
	}
	// Base webhook path
	if s.Config.TGHookPath != req.URL.Path[:len(s.Config.TGHookPath)] {
		http.Error(rsp, "Bad request", http.StatusBadRequest)
		return false
	}
	// Secret token
	botSecretToken := req.Header.Get("X-Telegram-Bot-Api-Secret-Token")
	if s.Config.TGHookToken != "" &&
		!(botSecretToken == s.Config.TGHookToken ||
			strings.Contains(req.URL.Path, s.Config.TGHookToken)) {
		http.Error(rsp, "Unauthorized", http.StatusUnauthorized)
		return false
	}
	return true
}

func (s *Server) parseTGMessage(rsp http.ResponseWriter, req *http.Request) *TGHookMessage {
	var update TGHookUpdate
	err := json.NewDecoder(req.Body).Decode(&update)
	if err != nil {
		http.Error(rsp, "Bad request", http.StatusBadRequest)
		return nil
	}
	msg := update.Message
	log.Printf("tgHookHandler: [%d %s %s %s] %s", msg.From.ID, msg.From.Username, msg.From.FirstName, msg.From.LastName, msg.Text)
	return &msg
}

func (s *Server) parseTGMessageText(msg *TGHookMessage) (bool, string) {
	query := strings.Map(func(r rune) rune {
		if unicode.IsLetter(r) || unicode.IsDigit(r) || r == '?' {
			return r
		}
		return -1
	}, msg.Text)

	real := (len(query) > 0 && query[0] == '?')
	if real {
		query = query[1:]
	}
	if len(query) > s.Config.ReqMax {
		query = query[:s.Config.ReqMax]
	}
	real = real && len(query) >= s.Config.ReqMin
	return real, query
}

func (s *Server) processTGHookHello(rsp http.ResponseWriter, msg *TGHookMessage, query string) {
	var reply string
	if query == "start" {
		reply = fmt.Sprintf(
			TG_HELLO,
			firstNonEmpty(msg.From.Username, msg.From.FirstName, fmt.Sprint(msg.From.ID)),
		)
	} else {
		reply = randomChoice(TG_MUMBLE)
	}
	hello := TGPostMessage{
		Method:    "sendMessage",
		ChatID:    msg.Chat.ID,
		Text:      reply,
		ReplyTo:   msg.MessageID,
		ParseMode: "Markdown",
	}
	rsp.Header().Set("Content-Type", "application/json")
	rsp.WriteHeader(http.StatusOK)
	payload, _ := json.Marshal(hello)
	rsp.Write(payload)
}

func (s *Server) processTGHookQuery(rsp http.ResponseWriter, msg *TGHookMessage, query string) {
	rsp.Header().Set("Content-Type", "application/json")
	rsp.WriteHeader(http.StatusOK)
	go s.processTGHookQueryBG(msg, query)
}

func (s *Server) processTGHookQueryBG(msg *TGHookMessage, query string) {
	opts := slovobor.TagsOpts{
		OnlyNoun:     true,
		NotOffensive: true,
		MinLength:    s.Config.RspMin,
	}
	var words []string
	for _, db := range s.Dbs {
		words = queryDB(&db, query, opts, s.Config.RspLimit)
		if words != nil {
			break
		}
	}
	sort.Slice(words, func(i, j int) bool { return !(len(words[i]) < len(words[j])) })
	data := qResponse{
		Query: query,
		Count: len(words),
		Words: strings.Join(words, ", "),
	}
	log.Printf(
		"processTGHookQueryBG: query=%s count=%d words=%.255s\n",
		query,
		len(words),
		data.Words,
	)
	s.postTGResponse(msg, data)
}

func (s *Server) postTGResponse(msg *TGHookMessage, data qResponse) {

	var text string
	if data.Count == 0 {
		text = randomChoice(TG_NOTHING_FOUND)
	} else {
		if len(data.Words) > 4084 {
			data.Words = data.Words[:4084]
		}
		text = fmt.Sprintf("%s _(%d)_", data.Words, data.Count)
	}
	if len(text) > 4096 {
		text = text[:4096]
	}
	tgrsp := TGPostMessage{
		Method:    "sendMessage",
		ChatID:    msg.Chat.ID,
		ReplyTo:   msg.MessageID,
		Text:      text,
		ParseMode: "Markdown",
	}
	sendTGMessage(s.Config.TGBotToken, &tgrsp)

}
