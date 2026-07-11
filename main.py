from bottle import route, post, run, request, static_file, template

@route('/')
@post('/')
def index():
    if request.method == 'POST':
        data = {
            'title':      request.forms.get('title'),
            'priority':   request.forms.get('priority'),
            'est_time':   request.forms.get('est_time'),
            'body':       request.forms.get('body'),
            'due_date':   request.forms.get('due_date'),
        }
        # TODO: process `data` here
        return template("index.html", success=f"Task {data['title']} created successfully!")
    return template("index.html")

@route('/<filepath:path>')
def server_static(filepath):
    print(filepath)
    return static_file(filepath, root='./static')


run(host='localhost', port=8080)