# test
## Требования
Требования внутри requirements.me

## env
необходимо после скачивания репозитория создать файл .env куда надо добавить
- BDUSER
- BDPASSWORD
- DATABASE=test (при изменении также необходимо изменить в alembic.ini)
- SECRET_KEY=secretkey123
- ALGORITHM=HS256
- BASE_URL=http://127.0.0.1:8000
- GMAILPASSWORD=azahprlgbfkrlecq
- GMAIL=qweadszcx07@gmail.com
- POSTGRES_USER (повторение предыдущего, я забыл где какие данные я вставлял и для точночти добавил эти поля)
- POSTGRES_PASSWORD
- POSTGRES_DB=test
- DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@хост:порт/${POSTGRES_DB}
