# bookshop
bookshop

Book inventory management test sample

## Prerequisite

1. docker
2. docker-compose

## Installation

Clone the repository:

```
git clone https://github.com/rocky2015aaa/bookshop.git
```

## Usage

```
make
```

## API Reference

Check `openapi.yaml`

- Ping
```
curl --location 'localhost:8000/ping'
```
- Author
```
curl --location 'localhost:8000/author' \
--header 'Content-Type: application/json' \
--data '{
  "name": "test author 2",
  "birth_date": "1980-11-11"
}'

curl --location 'localhost:8000/author/{author_id}'
```
- Book
```  
curl --location 'localhost:8000/book' \
--header 'Content-Type: application/json' \
--data '{
    "barcode": "14810", "title": "test book6", "publish_year": 2000,
    "author": 2
}'

curl --location 'localhost:8000/book/3'

curl --location 'localhost:8000/book?barcode=15'

```
- Inventory (Storing Information)
```
curl --location 'http://localhost:8000/leftover/add' \
--header 'Content-Type: application/json' \
--data '{
  "barcode": "1111238",
  "quantity": 8
}'

curl --location 'http://localhost:8000/leftover/remove' \
--header 'Content-Type: application/json' \
--data '{
  "barcode": "14810",
  "quantity": 1
}'

curl --location 'http://localhost:8000/leftover/bulk' \
--header 'Content-Type: multipart/form-data' \
--form 'file=@"/Users/donggeon/Downloads/txt_example.txt"'

curl --location 'http://localhost:8000/leftover/bulk' \
--header 'Content-Type: multipart/form-data' \
--form 'file=@"/Users/donggeon/Downloads/txt_example.txt"'

curl --location 'localhost:8000/history?start=2014-01-01&end=2024-02-02&book=1'

curl --location 'localhost:8000/history
: This case sets start and end for today date and check all book
```














