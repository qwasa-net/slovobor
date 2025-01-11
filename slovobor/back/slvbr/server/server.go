package server

import (
	"fmt"
	"log"
	"net/http"
	"time"

	"slvbr.back/slovobor"
)

type Config struct {
	ReqMin      int    `flag:"query-min" default:"3"`
	ReqMax      int    `flag:"query-max" default:"100"`
	RspMin      int    `flag:"rsp-min" default:"3"`
	RspLimit    int    `flag:"rsp-limit" default:"1000"`
	Port        int    `flag:"listen-port" env:"LISTEN_PORT" default:"8080"`
	Host        string `flag:"listen-host" env:"LISTEN_HOST" default:"localhost"`
	QPath       string `flag:"q-path" default:"/q"`
	TGBotToken  string `flag:"tg-bot-token" env:"TG_BOT_TOKEN" default:""`
	TGHookPath  string `flag:"tg-path" env:"TG_HOOK_PATH" default:"/tgbot_webhook/"`
	TGHookToken string `flag:"tg-hook-token" env:"TG_HOOK_TOKEN" default:""`
}

type Server struct {
	Dbs    []slovobor.DB
	Config Config
}

func (s *Server) Run() {

	listen := fmt.Sprintf("%s:%d", s.Config.Host, s.Config.Port)
	log.Printf("Server started on %s ...", listen)

	mux := http.NewServeMux()
	mux.HandleFunc("POST "+s.Config.QPath, s.qHandler)
	mux.HandleFunc("POST "+s.Config.TGHookPath, s.tgHookHandler)

	logMux := s.loggingMiddleware(mux)
	http.ListenAndServe(listen, logMux)

}

func (s *Server) loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(rsp http.ResponseWriter, req *http.Request) {
		realIp := req.Header.Get("X-Real-IP")
		if realIp == "" {
			realIp = req.RemoteAddr
		}
		start := time.Now()
		next.ServeHTTP(rsp, req)
		log.Printf("[%s] %s %s %s", realIp, req.Method, req.RequestURI, time.Since(start))
	})
}
