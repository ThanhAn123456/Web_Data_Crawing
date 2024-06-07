#! /usr/bin/bash 
# docker-compose up --build -d
# docker build -t test_mysql:0.1 ./mysql
# docker run -d --name=test_mysql_container --publish 3306:3306 test_mysql:0.1
# docker build -t test_craw:0.1 ./data_crawling
# docker run -d --name=test_craw_container --publish 5000:5000 test_craw:0.1
# docker build -t test_db_api:0.1 ./db_api
# docker run -d --name=test_db_api_container --publish 5001:5001 test_db_api:0.1
./remove_all.sh
docker-compose up --build -d
