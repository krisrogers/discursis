watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- celery worker --app=server.celery --concurrency=1 --loglevel=INFO
