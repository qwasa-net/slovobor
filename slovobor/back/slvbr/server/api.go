package server

import (
	"encoding/json"
	"errors"
	"log"
	"net/http"
	"strconv"
	"strings"

	"slvbr.back/slovobor"
)

type qResponse struct {
	Query string `json:"q"`
	Count int    `json:"c"`
	Words string `json:"w"`
}

func (s *Server) qHandler(rsp http.ResponseWriter, req *http.Request) {

	if req.Method != http.MethodPost {
		http.Error(rsp, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	q, o, n, err := parseQForm(req, s.Config.ReqMin, s.Config.ReqMax)
	if err != nil {
		http.Error(rsp, "Bad request", http.StatusBadRequest)
		return
	}

	log.Printf("q=%s %d o=%d n=%d", q, len(q), o, n)

	opts := slovobor.TagsOpts{
		OnlyNoun:     n != 0,
		NotOffensive: o != 0,
		MinLength:    s.Config.RspMin,
	}

	var words []string

	for _, db := range s.Dbs {
		words = queryDB(&db, q, opts, s.Config.RspLimit)
		if words != nil {
			break
		}
	}

	data := qResponse{
		Query: q,
		Count: len(words),
		Words: strings.Join(words, ","),
	}

	rsp.Header().Set("Content-Type", "application/json")
	rsp.WriteHeader(http.StatusOK)
	json.NewEncoder(rsp).Encode(data)

}

func parseQForm(req *http.Request, qmin int, qmax int) (string, int, int, error) {

	var err error
	var q string
	var o int
	var n int

	req.Header.Set("Content-Type", "application/x-www-form-urlencoded") //
	err = req.ParseForm()
	if err != nil {
		return "", 0, 0, err
	}

	log.Println("form:", req.Form)

	q = req.FormValue("q")
	o, _ = strconv.Atoi(req.FormValue("o"))
	n, _ = strconv.Atoi(req.FormValue("n"))

	if q == "" || len(q) < qmin || len(q) > qmax {
		return "", 0, 0, errors.New("bad query")
	}

	return q, o, n, nil

}
