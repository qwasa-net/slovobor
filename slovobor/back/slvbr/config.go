package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"reflect"
	"strconv"
	"strings"
)

func readConfig(cfg interface{}) {
	parseFlags(cfg, "")
	flag.Parse()
}

func parseFlags(cfg interface{}, prefix string) {

	v := reflect.ValueOf(cfg).Elem()
	t := v.Type()

	for i := 0; i < v.NumField(); i++ {

		field := v.Field(i)

		fieldType := t.Field(i)

		flagName := fieldType.Tag.Get("flag")
		if prefix != "" {
			flagName = prefix + "-" + flagName
		}

		usage := fieldType.Tag.Get("usage")

		defaultValue := fieldType.Tag.Get("default")

		// DEFAULT -> ENV -> FLAG
		envName := fieldType.Tag.Get("env")
		if envName != "" {
			if prefix != "" {
				envName = strings.ToUpper(prefix) + "_" + envName
			}
			if envValue, exists := getEnvValue(envName); exists {
				defaultValue = envValue
			}
			usage += " (env: " + envName + ")"
		}

		switch field.Kind() {

		case reflect.String:
			flag.StringVar(field.Addr().Interface().(*string), flagName, defaultValue, usage)

		case reflect.Int:
			defaultIntValue, _ := strconv.Atoi(defaultValue)
			flag.IntVar(field.Addr().Interface().(*int), flagName, defaultIntValue, usage)

		case reflect.Bool:
			defaultBoolValue, _ := strconv.ParseBool(defaultValue)
			flag.BoolVar(field.Addr().Interface().(*bool), flagName, defaultBoolValue, usage)

		case reflect.Struct:
			parseFlags(field.Addr().Interface(), flagName)

		case reflect.Slice:
			var sep string = fieldType.Tag.Get("sep")
			if sep == "" {
				sep = ","
			}
			var values []string = strings.Split(defaultValue, sep)
			field.Set(reflect.ValueOf(values))
			fmt.Println(flagName, values, sep)
			flag.Func(flagName, "", func(value string) error {
				values = append(values, value)
				field.Set(reflect.ValueOf(values))
				return nil
			})

		default:
			log.Fatalln("unsupported type config", field.Kind())
		}

	}
}

func getEnvValue(envName string) (string, bool) {
	if envName == "" {
		return "", false
	}
	_, ok := os.LookupEnv(envName)
	if !ok {
		return "", false
	}
	return os.Getenv(envName), true
}
