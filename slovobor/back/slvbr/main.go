package main

import (
	"fmt"
	"log"
	"os"
	"time"

	"slvbr.back/server"
	"slvbr.back/slovobor"
)

type Config struct {
	DBPaths      []string      `flag:"db" env:"DB_PATHS" default:""`
	Query        string        `flag:"query" default:""`
	Demo         bool          `flag:"demo" default:"false" usage:"run demo"`
	Server       bool          `flag:"server" default:"false" usage:"run http server"`
	ServerConfig server.Config `flag:"server"`
}

func main() {

	var cfg Config
	readConfig(&cfg)
	log.Println(cfg)

	var dbs []slovobor.DB
	for _, dbPath := range cfg.DBPaths {
		db := loadDataBase(dbPath)
		dbs = append(dbs, *db)
	}

	if cfg.Query != "" {
		doQuery(dbs, cfg)
	}

	if cfg.Demo {
		doDemo(dbs, cfg)
	}

	if cfg.Server {
		runServer(dbs, cfg)
	}

}

func loadDataBase(dbPath string) *slovobor.DB {

	log.Println("loadDataBase", dbPath)

	file, err := os.Open(dbPath)
	if err != nil {
		log.Fatalf("failed to open file: %s", err)
	}
	defer file.Close()

	db := slovobor.ReadDataFile(file)

	return db
}

func doDemo(dbs []slovobor.DB, cfg Config) {
	for _, db := range dbs {
		doDemoDB(&db)
	}
}

func runServer(dbs []slovobor.DB, cfg Config) {
	s := server.Server{
		Dbs:    dbs,
		Config: cfg.ServerConfig,
	}
	s.Run()
}

func doQuery(dbs []slovobor.DB, cfg Config) {
	for _, db := range dbs {
		queryLine, _ := db.StringToTagLine(cfg.Query)
		log.Println("=== QueryRecordFitAll", time.Now())
		startTm := time.Now()
		foundCount, foundAll := db.QueryTocFitAll(queryLine, 0, 0)
		endTm := time.Now()
		log.Printf("QueryRecordFitAll found %d results in %v\n", foundCount, endTm.Sub(startTm))

		for i := 0; i < foundCount; i++ {
			txt := db.GetRecordText(foundAll[i])
			fmt.Print(txt, " ")
		}
		fmt.Println()
	}
}
