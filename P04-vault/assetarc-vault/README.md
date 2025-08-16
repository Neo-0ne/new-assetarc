# AssetArc – S3 Vault & Document Service

Stores originals in S3 with versioning, generates **watermarked previews**, tracks
downloads, and issues short-lived **signed URLs**. Before human review approval,
only the preview is visible. After approval, original can be downloaded via signed
link.

## Endpoints

- `GET  /healthz`
- `POST /files/upload` (multipart: `file`), optional fields: `folder`, `label`
- `GET  /files` – list my files
- `GET  /files/<id>` – metadata
- `POST /files/<id>/watermark` – generate/update preview (PDF/image)
- `POST /files/<id>/approve` – mark approved
- `POST /files/<id>/signed-url` –
  `{disposition?: "inline"|"attachment", filename?: string}`
  → presigned S3 URL
  Example:

  ```json
  {
    "disposition": "attachment",
    "filename": "contract.pdf"
  }
  ```

- `POST /files/<id>/track-download` – record a download event

Auth: JWT cookie/header shared with Auth (Project 1).
