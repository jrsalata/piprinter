# piprinter

PiPrinter is going to use a raspberry pi connected with a printer to print tickets using a receipt printer

It is a simple web ui that will be updated as I find new use cases for it.

It was heavily inspired by [this YouTube video](https://youtu.be/xg45b8UXoZI) on how to manage productivity. However, I needed something a lot simpler for my day to day life.

NOTE: I have ordered my printer as of writing this README, but have not received it yet for testing. Your mileage may vary.

## AI-usage disclaimer

This project is labeled as [AI-Reviewed](https://salata.software/about/ai/#ai-reviewed). The majority of the project was written by myself with further updates to styling and appearance from Claude code.

A majority of the front-end (styling, HTML, js) is Claude, while the PreprocessBuilder and most of the printer.py was originally written by myself.

## Installation

Python 3.12 is required

To install dependencies, run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

There is also a service file that can be used to run this on startup. This can be done using

```bash
sudo cp piprinter.service /etc/systemd/system
sudo chmod 644 /etc/systemd/system/piprinter.service
sudo systemctl daemon-reload
sudo systemctl enable piprinter.service
```

Be sure to edit the service file with the appropriate username, config file, path, and environment variables.

### Printer Config

I will redirect you to the [escpos docs](https://python-escpos.readthedocs.io/en/latest/index.html) on how to set up a config file. The example one is just a dummy for testing purposes.
