FROM mysql

ENV MYSQL_ROOT_PASSWORD psw123
ADD ./init_db /docker-entrypoint-initdb.d
EXPOSE 3306