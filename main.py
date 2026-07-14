import os
from bottle import route, post, put, delete, run, request, response, static_file, template
from printer import load_printer, printer_status, print_blocks
from templates_store import TemplateStore

template_store = None

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
    return {"templates": template_store.list()}

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
        response.status = 404
        return {"error": "Template not found"}
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
        response.status = 404
        return {"error": "Template not found"}
    return tmpl

@delete('/templates/<template_id>')
def templates_delete(template_id):
    if not template_store.delete(template_id):
        response.status = 404
        return {"error": "Template not found"}
    return {"success": True}

def _validate_template_payload(payload):
    name = (payload.get('name') or '').strip()
    blocks = payload.get('blocks') or []
    if not name:
        return None, None, "Template name is required"
    if not blocks:
        return None, None, "At least one block is required"
    return name, blocks, None

@route('/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root='./static')


if __name__ == '__main__':
    DEFAULT_LISTEN_IP = os.environ.get('PIPRINTER_LISTEN_IP', 'localhost')
    DEFAULT_LISTEN_PORT = int(os.environ.get('PIPRINTER_PORT', 8080))
    PIPRINTER_CONFIG_PATH = os.environ.get('PIPRINTER_CONFIG_PATH', 'config.example.yaml')
    PIPRINTER_TEMPLATES_PATH = os.environ.get('PIPRINTER_TEMPLATES_PATH', 'templates.json')
    load_printer(PIPRINTER_CONFIG_PATH)
    template_store = TemplateStore(PIPRINTER_TEMPLATES_PATH)
    run(host=DEFAULT_LISTEN_IP, port=DEFAULT_LISTEN_PORT)
