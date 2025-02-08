package main

import (
	"fmt"
	"time"

	"slvbr.back/slovobor"
)

func doDemoDB(db *slovobor.DB) {

	fmt.Println("=== Demo", db.GetTitle(), time.Now())

	fmt.Println()
	db.Show()
	fmt.Println()

	query_word := "вечность"
	query_line, _ := db.StringToTagLine(
		query_word,
		slovobor.TagsOpts{
			OnlyNoun:     true,
			NoTopo:       true,
			NoNomen:      true,
			NotOffensive: true,
			MinLength:    4,
		},
	)
	// query_line, _, _ := db.GetLineValues(uint(db.Metadata.RecordsCount) / 2)
	// query_line := []byte{1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0}
	fmt.Println("Query:", query_word, query_line)

	var tm_a, tm_b time.Time
	var ids []uint
	var fc int

	fmt.Println("=== FindAllLinesFit =>", time.Now())
	tm_a = time.Now()
	fc, ids = db.FindAllLinesFit(query_line, 0, 0, 0)
	tm_b = time.Now()
	fmt.Println("=== FindAllLinesFit =>", fc, len(ids), tm_b.Sub(tm_a))
	for i := uint(fc / 4); i < min(uint(fc), uint(fc/4+10)); i++ {
		fmt.Printf("[%d]=%s ", uint(ids[i]), db.GetLineText(uint(ids[i])))
	}
	fmt.Println()

	fmt.Println("=== for { FindLineFit }", time.Now())
	recNo := uint(0)
	fc = 0
	ids = make([]uint, 0, 10_000)
	tm_a = time.Now()
	for {
		found, rNo := db.FindLineFit(query_line, recNo, 0)
		if found <= 0 {
			break
		}
		ids = append(ids, uint(rNo))
		fc += 1
		recNo = rNo + 1
	}
	tm_b = time.Now()
	fmt.Println("=== for { FindLineFit } =>", fc, len(ids), tm_b.Sub(tm_a))
	for i := uint(fc / 4); i < min(uint(fc), uint(fc/4+10)); i++ {
		fmt.Printf("[%d]=%s ", uint(ids[i]), db.GetLineText(uint(ids[i])))
	}
	fmt.Println()

	fmt.Println("=== for { FindLineByTocFit }", time.Now())
	recNo = 0
	pageNo := uint(0)
	fc = 0
	ids = make([]uint, 0, 10_000)
	tm_a = time.Now()
	for {
		found, rNo, pgNo := db.FindLineByTocFit(query_line, recNo, pageNo)
		if found <= 0 {
			break
		}
		ids = append(ids, uint(rNo))
		fc += 1
		recNo = rNo + 1
		pageNo = pgNo
	}
	tm_b = time.Now()
	fmt.Println("=== for { FindLineByTocFit } =>", fc, len(ids), tm_b.Sub(tm_a))
	for i := uint(fc / 4); i < min(uint(fc), uint(fc/4+10)); i++ {
		fmt.Printf("[%d]=%s ", uint(ids[i]), db.GetLineText(uint(ids[i])))
	}
	fmt.Println()

	fmt.Println("=== FindAllLinesByTocFit", time.Now())
	tm_a = time.Now()
	fc, ids = db.FindAllLinesByTocFit(query_line, 0, 0)
	tm_b = time.Now()
	fmt.Println("=== FindAllLinesByTocFit =>", fc, len(ids), tm_b.Sub(tm_a))
	for i := uint(fc / 4); i < min(uint(fc), uint(fc/4+10)); i++ {
		fmt.Printf("[%d]=%s ", uint(ids[i]), db.GetLineText(uint(ids[i])))
	}
	fmt.Println()

	var cached bool
	for i := 0; i < 3; i++ {
		fmt.Println("=== FindAllLinesByTocFitCached", time.Now())
		tm_a = time.Now()
		fc, ids, cached = db.FindAllLinesByTocFitCached(query_line, 0, 0)
		tm_b = time.Now()
		fmt.Println("=== FindAllLinesByTocFitCached =>", fc, len(ids), tm_b.Sub(tm_a), cached)
		for i := uint(fc / 4); i < min(uint(fc), uint(fc/4+10)); i++ {
			fmt.Printf("[%d]=%s ", uint(ids[i]), db.GetLineText(uint(ids[i])))
		}
		fmt.Println()
	}

}
