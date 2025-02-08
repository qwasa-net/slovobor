package slovobor

import (
	"encoding/binary"
	"fmt"
	"log"
	"strings"

	"golang.org/x/text/encoding"
	"golang.org/x/text/transform"
)

type DB struct {
	Meta       *DBHeader
	Tags       []Tag
	LinesIndex []byte
	Bog        []byte
	Toc        []byte
	Decoder    *encoding.Decoder
}

type Tag struct {
	Type  int16
	Value string
}

func (t *Tag) Fit(a byte, b byte) bool {
	if t.Type == 0 {
		return a >= b
	}
	if t.Type == 1 {
		return a == 0 || a <= b
	}
	if t.Type == 2 {
		return a == 0 || a == b
	}
	if t.Type == 3 {
		return a == 0 || a == b
	}
	return true
}

type MagicCode struct {
	Magic   [6]byte
	Version int16
}

type DBHeader struct {
	Magic          MagicCode
	Title          [128]byte
	Encoding       [8]byte
	MagicHeaderLen uint32
	LinesCount     uint32
	LineLen        uint32
	TagsCount      uint32
	TagLen         uint32
	TagTypeLen     uint32
	TagValueLen    uint32
	LineDataLen    uint32
	BogLen         uint32
	TOCLen         uint32
	TOCCount       uint32
}

type Line struct {
	Tagline []byte
	Data    []byte
}

func (db *DB) Show() {
	log.Printf("tags: %d\n", len(db.Tags))
	for i, tag := range db.Tags {
		fmt.Printf("%s[%d]; ", tag.Value, tag.Type)
		if i%20 == 19 || i == len(db.Tags)-1 {
			fmt.Println()
		}
	}
	log.Printf("lines: %d\n", db.Meta.LinesCount)
	for i := uint(0); i < 10; i++ {
		ii := uint(db.Meta.LinesCount)/3 + i
		fits, body, txt := db.GetRecordValues(ii)
		fmt.Printf("[%3d] %x %x %s\n", ii, fits, body, txt)
	}
	pages, lines := db.CountTOC()
	log.Printf("toc: %d÷%d\n", lines, pages)
	log.Printf("bog: %d (%.2fMB)\n", len(db.Bog), float64(len(db.Bog))/(1024*1024))
}

func (db *DB) GetTitle() string {
	return string(db.Meta.Title[:])
}

func (db *DB) GetRecord(recNo int) []byte {
	if recNo >= int(db.Meta.LinesCount) {
		return nil
	}
	start := recNo * int(db.Meta.LineLen)
	end := start + int(db.Meta.LineLen)
	return db.LinesIndex[start:end]
}

func (db *DB) GetRecordValues(recNo uint) ([]byte, []byte, string) {
	if recNo >= uint(db.Meta.LinesCount) {
		return nil, nil, ""
	}
	var txt string
	start := recNo * uint(db.Meta.LineLen)
	end1 := start + uint(db.Meta.TagLen*db.Meta.TagsCount)
	end := start + uint(db.Meta.LineLen)
	fitters := db.LinesIndex[start:end1]
	body := db.LinesIndex[end1:end]
	if len(body) >= 8 {
		data_ptr := binary.LittleEndian.Uint32(body[:4])
		data_len := binary.LittleEndian.Uint32(body[4:8])
		if data_ptr+data_len <= db.Meta.BogLen {
			data := db.Bog[data_ptr : data_ptr+data_len]
			txt, _, _ = transform.String(db.Decoder, string(data))
		}
	}

	return fitters, body, txt
}

func (db *DB) GetRecordText(recNo uint) string {
	if recNo >= uint(db.Meta.LinesCount) {
		return ""
	}
	var txt string
	start := recNo * uint(db.Meta.LineLen)
	start_body := start + uint(db.Meta.TagLen*db.Meta.TagsCount)
	data_ptr := binary.LittleEndian.Uint32(db.LinesIndex[start_body : start_body+4])
	data_len := binary.LittleEndian.Uint32(db.LinesIndex[start_body+4 : start_body+8])
	if data_ptr+data_len <= db.Meta.BogLen {
		data := db.Bog[data_ptr : data_ptr+data_len]
		txt, _, _ = transform.String(db.Decoder, string(data))
	}
	return txt
}

func (db *DB) QueryRecordFit(query []byte, start uint, len uint) (int, uint) {
	var stop uint
	if len == 0 {
		stop = uint(db.Meta.LinesCount)
	} else {
		stop = min(start+len, uint(db.Meta.LinesCount))
	}
	queryLen := uint(db.Meta.TagsCount)
	for i := start; i < stop; i++ {
		recOff := i * uint(db.Meta.LineLen)
		match := true
		for j := uint(0); j < queryLen; j++ {
			fit := db.Tags[j].Fit(query[j], db.LinesIndex[recOff+j])
			if !fit {
				match = false
				break
			}
		}
		if match {
			return 1, i
		}
	}
	return 0, 0
}

func (db *DB) QueryRecordFitAll(query []byte, start uint, length uint, limit int) (int, []uint) {
	var found = make([]uint, 0, 1000)
	var stop uint
	if length == 0 {
		stop = uint(db.Meta.LinesCount)
	} else {
		stop = min(start+length, uint(db.Meta.LinesCount))
	}
	queryLength := uint(db.Meta.TagsCount)
	for i := start; i < stop; i++ {
		recOff := i * uint(db.Meta.LineLen)
		match := true
		for j := uint(0); j < queryLength; j++ {
			fit := db.Tags[j].Fit(query[j], db.LinesIndex[recOff+j])
			if !fit {
				match = false
				break
			}
		}
		if match {
			found = append(found, i)
		}
		if limit > 0 && len(found) >= limit {
			break
		}
	}
	return len(found), found
}

func (db *DB) CountTOC() (uint, uint) {
	var pages uint = 0
	var records uint = 0
	for i := uint(0); i < uint(db.Meta.TOCCount); i++ {
		tocOff := i * uint(db.Meta.TOCLen)
		tocFitLen := uint(db.Meta.TagLen) * uint(db.Meta.TagsCount)
		count := uint(binary.LittleEndian.Uint32(db.Toc[tocOff+tocFitLen+4 : tocOff+tocFitLen+8]))
		records += count
		pages += 1
	}
	return pages, records
}

func queryFits(query []byte, fits []byte, fitters []Tag, len int) (bool, int, int) {
	c := 0
	for j := int(0); j < int(len); j++ {
		c += 1
		if fitters[j].Type == 0 {
			if query[j] < fits[j] {
				return false, j, c
			}
		}
	}
	return true, -1, c
}

func (db *DB) QueryTocFit(query []byte, recNo uint, pageNo uint) (int, uint, uint) {
	tocFitLen := uint(db.Meta.TagLen * db.Meta.TagsCount)
	skipPageFit := pageNo > 0 || recNo > 0
	for i := uint(pageNo); i < uint(db.Meta.TOCCount); i++ {
		tocOff := uint(i) * uint(db.Meta.TOCLen)

		if !skipPageFit {
			pageFits := true
			for j := uint(0); j < tocFitLen; j++ {
				if db.Tags[j].Type == 0 {
					if query[j] < db.Toc[tocOff+j] {
						pageFits = false
						break
					}
				}
			}

			if !pageFits {
				continue
			}
		}

		tocNo := uint(binary.LittleEndian.Uint32(db.Toc[tocOff+tocFitLen : tocOff+tocFitLen+4]))
		count := uint(binary.LittleEndian.Uint32(db.Toc[tocOff+tocFitLen+4 : tocOff+tocFitLen+8]))
		scanCount := min(count, count-(recNo-tocNo))
		if scanCount <= 0 {
			continue
		}
		scanStart := max(tocNo, recNo)

		found, lineNo := db.QueryRecordFit(query, scanStart, scanCount)
		if found > 0 {
			return found, lineNo, i
		}
	}
	return 0, 0, 0

}

func (db *DB) QueryTocFitAll(query []byte, pageNo uint, limit int) (int, []uint) {

	var tocRecs []uint = make([]uint, 0, 1000)

	for i := uint(pageNo); i < uint(db.Meta.TOCCount); i++ {

		tocOff := uint(i) * uint(db.Meta.TOCLen)
		tocFitLen := uint(db.Meta.TagLen * db.Meta.TagsCount)

		pageFits := true

		for j := uint(0); j < tocFitLen; j++ {
			if db.Tags[j].Type == 0 {
				if query[j] < db.Toc[tocOff+j] {
					pageFits = false
					break
				}
			}
		}
		if !pageFits {
			continue
		}

		recNo := uint(binary.LittleEndian.Uint32(db.Toc[tocOff+tocFitLen : tocOff+tocFitLen+4]))
		count := uint(binary.LittleEndian.Uint32(db.Toc[tocOff+tocFitLen+4 : tocOff+tocFitLen+8]))

		found, pageRecs := db.QueryRecordFitAll(query, recNo, count, limit)
		if found > 0 {
			tocRecs = append(tocRecs, pageRecs...)
		}
		if limit > 0 && len(tocRecs) >= limit {
			break
		}
	}
	return len(tocRecs), tocRecs
}

func (db *DB) PostInit() {
}

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
