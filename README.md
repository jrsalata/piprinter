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

## Periodic Jira ticket printing

`jira_poll.py` polls Jira for issues assigned to you and prints any tickets it hasn't printed before. It's built on top of [jira-cli](https://github.com/ankitpokhrel/jira-cli), a third-party command line tool for Jira.

### Setup

1. Install `jira-cli` (see its [installation docs](https://github.com/ankitpokhrel/jira-cli#installation)) and make sure the `jira` binary is on your `PATH`.
2. Run `jira init` to authenticate and generate a config file. For headless setups, export `JIRA_API_TOKEN` (and `JIRA_AUTH_TYPE=bearer` for a personal access token) before running `jira init`.
3. Verify it works: `jira issue list -a$(jira me)` should list your assigned issues.

### Running the poll manually

```bash
python3 jira_poll.py
```

Only tickets not seen on a previous run are printed. Printed ticket keys are tracked in `jira_poll_state.json` (path configurable via `JIRA_POLL_STATE_PATH`) so re-running the script won't reprint the same ticket.

Environment variables:

- `PIPRINTER_CONFIG_PATH` — path to the escpos printer config (same variable used by `main.py`)
- `JIRA_POLL_STATE_PATH` — where to store the set of already-printed ticket keys (default: `jira_poll_state.json` next to the script)
- `JIRA_BIN` — path to the `jira` binary if it isn't on `PATH` (default: `jira`)

### Running it periodically

`piprinter-jira-poll.service` and `piprinter-jira-poll.timer` run the poll on a systemd timer (every 15 minutes by default). To install:

```bash
sudo cp piprinter-jira-poll.service piprinter-jira-poll.timer /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable --now piprinter-jira-poll.timer
```

Be sure to edit `piprinter-jira-poll.service` first with the appropriate username, paths, and environment variables, same as `piprinter.service`. Since `jira-cli` auth is tied to the user running it, run the timer as the same user who ran `jira init`.
