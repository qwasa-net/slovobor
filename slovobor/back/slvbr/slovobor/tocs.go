package slovobor

import "encoding/binary"

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

func (db *DB) FindLineByTocFit(query []byte, recNo uint, pageNo uint) (int, uint, uint) {
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

		found, lineNo := db.FindLineFit(query, scanStart, scanCount)
		if found > 0 {
			return found, lineNo, i
		}
	}
	return 0, 0, 0

}

func (db *DB) FindAllLinesByTocFit(query []byte, pageNo uint, limit int) (int, []uint) {

	var tocRecs []uint = make([]uint, 0, 1000)
	tocFitLen := uint(db.Meta.TagLen * db.Meta.TagsCount)

	for i := uint(pageNo); i < uint(db.Meta.TOCCount); i++ {

		tocOff := uint(i) * uint(db.Meta.TOCLen)

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

		found, pageRecs := db.FindAllLinesFit(query, recNo, count, limit)
		if found > 0 {
			tocRecs = append(tocRecs, pageRecs...)
		}
		if limit > 0 && len(tocRecs) >= limit {
			break
		}
	}
	return len(tocRecs), tocRecs
}
