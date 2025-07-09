from presenter import app

bind = '0.0.0.0:8123'
workers = 12
on_starting = app.on_starting
timeout = 180