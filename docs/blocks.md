# Blocks

A **block** is the basic unit of content in a print job. A print job (or a
saved template) is just an ordered list of blocks, and the server renders
them top to bottom onto the receipt.

Blocks are consumed by:

- `POST /builder` — print a one-off list of blocks immediately.
- `POST /templates` — save a named list of blocks as a reusable template.
- `PUT /templates/<template_id>` — replace a template's name/blocks.

The block list itself has the same shape in all three places: a JSON array
under the `blocks` key, e.g. `{"blocks": [ ... ]}`.

## Block shape

Every block is a JSON object with a required `type` and fields that depend
on that type:

```json
{ "type": "text", "text": "hello", "style": { "align": "center", "bold": true } }
```

| Field    | Type   | Required | Description                                                                 |
| -------- | ------ | -------- | ----------------------------------------------------------------------------- |
| `type`   | string | yes      | One of `title`, `text`, `divider`, `newline`, `qr`, `image`.                  |
| `style`  | object | no       | Optional [style overrides](#style) applied to this block, then reset after.   |

Any other fields are type-specific, documented below.

Server-side validation (`POST`/`PUT /templates`) rejects a payload if any
block is not an object or has a `type` outside the known set:
`title`, `text`, `divider`, `newline`, `qr`, `image`.

## Block types

### `title`

A single line of large, bold, centered text (unless overridden by `style`).

```json
{ "type": "title", "text": "Grocery List" }
```

| Field  | Type   | Required | Default | Notes            |
| ------ | ------ | -------- | ------- | ----------------- |
| `text` | string | no       | `""`    | Line to print.     |

Default style for `title` blocks (each key can be overridden individually
via the block's own `style`):

```json
{ "align": "center", "bold": true, "double_width": true, "double_height": true }
```

### `text`

A single block of body text.

```json
{ "type": "text", "text": "2% milk\nEggs\nBread" }
```

| Field  | Type   | Required | Default | Notes                       |
| ------ | ------ | -------- | ------- | ----------------------------- |
| `text` | string | no       | `""`    | Text to print (may contain `\n`). |

### `divider`

A horizontal rule (a line of dashes). Takes no fields besides `type` and
optional `style`.

```json
{ "type": "divider" }
```

### `newline`

One or more blank lines.

```json
{ "type": "newline", "count": 2 }
```

| Field   | Type    | Required | Default | Notes                                             |
| ------- | ------- | -------- | ------- | ---------------------------------------------------- |
| `count` | integer | no       | `1`     | Number of blank lines. Negative values are silently ignored (no-op). |

### `qr`

A QR code.

```json
{ "type": "qr", "data": "https://example.com", "size": 3, "center": true }
```

| Field    | Type    | Required | Default | Notes                                  |
| -------- | ------- | -------- | ------- | ----------------------------------------- |
| `data`   | string  | no       | `""`    | Text/URL to encode.                        |
| `size`   | integer | no       | `3`     | Module size passed to the printer (builder UI allows 1-16). |
| `center` | boolean | no       | `true`  | Whether to center the code horizontally.  |

### `image`

A raster image.

```json
{ "type": "image", "image": "data:image/png;base64,iVBORw0KG...", "center": true }
```

| Field    | Type    | Required | Notes                                                                 |
| -------- | ------- | -------- | ---------------------------------------------------------------------- |
| `image`  | string  | yes      | A base64 data URL (`data:image/...;base64,...`). The `data:...;base64,` prefix, if present, is stripped before decoding — only the part after the first comma is treated as base64. |
| `center` | boolean | no       | Whether to center the image horizontally. Default `true`.              |

The image is decoded server-side with Pillow and, if wider than the
printer's known media width (from the escpos profile, falling back to 384
dots for 58mm printers), is downscaled to fit while preserving aspect
ratio.

An `image` block with no usable `image` data is simply skipped (no error);
the front-end builder additionally refuses to submit an `image` block that
has no file chosen.

## Style

`style` is an optional object on any block. Its keys map directly onto the
underlying escpos `printer.set(...)` call, are applied immediately before
the block renders, and are reset back to defaults immediately after — so a
style never bleeds into later blocks.

| Key               | Type    | Notes                                                        |
| ----------------- | ------- | -------------------------------------------------------------- |
| `align`            | string  | `left`, `center`, or `right`.                                  |
| `font`             | string  | `a` or `b`.                                                     |
| `bold`             | boolean |                                                                  |
| `underline`        | integer | `0`-`2`.                                                        |
| `invert`           | boolean | White-on-black.                                                 |
| `smooth`           | boolean |                                                                  |
| `flip`             | boolean | Upside-down.                                                    |
| `double_width`     | boolean |                                                                  |
| `double_height`    | boolean |                                                                  |
| `custom_size`      | boolean | Must be `true` for `width`/`height` to take effect.             |
| `width`            | integer | `1`-`8`. Requires `custom_size: true`.                          |
| `height`           | integer | `1`-`8`. Requires `custom_size: true`.                          |
| `density`          | integer | `0`-`8`.                                                        |
| `normal_textsize`  | boolean | Resets to the printer's normal text size.                       |

Only keys present in `style` are applied and reset — omitted keys are left
untouched from whatever the previous block set (aside from `title`, whose
own defaults above are merged under any `style` you provide).

## Example payload

```json
{
  "blocks": [
    { "type": "title", "text": "Grocery List" },
    { "type": "divider" },
    { "type": "text", "text": "2% milk\nEggs\nBread", "style": { "align": "left" } },
    { "type": "newline", "count": 2 },
    { "type": "qr", "data": "https://example.com/list/123", "size": 4 },
    { "type": "image", "image": "data:image/png;base64,iVBORw0KG..." }
  ]
}
```

## Endpoints

### `POST /builder`

Prints the given blocks immediately.

Request body:

```json
{ "blocks": [ /* block objects, see above */ ] }
```

Responses:

- `200 OK` — `{ "success": true }`
- `422 Unprocessable Entity` — `{ "success": false, "error": "<message>" }` if there are no blocks, or if rendering fails (e.g. bad image data, unsupported style value).

Note: `POST /builder` does not itself validate block `type` against the
known set the way `/templates` does — an unknown type raises an error
during rendering (surfaced as a `422`) instead of being rejected up front.

### `POST /templates`

Saves a new named template.

Request body:

```json
{ "name": "Grocery List", "blocks": [ /* block objects */ ] }
```

Responses:

- `200 OK` — the created template: `{ "id": "...", "name": "...", "blocks": [...] }`
- `422 Unprocessable Entity` — `{ "error": "<message>" }` if `name` is blank, `blocks` is missing/empty, or any block is not an object with a valid `type` (one of `title`, `text`, `divider`, `newline`, `qr`, `image`).

### `PUT /templates/<template_id>`

Replaces an existing template's name and blocks. Same request/response
shape and validation as `POST /templates`. Returns `404` (`{ "error": "Template not found" }`) if the template doesn't exist.
