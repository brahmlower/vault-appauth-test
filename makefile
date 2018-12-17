
db-setup:
	psql -U app-user -h localhost app-db < sql/schema.sql
	psql -U app-user -h localhost app-db < sql/data.sql

db-revert:
	psql -U app-user -h localhost app-db < sql/revert.sql

install:
	pip install ./app

uninstall:
	pip uninstall -y app

reinstall: uninstall install

run:
	app app/settings.py
