package slovobor

import (
	"log"

	"golang.org/x/text/encoding"
	"golang.org/x/text/encoding/charmap"
)

func CreateDecoderByCharset(charset string) *encoding.Decoder {
	var decoder *encoding.Decoder
	switch charset {
	case "utf-8", "utf8", "ascii":
		decoder = encoding.Nop.NewDecoder()
	case "cp1251", "windows-1251":
		decoder = charmap.Windows1251.NewDecoder()
	case "windows-1252", "cp1252":
		decoder = charmap.Windows1252.NewDecoder()
	case "koi8-r":
		decoder = charmap.KOI8R.NewDecoder()
	case "iso-8859-1", "latin1":
		decoder = charmap.ISO8859_1.NewDecoder()
	default:
		log.Fatalf("Unknown charset: %s\n", charset)
	}
	return decoder
}
