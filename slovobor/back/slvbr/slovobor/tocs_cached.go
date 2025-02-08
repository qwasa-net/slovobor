package slovobor

import (
	"hash/crc64"
	"log"
	"sync"
)

var searchCacheMx sync.Mutex
var searchCacheLimit = 1 * 1024
var searchCache = make(map[uint64]interface{}, searchCacheLimit)

func (db *DB) FindAllLinesByTocFitCached(query []byte, pageNo uint, limit int) (int, []uint, bool) {

	searchCacheMx.Lock()
	defer searchCacheMx.Unlock()
	var records []uint

	key := makeCacheKey(query, pageNo, limit)
	if cached, found := searchCache[key]; found {
		records := cached.([]uint)
		log.Printf("cache hit key=%x, len=%d cached=%d\n", key, len(records), len(searchCache))
		return len(records), records, true
	}

	length, records := db.FindAllLinesByTocFit(query, pageNo, limit)
	if length > 0 && len(searchCache) < searchCacheLimit {
		searchCache[key] = records
		log.Printf("cache miss key=%x, len=%d cached=%d\n", key, len(records), len(searchCache))
	}

	return length, records, false
}

func makeCacheKey(query []byte, pageNo uint, limit int) uint64 {
	hasher := crc64.New(crc64.MakeTable(crc64.ISO))
	hasher.Write(query)
	hasher.Write([]byte{byte(pageNo >> 24), byte(pageNo >> 16), byte(pageNo >> 8), byte(pageNo)})
	hasher.Write([]byte{byte(limit >> 24), byte(limit >> 16), byte(limit >> 8), byte(limit)})
	return hasher.Sum64()
}
