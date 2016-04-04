# rsnap_prom_stats
Exports [rsnapshot](http://rsnapshot.org/) stats to [Prometheus](http://prometheus.io/) (via [Pushgateway](https://github.com/prometheus/pushgateway/)).

## Requirements:
- python3
- The Prometheus [python client library](https://github.com/prometheus/client_python)

This assumes that you already have Prometheus setup, and a pushgateway running on the local machine.

A debian package is available from [deb.ichbinn.net](https://deb.ichbinn.net/).

## Setup
rsnap_prom_stats needs 2 settings changed in `rsnapshot.conf`. The first is setting `verbose` to at least 3 (so that rsnapshot prints the rsync commands that it runs), and the second is adding `--stats` to the `rsync_long_args` setting, so that rsync prints out stats after every run. Example of how the entries will look:
```
verbose         3
rsync_long_args --delete --numeric-ids --relative --delete-excluded --stats
```

## Running
To use rsnap_prom_stats, simply pipe the output of `rsnapshot sync` into it. E.g. (assuming that rsnap_prom_stats is in your path):
```
rsnapshot sync | rsnap_prom_stats
```

For now, the location of your pushgateway is assumed to be `localhost:9091`, edit the `PUSH_GATEWAY` constant at the top of `rsnap_prom_stats.py` to change this.
