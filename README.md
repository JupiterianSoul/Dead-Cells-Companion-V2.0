# Dead Cells Companion

A small Flask app that lets you browse, search and filter every item in Dead Cells. Item data comes from the Dead Cells wiki and lives in `items.json`.

## Features

- Search by name and filter by category
- Item detail view with the stats from the wiki
- Random item button
- Personal notes per item, saved locally
- Export of the item list
- Stats endpoint with counts per category

## Run it

```
pip install flask
python app.py
```

Then open http://localhost:5000. Notes are written to `data/item_notes.json`.

## Tests

```
python -m unittest test_app.py
```

## API

- `GET /api/items` list items, with query filters
- `GET /api/categories`
- `GET /api/item/<name>`
- `GET /api/random`
- `GET, POST /api/notes`
- `GET /api/export/<format>`
- `GET /api/reload` reload `items.json`
- `GET /api/stats`

The `index.html`, `style.css` and `app.js` files at the repo root are the front end. Flask expects them under `templates/` and `static/`, so copy them there before running.
