# AssetArc – Newsletter Logic Bot (P40)

Newsletter HTML rendering **and PDF export**.

## Endpoints

### GET `/healthz`

Basic health check.

### GET `/templates`

Lists available HTML templates in the `templates/` directory.

### POST `/render`

Render a template to HTML.

Example request body:

```json
{
  "template_id": "newsletter_base.html",
  "vars": {
    "title": "April Update",
    "body": "Hello world"
  }
}
```

Returns JSON with an `html` property containing the rendered template.

### POST `/render/pdf`

Render a template to a downloadable PDF.

Example request body:

```json
{
  "template_id": "newsletter_base.html",
  "vars": {
    "title": "April Update"
  },
  "output_name": "update.pdf"
}
```

Returns the rendered PDF as a file download.

## Configuration

* Templates must be stored in a `templates/` directory and end with `.html`.
* Environment variables from a `.env` file are loaded if present, but none are required
  by default.
* The container exposes port `8080` unless `PORT` is set.
