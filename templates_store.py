import json
import os
import threading
import uuid

# TemplateStore persists user-defined custom block templates to a JSON
# file so they survive restarts, and are shared across requests/threads.
class TemplateStore:
    def __init__(self, path):
        self.path = path
        self._lock = threading.Lock()
        if not os.path.exists(self.path):
            self._write([])

    def _read(self):
        with open(self.path, 'r') as f:
            return json.load(f)

    def _write(self, templates):
        tmp_path = f"{self.path}.tmp"
        with open(tmp_path, 'w') as f:
            json.dump(templates, f, indent=2)
        os.replace(tmp_path, self.path)

    def list(self):
        with self._lock:
            return self._read()

    def get(self, template_id):
        with self._lock:
            for t in self._read():
                if t['id'] == template_id:
                    return t
        return None

    def create(self, name, blocks):
        with self._lock:
            templates = self._read()
            template = {
                'id': uuid.uuid4().hex,
                'name': name,
                'blocks': blocks,
            }
            templates.append(template)
            self._write(templates)
            return template

    def update(self, template_id, name, blocks):
        with self._lock:
            templates = self._read()
            for t in templates:
                if t['id'] == template_id:
                    t['name'] = name
                    t['blocks'] = blocks
                    self._write(templates)
                    return t
        return None

    def delete(self, template_id):
        with self._lock:
            templates = self._read()
            remaining = [t for t in templates if t['id'] != template_id]
            if len(remaining) == len(templates):
                return False
            self._write(remaining)
            return True
