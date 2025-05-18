# Flask1_04052025

## Инструкция по развертыванию проекта
1. Создать виртуальное окружение
```
python3 -m venv flask_venv
```
2. Активировать виртуальное окружение
```
source flask_venv/bin/activate
```
3. Установить нужные библиотеки
```
python -m pip install -r requirements.txt
```
4. Применить миграции
```
flask db migrate
```
5. Запустить приложение
```
python app.py
```

## Работа с sqlite3

1. Установка **CLI** для **sqlite**: 
```
sudo apt install sqlite3
```
2. Создать дамп БД (схема + данные): 
```
sqlite3 store.db .dump > db_sql/db_data.sql
```
3. Создать дамп БД (только схема): 
```
sqlite3 store.db ".schema quotes" > db_sql/db_schema.sql
```
4. Загрузить данные в БД: 
```
sqlite3 new_store.db ".read db_sql/db_data.sql"
```