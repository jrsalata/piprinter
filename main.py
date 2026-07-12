import os
from bottle import route, post, run, request, static_file, template
from printer import load_printer, printer_status, send_print

@route('/')
@post('/')
def index():
    status = printer_status()
    if request.method == 'POST':
        data = {
            'title':      request.forms.get('title'),
            'priority':   request.forms.get('priority'),
            'est_time':   request.forms.get('est_time'),
            'body':       request.forms.get('body'),
            'due_date':   request.forms.get('due_date'),
        }
        result, err = send_print(data)
        if result:
            return template("index.html", success=f"Task {data['title']} created successfully!", status=status)
        else:
            return template("index.html", error=f"Failed to create task: {err}", status=status)
    
    return template("index.html", status=status)

@route('/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root='./static')


if __name__ == '__main__':
    DEFAULT_LISTEN_IP = os.environ.get('PIPRINTER_LISTEN_IP', 'localhost')
    DEFAULT_LISTEN_PORT = int(os.environ.get('PIPRINTER_PORT', 8080))
    PIPRINTER_CONFIG_PATH = os.environ.get('PIPRINTER_CONFIG_PATH', 'config.example.yaml')
    load_printer(PIPRINTER_CONFIG_PATH)
    run(host=DEFAULT_LISTEN_IP, port=DEFAULT_LISTEN_PORT)