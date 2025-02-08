package slovobor

import (
	"strings"
)

type TagsOpts struct {
	OnlyNoun     bool
	NoTopo       bool
	NoNomen      bool
	NotOffensive bool
	MinLength    int
}

func (db *DB) StringToTagLine(q string, opts ...TagsOpts) ([]byte, int) {
	var query []byte
	var total int = 0
	q = strings.ToLower(q)
	for i := 0; i < len(db.Tags); i++ {
		if db.Tags[i].Type == 0 {
			v := db.Tags[i].Value
			count := 0
			for _, c := range q {
				if string(c) == v {
					count += 1
				}
			}
			query = append(query, byte(count))
			total += count
		} else {
			query = append(query, 0)
		}
	}

	// magic tagging
	if len(opts) > 0 {
		if opts[0].MinLength > 0 {
			query[len(query)-4] = byte(opts[0].MinLength) // length
		}
		if opts[0].OnlyNoun {
			query[len(query)-3] = 78 // morph=N|V|A
			query[len(query)-2] = 2  // topo=false
			query[len(query)-1] = 2  // nomen=false
		}
	}

	return query, total
}
