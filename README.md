# Словобор

## Подготовка базы

1. Скачивание дампа википедии
[dumps.wikimedia.org](https://dumps.wikimedia.org/ruwiktionary/latest/)


2. Преобразование дампа в json

```
> python3 slovobor/tools/dbbuilder/parse_ruwiktionary_to_json.py \
    --lang ru \
    data/src/ruwiktionary-pages-articles-multistream.xml.bz2 \
    data/src/ruwiktionary-parsed-ru.json
```

3. Компиляция базы (slvBR)

```
python3 slovobor/tools/dbbuilder/dbcompiler.py  \
    --min-length 2 --morph NVA \
    --tags-language ru \
    --best-tag-order \
    --encoding cp1251 \
    data/src/ruwiktionary-parsed-ru.json.bz2 \
    data/ru.slvbr.db
```

## Сборка переборщика

```
> cd slovobor/back/slvbr
> go build -v -ldflags="-s -w" -o slvbr.back .
```


## Использование

```
> ./slvbr.back -db data/ru.slvbr.db -query "вечность"
2000/01/02 01:23:45 loadDataBase data/ru.slvbr.db
2000/01/02 01:23:45 magic: !slvBR version=1
…
2000/01/02 01:23:45 QueryRecordFitAll found 107 results in 769.718µs

… осень сочень … отсечь советь востечь тень Неть новеть стень вечность

```

