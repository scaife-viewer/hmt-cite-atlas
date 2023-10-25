# Homer Multitext CITE ATLAS

CITE ATLAS Server for the Homer Multitext Project.

## Getting Started

Make sure you are using a virtual environment of some sort (e.g. `virtualenv`
or `pyenv`).

```
pip install -r requirements-dev.txt
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

Run the `import_libraries` script:

```
./manage.py shell -c 'from hmt_cite_atlas.library.importers import import_libraries; import_libraries()'
```

## Exporting text annotations for Beyond Translation


```
./manage.py shell -c 'from hmt_cite_atlas.shortcuts import main; main()'
```

## Sample Queries
_NOTE: This should be considered deprecated in favor of [scaife-viewer-atlas](https://github.com/scaife-viewer/backend/tree/6c8f8f1a869ff650632ebc0d93a214f913d1983d/atlas)_

Access the interactive GraphQL explorer at `http://localhost:8000/graphql/`.

Get all libraries and the URNs of the versions they contain.
```
{
  libraries {
    edges {
      node {
        id
        urn
        versions {
          edges {
            node {
              urn
            }
          }
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

Get the first line of the Iliad.
```
{
  lines(position: 1) {
    edges {
      node {
        urn
        textContent
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

Get the first line of all the scholia on the Iliad.
```
{
  sections(position: 1) {
    edges {
      node {
        urn
        textContent
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```


Page through the Iliad ten lines at a time.
```
{
  lines(book_Urn: "urn:cts:greekLit:tlg0012.tlg001.msA:", first:10) {
    edges {
      cursor
      node {
        urn
        textContent
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```
