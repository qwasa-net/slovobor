package main

import (
	"fmt"
	"time"

	"slvbr.back/slovobor"
)

// query_line, _, _ := db.GetLineValues(uint(db.Metadata.RecordsCount) / 2)
// query_line := []byte{1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0}
// query_line := []byte{1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}

func doDemoDB(db *slovobor.DB) {

	fmt.Println("=== Demo", db.GetTitle(), time.Now())
	db.Show()

	query_word := "вечность"
	query_line, _ := db.StringToTagLine(query_word)
	query_line[len(query_line)-4] = 0
	query_line[len(query_line)-3] = 0
	query_line[len(query_line)-2] = 0
	query_line[len(query_line)-1] = 0
	fmt.Println("Query:", query_word, query_line)

	var tm_a, tm_b time.Time
	var ids []uint
	var fc int

	fmt.Println("=== QueryRecordFitAll >", time.Now())
	tm_a = time.Now()
	fc, ids = db.QueryRecordFitAll(query_line, 0, 0, 0)
	tm_b = time.Now()
	fmt.Println("=== QueryRecordFitAll >", fc, len(ids), tm_b.Sub(tm_a))
	for i := uint(fc / 2); i < min(uint(fc), uint(fc/2+10)); i++ {
		txt := db.GetRecordText(uint(ids[i]))
		fmt.Printf("[%d]=%s ", uint(ids[i]), txt)
	}
	fmt.Println()

	fmt.Println("=== for { QueryRecordFit }", time.Now())
	recNo := uint(0)
	fc = 0
	ids = make([]uint, 0, 10_000)
	tm_a = time.Now()
	for {
		found, rNo := db.QueryRecordFit(query_line, recNo, 0)
		if found <= 0 {
			break
		}
		ids = append(ids, uint(rNo))
		fc += 1
		recNo = rNo + 1
	}
	tm_b = time.Now()
	fmt.Println("=== for { QueryRecordFit } >", fc, len(ids), tm_b.Sub(tm_a))
	for i := uint(fc / 2); i < min(uint(fc), uint(fc/2+10)); i++ {
		txt := db.GetRecordText(uint(ids[i]))
		fmt.Printf("[%d]=%s ", uint(ids[i]), txt)
	}
	fmt.Println()

	fmt.Println("=== for { QueryTocFit }", time.Now())
	recNo = 0
	pageNo := uint(0)
	fc = 0
	ids = make([]uint, 0, 10_000)
	tm_a = time.Now()
	for {
		found, rNo, pgNo := db.QueryTocFit(query_line, recNo, pageNo)
		if found <= 0 {
			break
		}
		ids = append(ids, uint(rNo))
		fc += 1
		recNo = rNo + 1
		pageNo = pgNo
	}
	tm_b = time.Now()
	fmt.Println("=== for { QueryTocFit } >", fc, len(ids), tm_b.Sub(tm_a))
	for i := uint(fc / 2); i < min(uint(fc), uint(fc/2+10)); i++ {
		txt := db.GetRecordText(uint(ids[i]))
		fmt.Printf("[%d]=%s ", uint(ids[i]), txt)
	}
	fmt.Println()

	fmt.Println("=== QueryTocFitAll", time.Now())
	tm_a = time.Now()
	tm_a = time.Now()
	fc, ids = db.QueryTocFitAll(query_line, 0, 999)
	tm_b = time.Now()
	fmt.Println("=== QueryTocFitAll >", fc, len(ids), tm_b.Sub(tm_a))
	for i := uint(fc / 2); i < min(uint(fc), uint(fc/2+10)); i++ {
		txt := db.GetRecordText(uint(ids[i]))
		fmt.Printf("[%d]=%s ", uint(ids[i]), txt)
	}
	fmt.Println()

}
