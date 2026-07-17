from escpos import config, printer
from escpos import *

from PreprocessBuilder import PreprocessBuilder

# global printer defined at initial load
printer = None

def load_printer(config_file="config.example.yaml"):
    global printer
    printer_config = config.Config()
    printer_config.load(config_file)
    printer = printer_config.printer()
    return printer

def printer_status():

    paper_num = printer.paper_status()
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

def print_blocks(blocks):
    if not blocks:
        return False, "No blocks to print"

    try:
        builder = PreprocessBuilder(profile=printer.profile)
        builder.build_from_blocks(blocks)
        output = builder.get_commands()

        printer.open()
        printer._raw(output)
        printer.close()
        return True, None
    except Exception as e:
        return False, str(e)

