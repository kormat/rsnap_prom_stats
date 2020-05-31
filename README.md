# rsnap_prom_stats
Exports [rsnapshot](http://rsnapshot.org/) stats to [Prometheus](http://prometheus.io/) (via [Pushgateway](https://github.com/prometheus/pushgateway/)).

## Requirements:
A running pushgateway instance.

## Installation:
Download a binary from the [releases](https://github.com/kormat/rsnap_prom_stats/releases) page, install somewhere in your $PATH (e.g. `/usr/local/bin`), and make it executable.

## Setup
`rsnap_prom_stats` needs 2 settings changed in `rsnapshot.conf`. The first is setting `verbose` to at least 4 (so that rsnapshot prints the rsync commands that it runs, and the resulting stats), and the second is adding `--stats --no-human-readable` to the `rsync_long_args` setting, so that rsync prints out stats after every run (in a machine-readable format). It's also recommended to add `--no-verbose` to `rsync_long_args`, to reduce [log spam](https://github.com/rsnapshot/rsnapshot/issues/203#issuecomment-369386151). Example of how the entries will look:
```
verbose         4
rsync_long_args --delete --numeric-ids --relative --delete-excluded --stats --no-human-readable --no-verbose
```

## Running
To use `rsnap_prom_stats`, simply pipe the output of `rsnapshot sync` into it. E.g. (assuming that `rsnap_prom_stats` is in your path):
```
rsnapshot sync | rsnap_prom_stats
```

If your pushgateway isn't running at `localhost:9091`, use the `--pushgw` flag to specify its location.

## Example metrics
```
# HELP rsnapshot_start_time Timestamp rsnapshot started at
# TYPE rsnapshot_start_time gauge
rsnapshot_start_time{instance="{'instance': 'local.host'}"} 1.5909347692082808e+09
# HELP rsnapshot_end_time Timestamp rsnapshot finished at
# TYPE rsnapshot_end_time gauge
rsnapshot_end_time{instance="{'instance': 'local.host'}"} 1.5909347717281592e+09
# HELP rsnapshot_duration_seconds How long rsnapshot ran for
# TYPE rsnapshot_duration_seconds gauge
rsnapshot_duration_seconds{instance="{'instance': 'local.host'}"} 2.519878387451172
# HELP rsync_start_time Time rsync started at
# TYPE rsync_start_time gauge
rsync_start_time{dst_host="local.host",dst_path="/rsnapshot/.sync/remote.host/",instance="local.host",src_host="remote.host",src_path="/"} 1.590934769995552e+09
# HELP rsync_end_time Time rsync finished at
# TYPE rsync_end_time gauge
rsync_end_time{dst_host="local.host",dst_path="/rsnapshot/.sync/remote.host/",instance="local.host",src_host="remote.host",src_path="/"} 1.590934769997473e+09
# HELP rsync_duration_seconds How long rsync ran for
# TYPE rsync_duration_seconds gauge
rsync_duration_seconds{dst_host="local.host",dst_path="/rsnapshot/.sync/remote.host/",instance="local.host",src_host="remote.host",src_path="/"} 0.001920938491821289
# HELP rsync_success 0 if rsync encountered no errors, 1 otherwise.
# TYPE rsync_success gauge
rsync_success{dst_host="local.host",dst_path="/rsnapshot/.sync/remote.host/",instance="local.host",src_host="remote.host",src_path="/"} 0.0
# HELP rsync_num_files Number of files
# TYPE rsync_num_files gauge
rsync_num_files{dst_host="local.host",dst_path="/rsnapshot/.sync/remote.host/",instance="local.host",src_host="remote.host",src_path="/"} 511795.0
# HELP rsync_num_xferred_files Number of regular files transferred
# TYPE rsync_num_xferred_files gauge
rsync_num_xferred_files{dst_host="local.host",dst_path="/rsnapshot/.sync/remote.host/",instance="local.host",src_host="remote.host",src_path="/"} 17.0
# HELP rsync_total_file_bytes Total file size
# TYPE rsync_total_file_bytes gauge
rsync_total_file_bytes{dst_host="local.host",dst_path="/rsnapshot/.sync/remote.host/",instance="local.host",src_host="remote.host",src_path="/"} 2.0689480235e+010
# HELP rsync_total_xferred_file_bytes Total transferred file size
# TYPE rsync_total_xferred_file_bytes gauge
rsync_total_xferred_file_bytes{dst_host="local.host",dst_path="/rsnapshot/.sync/remote.host/",instance="local.host",src_host="remote.host",src_path="/"} 1.13147736e+08
# HELP rsync_literal_data_bytes Literal data
# TYPE rsync_literal_data_bytes gauge
rsync_literal_data_bytes{dst_host="local.host",dst_path="/rsnapshot/.sync/remote.host/",instance="local.host",src_host="remote.host",src_path="/"} 4.946028e+06
# HELP rsync_matched_data_bytes Matched data
# TYPE rsync_matched_data_bytes gauge
rsync_matched_data_bytes{dst_host="local.host",dst_path="/rsnapshot/.sync/remote.host/",instance="local.host",src_host="remote.host",src_path="/"} 1.08201708e+08
# HELP rsync_file_list_bytes File list size
# TYPE rsync_file_list_bytes gauge
rsync_file_list_bytes{dst_host="local.host",dst_path="/rsnapshot/.sync/remote.host/",instance="local.host",src_host="remote.host",src_path="/"} 5.248188e+06
# HELP rsync_file_list_gen_seconds File list generation time
# TYPE rsync_file_list_gen_seconds gauge
rsync_file_list_gen_seconds{dst_host="local.host",dst_path="/rsnapshot/.sync/remote.host/",instance="local.host",src_host="remote.host",src_path="/"} 0.001
# HELP rsync_file_list_xfer_seconds File list transfer time
# TYPE rsync_file_list_xfer_seconds gauge
rsync_file_list_xfer_seconds{dst_host="local.host",dst_path="/rsnapshot/.sync/remote.host/",instance="local.host",src_host="remote.host",src_path="/"} 0.0
# HELP rsync_total_sent_bytes Total bytes sent
# TYPE rsync_total_sent_bytes gauge
rsync_total_sent_bytes{dst_host="local.host",dst_path="/rsnapshot/.sync/remote.host/",instance="local.host",src_host="remote.host",src_path="/"} 167812.0
# HELP rsync_total_recv_bytes Total bytes received
# TYPE rsync_total_recv_bytes gauge
rsync_total_recv_bytes{dst_host="local.host",dst_path="/rsnapshot/.sync/remote.host/",instance="local.host",src_host="remote.host",src_path="/"} 2.078377e+07
```
