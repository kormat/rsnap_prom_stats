# rsnapshot_exporter
Exports [rsnapshot](http://rsnapshot.org/) stats to [Prometheus](http://prometheus.io/) (via [Pushgateway](https://github.com/prometheus/pushgateway/)).

## Requirements:
- python3
- The Prometheus [python client library](https://github.com/prometheus/client_python)

This assumes that you already have Prometheus setup, and a pushgateway running on the local machine.

## Setup
rsnapshot_exporter needs 2 settings changed in `rsnapshot.conf`. The first is setting `verbose` to at least 3 (so that rsnapshot prints the rsync commands that it runs), and the second is adding `--stats` to the `rsync_long_args` setting, so that rsync prints out stats after every run. Example of how the entries will look:
```
verbose         3
rsync_long_args --delete --numeric-ids --relative --delete-excluded --stats
```

## Running
To use rsnapshot_exporter, simply pipe the output of `rsnapshot sync` into it. E.g. (assuming that rsnapshot_exporter is in your path):
```
rsnapshot sync | rsnapshot_exporter
```

For now, the location of your pushgateway is assumed to be `localhost:9091`, edit the `PUSH_GATEWAY` constant at the top of `rsnapshot_exporter.py` to change this.
