import os
from bottle import route, post, put, delete, run, request, response, static_file, template
from printer import load_printer, printer_status, print_blocks
from templates_store import TemplateStore

# Block types the builder can construct and PreprocessBuilder can render.
# Templates referencing anything else are rejected so a bad template can't
# be persisted and then crash the builder form when it's loaded back.
KNOWN_BLOCK_TYPES = {'title', 'text', 'divider', 'newline', 'qr', 'image'}

# Initialized at import time (not just under __main__) so the /templates
# routes work under any WSGI host, e.g. `gunicorn main:app`.
template_store = TemplateStore(os.environ.get('PIPRINTER_TEMPLATES_PATH', 'templates.json'))

@route('/')
def index():
    status = printer_status()
    return template("index.html", status=status)

@route('/ticket')
def ticket():
    status = printer_status()
    return template("ticket.html", status=status)

@route('/builder')
def builder():
    status = printer_status()
    return template("builder.html", status=status)

@post('/builder')
def builder_print():
    payload = request.json or {}
    blocks = payload.get('blocks', [])

    result, err = print_blocks(blocks)
    if result:
        return {"success": True}
    else:
        response.status = 422
        return {"success": False, "error": err}

@route('/templates')
def templates_list():
    # Return lightweight summaries only: the home page renders just the name
    # and block count, so there's no need to ship every template's full block
    # list (which can carry large base64 image payloads) on each page load.
    summaries = [
        {"id": t["id"], "name": t["name"], "block_count": len(t.get("blocks") or [])}
        for t in template_store.list()
    ]
    return {"templates": summaries}

@post('/templates')
def templates_create():
    payload = request.json or {}
    name, blocks, err = _validate_template_payload(payload)
    if err:
        response.status = 422
        return {"error": err}

    return template_store.create(name, blocks)

@route('/templates/<template_id>')
def templates_get(template_id):
    tmpl = template_store.get(template_id)
    if not tmpl:
        return _not_found()
    return tmpl

@put('/templates/<template_id>')
def templates_update(template_id):
    payload = request.json or {}
    name, blocks, err = _validate_template_payload(payload)
    if err:
        response.status = 422
        return {"error": err}

    tmpl = template_store.update(template_id, name, blocks)
    if not tmpl:
        return _not_found()
    return tmpl

@delete('/templates/<template_id>')
def templates_delete(template_id):
    if not template_store.delete(template_id):
        return _not_found()
    return {"success": True}

def _not_found():
    response.status = 404
    return {"error": "Template not found"}

def _validate_template_payload(payload):
    name = (payload.get('name') or '').strip()
    blocks = payload.get('blocks')
    if not name:
        return None, None, "Template name is required"
    if not isinstance(blocks, list) or not blocks:
        return None, None, "At least one block is required"
    for block in blocks:
        if not isinstance(block, dict) or block.get('type') not in KNOWN_BLOCK_TYPES:
            return None, None, "Every block must have a valid type"
    return name, blocks, None

@route('/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root='./static')


if __name__ == '__main__':
    DEFAULT_LISTEN_IP = os.environ.get('PIPRINTER_LISTEN_IP', 'localhost')
    DEFAULT_LISTEN_PORT = int(os.environ.get('PIPRINTER_PORT', 8080))
    PIPRINTER_CONFIG_PATH = os.environ.get('PIPRINTER_CONFIG_PATH', 'config.example.yaml')
    load_printer(PIPRINTER_CONFIG_PATH)
    run(host=DEFAULT_LISTEN_IP, port=DEFAULT_LISTEN_PORT)
