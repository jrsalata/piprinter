from escpos import config, printer
from escpos import *


# global printer defined at initial load
printer = None

def load_printer(config_file="config.example.yaml"):
    global printer
    printer_config = config.Config()
    printer_config.load(config_file)
    printer = printer_config.printer()
    return printer

def printer_status():

    # paper_num = printer.paper_status()
    paper_num = 2
    paper = "Unknown"
    if paper_num == 0:
        paper = "Out of paper"
    elif paper_num == 1:
        paper = "Paper low"
    else:
        paper = "Paper OK"

    status = {
        "ready": printer.is_usable(),
        "paper": paper,
    }
    return status

def send_print(data):
    title = (data.get('title') or '').strip()
    if not title:
        return False, "Title is required"

    priority = (data.get('priority') or '').strip()
    est_time = (data.get('est_time') or '').strip()
    due_date = (data.get('due_date') or '').strip()
    body = (data.get('body') or '').strip()

    try:
        printer.open()

        printer.set(align='center', bold=True, double_width=True, double_height=True)
        printer.textln(title)
        printer.set(align='left', bold=False, double_width=False, double_height=False)

        meta = []
        if priority:
            meta.append(f"Priority: {priority}")
        if est_time:
            meta.append(f"Estimated Time: {est_time}")
        if due_date:
            meta.append(f"Due Date: {due_date}")

        if meta:
            printer.ln()
            for line in meta:
                printer.textln(line)

        if body:
            printer.ln()
            printer.textln("-" * 32)
            printer.ln()
            printer.textln(body)

        printer.ln()
        printer.cut()
        return True, None
    except Exception as e:
        return False, str(e)
