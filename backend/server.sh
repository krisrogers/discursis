NUM_WORKERS=3
TIMEOUT=120

exec gunicorn server:app \
--workers $NUM_WORKERS \
--timeout $TIMEOUT \
--log-level=debug \
--bind=127.0.0.1:5000
