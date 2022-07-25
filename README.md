![yamdb_workflow](https://github.com/Nizzerato/foodgram-project-react/actions/workflows/main.yml/badge.svg)

# Foodgram

## Описание проекта

- Проект Foodgram позволяет создавать, редактировать добавлять в избранное, делиться и скачивать рецепты. Помимо этого, можено так же подписываться на авторов, следить за рецептами, которые они добавляют и самому их выкладывать, в том числе.

# Доступность проекта

- Проект доступен по адресу: 51.250.101.1
(Логин(эл.почта) админа: admin@admin.ru, пароль админа: adminadmin)

# Как запустить проект

- Локально проект будет вам доступен по адресу: http://localhost

Склонируйте репозиторий в рабочее пространство командой:

```
git clone https://github.com/Nizzerato/foodgram-project-react.git
```

## Запуск проекта:

- Соберите и запустите проект командой:

```
docker-compose up -d --build
```

- Создайте миграции:

```
docker-compose exec backend python manage.py makemigrations
```

```
docker-compose exec backend python manage.py migrate
```

- Соберите статику проекта:

```
docker-compose exec backend python manage.py collectstatic --no-input
```

Глобальные настройки проекта находятся в файле `backend/settings.py`

## Создание суперпользователя

- Выполните команду:

```
docker-compose exec -ti container_name python manage.py createsuperuser
```

## Наполнение базы данных тестовыми данными

- Выполните команду:

```
docker-compose exec backend bash
```
```
python manage.py shell < import_db.py
```

## Пример наполнения .env-файла:

```
SECRET_KEY=(Этот ключ находится в настройках проекта)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
```

# Tech
**Python**, **Django**, **Rest Framework**, **NGINX**, **Docker**, **Gunicorn**

# Автор
[Nizzerato](https://github.com/Nizzerato)
