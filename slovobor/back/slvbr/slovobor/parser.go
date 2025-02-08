package slovobor

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"io"
	"log"
	"os"
	"strings"

	"golang.org/x/text/transform"
)

func ReadDataFile(file *os.File) *DB {

	var err error
	var db DB

	var metadata *DBHeader
	var tags []Tag

	metadata, tags, err = readHeader(file)
	if err != nil {
		log.Fatalf("Error reading metadata: %s", err)
	}
	db.Meta = metadata
	db.Tags = tags

	//
	log.Printf("magic: %s version=%d\n", string(metadata.Magic.Magic[:]), metadata.Magic.Version)
	log.Printf("name: %s\n", string(metadata.Title[:]))
	log.Printf("encoding: %s\n", string(metadata.Encoding[:]))
	log.Printf("lines: %d×%d\n", metadata.LinesCount, metadata.LineLen)
	log.Printf("tags: %d×%d\n", metadata.TagsCount, metadata.TagLen)
	log.Printf("line data len: %d\n", metadata.LineDataLen)
	log.Printf("bog len: %d\n", metadata.BogLen)
	log.Printf("toc: %d×%d\n", metadata.TOCCount, metadata.TOCLen)

	var index []byte
	index, err = readLines(file, metadata)
	if err != nil {
		log.Fatalf("Error reading records: %s", err)
	}
	db.LinesIndex = index

	var bog []byte
	bog, _ = readBog(file, metadata)
	db.Bog = bog

	var toc []byte
	toc, _ = readToc(file, metadata)
	db.Toc = toc

	charset := strings.ToLower(string(bytes.Trim(metadata.Encoding[:], "\x00")))
	db.Decoder = CreateDecoderByCharset(charset)

	db.PostInit()

	return &db
}

func readHeader(file *os.File) (*DBHeader, []Tag, error) {

	startPosition := 0
	_, err := file.Seek(int64(startPosition), io.SeekStart)
	if err != nil {
		return nil, nil, err
	}

	metadata := &DBHeader{}
	err = binary.Read(file, binary.LittleEndian, metadata)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to read metadata: %w", err)
	}
	if metadata.Magic.Magic != [6]byte{'!', 's', 'l', 'v', 'B', 'R'} || metadata.Magic.Version != 0x0001 {
		return nil, nil, fmt.Errorf("invalid magic header: %x", metadata.Magic.Magic)
	}

	charset := strings.ToLower(string(bytes.Trim(metadata.Encoding[:], "\x00")))
	decoder := CreateDecoderByCharset(charset)

	// Read the tags
	tags := make([]Tag, metadata.TagsCount)
	for i := 0; i < int(metadata.TagsCount); i++ {

		tagType := make([]byte, metadata.TagTypeLen)
		file.Read(tagType)

		tagValueRaw := make([]byte, metadata.TagValueLen)
		file.Read(tagValueRaw)
		tagValueRaw = bytes.Trim(tagValueRaw, "\x00")
		tagValue, _, _ := transform.String(decoder, string(tagValueRaw))

		tags[i] = Tag{
			Type:  int16(binary.LittleEndian.Uint16(tagType)),
			Value: tagValue,
		}
	}

	return metadata, tags, nil
}

func readLines(file *os.File, metadata *DBHeader) ([]byte, error) {

	startPosition := metadata.MagicHeaderLen
	_, err := file.Seek(int64(startPosition), io.SeekStart)
	if err != nil {
		return nil, err
	}

	index := make([]byte, metadata.LinesCount*metadata.LineLen)
	n, err := file.Read(index)
	if err != nil && err != io.EOF {
		return nil, err
	}
	if n != int(metadata.LinesCount*metadata.LineLen) {
		return nil, fmt.Errorf("failed to read full index: %w", err)
	}

	return index, nil
}

func readBog(file *os.File, metadata *DBHeader) ([]byte, error) {

	startPosition := 1024 + metadata.LinesCount*metadata.LineLen
	_, err := file.Seek(int64(startPosition), io.SeekStart)
	if err != nil {
		return nil, err
	}

	bog := make([]byte, metadata.BogLen)
	n, err := file.Read(bog)
	if err != nil && err != io.EOF {
		return nil, err
	}
	if n != int(metadata.BogLen) {
		return nil, fmt.Errorf("failed to read full bog: %w", err)
	}
	return bog, nil
}

func readToc(file *os.File, metadata *DBHeader) ([]byte, error) {

	startPosition := metadata.MagicHeaderLen + metadata.LinesCount*metadata.LineLen + metadata.BogLen
	_, err := file.Seek(int64(startPosition), io.SeekStart)
	if err != nil {
		return nil, err
	}

	tocLen := metadata.TOCCount * metadata.TOCLen
	toc := make([]byte, tocLen)
	n, err := file.Read(toc)
	if err != nil && err != io.EOF {
		return nil, err
	}
	if n != int(tocLen) {
		return nil, fmt.Errorf("failed to read full toc: %w", err)
	}

	return toc, nil
}
