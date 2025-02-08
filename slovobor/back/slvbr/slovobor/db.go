package slovobor

import (
	"encoding/binary"
	"fmt"
	"log"

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
		fits, body, txt := db.GetLineValues(ii)
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

func (db *DB) GetLineValues(recNo uint) ([]byte, []byte, string) {
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

func (db *DB) GetLineText(recNo uint) string {
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

func (db *DB) FindLineFit(query []byte, start uint, len uint) (int, uint) {
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

func (db *DB) FindAllLinesFit(query []byte, start uint, length uint, limit int) (int, []uint) {
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

func (db *DB) PostInit() {
}
