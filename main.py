import os
from bottle import route, post, run, request, response, static_file, template, BaseRequest
from printer import load_printer, printer_status, print_blocks

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

@route('/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root='./static')


if __name__ == '__main__':
    DEFAULT_LISTEN_IP = os.environ.get('PIPRINTER_LISTEN_IP', 'localhost')
    DEFAULT_LISTEN_PORT = int(os.environ.get('PIPRINTER_PORT', 8080))
    PIPRINTER_CONFIG_PATH = os.environ.get('PIPRINTER_CONFIG_PATH', 'config.example.yaml')
    BaseRequest.MEMFILE_MAX = 10240 * 1024
    load_printer(PIPRINTER_CONFIG_PATH)
    run(host=DEFAULT_LISTEN_IP, port=DEFAULT_LISTEN_PORT)
