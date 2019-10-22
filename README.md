# Homer Multitext CITE ATLAS

CITE ATLAS Server for the Homer Multitext Project.

## Getting Started

Make sure you are using a virtual environment of some sort (e.g. `virtualenv`
or `pyenv`).

```
pip install -r requirements-dev.txt
```

Create a PostgreSQL database `hmt_cite_atlas`:

```
createdb hmt_cite_atlas
```

Populate the database:

```
./manage.py migrate
./manage.py loaddata sites
```

Run the Django dev server:
```
./manage.py runserver
```

Browse to http://localhost:8000/

## Loading data

Create a superuser:

```
./manage.py createsuperuser
```

Run the `import_versions` script:

```
./manage.py shell -c 'from hmt_cite_atlas.library.importers import import_versions; import_versions();'
```

## Sample Queries

Access the interactive GraphQL explorer at `http://localhost:8000/graphql/`.
