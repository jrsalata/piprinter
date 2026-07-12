from escpos import config, printer
from escpos import *

printer_config = config.Config()
printer_config.load("config.example.yaml")

printer = printer_config.printer()
print(printer.is_usable())

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
    try:
        printer.open()
        printer.textln(data['title'])
        printer.ln()
        printer.textln(f"Priority: {data['priority']}")
        printer.textln(f"Estimated Time: {data['est_time']}")
        printer.textln(f"Due Date: {data['due_date']}")
        printer.ln()
        printer.textln(data['body'])
        printer.cut()
        return True, None
    except Exception as e:
        return False, str(e)
    