# Copyright 2016 Stephen Shirley
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import logging
import re
import socket
import sys
import time

from prometheus_client import (
    CollectorRegistry,
    Gauge,
    generate_latest,
    push_to_gateway,
)

DEFAULT_PUSH_GATEWAY = "localhost:9091"
DEFAULT_JOB_NAME = "rsnapshot"

localhost = socket.getfqdn()
gauges = {}
RSYNC_STATS = {
    # Metadata
    "rsync_start_time": "Time rsync started at",
    "rsync_end_time": "Time rsync finished at",
    "rsync_duration_seconds": "How long rsync ran for",
    "rsync_success": "0 if rsync encountered no errors, 1 otherwise.",
    # Stats directly from rsync
    "rsync_num_files": "Number of files",
    "rsync_num_xferred_files": "Number of regular files transferred",
    "rsync_total_file_bytes": "Total file size",
    "rsync_total_xferred_file_bytes": "Total transferred file size",
    "rsync_literal_data_bytes": "Literal data",
    "rsync_matched_data_bytes": "Matched data",
    "rsync_file_list_bytes": "File list size",
    "rsync_file_list_gen_seconds": "File list generation time",
    "rsync_file_list_xfer_seconds": "File list transfer time",
    "rsync_total_sent_bytes": "Total bytes sent",
    "rsync_total_recv_bytes": "Total bytes received",
}


class Stats:
    STAT_NAME = {v: k for k, v in RSYNC_STATS.items()}

    def __init__(self, line):
        self._metrics = {}
        self._metrics['rsync_start_time'] = time.time()
        self._end = 0
        self._success = True
        self.src_host = None
        self.src_path = None
        self.dst_host = None
        self.dst_path = None
        self._parse_rsync_line(line)

    def _parse_rsync_line(self, line):
        parts = line.split()
        self.src_host, self.src_path = self._get_host_path(parts[-2])
        self.dst_host, self.dst_path = self._get_host_path(parts[-1])

    def _get_host_path(self, s):
        remote_rx = re.compile(r'((.*@)?(?P<host>.+):)?(?P<path>.+)$')
        m = remote_rx.match(s)
        host = m.group('host') or localhost
        path = m.group('path')
        return host, path

    def parse(self, line):
        """
        Returns None on success, False on error
        """
        parse_rx = re.compile(r'^(?P<desc>[^:]+): (?P<val>\S+)')
        m = parse_rx.match(line)
        if not m:
            return
        desc = m.group('desc')
        if desc == "rsync error":
            self._success = False
            return False
        name = self.STAT_NAME.get(m.group('desc'))
        if not name:
            # Skip non-matching lines
            return
        self._metrics[name] = float(m.group('val'))

    def publish(self, def_labels):
        self._metrics['rsync_end_time'] = time.time()
        self._metrics['rsync_duration_seconds'] = (
            self._metrics['rsync_end_time'] - self._metrics['rsync_start_time'])
        self._metrics['rsync_success'] = 0 if self._success else 1
        logging.info("Publishing %s:%s -> %s:%s" % (
                self.src_host, self.src_path, self.dst_host, self.dst_path))
        labels = {
            'src_host': self.src_host,
            'src_path': self.src_path,
            'dst_host': self.dst_host,
            'dst_path': self.dst_path,
        }
        labels.update(def_labels)
        for name, val in self._metrics.items():
            metric = gauges[name]
            metric.labels(**labels).set(val)


def main():
    parser = argparse.ArgumentParser(
        prog="rsnap_prom_stats",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--pushgw", default=DEFAULT_PUSH_GATEWAY,
                        help="Address of the pushgateway to publish to. If "
                        "set to '-' it will print the metrics to stdout instead.")
    parser.add_argument("--job", default=DEFAULT_JOB_NAME,
                        help="Pushgateway job name.")
    parser.add_argument("-v", action="store_true",
                        help="Print some information to stdout.")
    args = parser.parse_args()
    level = logging.WARNING
    if args.v:
        level = logging.INFO
    logging.basicConfig(
        format='[%(asctime)s] %(message)s',
        level=level)

    registry = setup_metrics()
    start = time.time()
    logging.info("Started")
    def_labels = {'instance': localhost}
    process_input(def_labels)
    end = time.time()
    logging.info("Finished reading output")
    gauges["rsnapshot_start_time"].labels(def_labels).set(start)
    gauges["rsnapshot_end_time"].labels(def_labels).set(end)
    gauges["rsnapshot_duration_seconds"].labels(def_labels).set(end - start)
    if args.pushgw == "-":
        print(generate_latest(registry).decode("utf-8"))
    else:
        logging.info("publishing to pushgateway @ %s", args.pushgw)
        push_to_gateway(args.pushgw, job=args.job, registry=registry)


def setup_metrics():
    registry = CollectorRegistry()
    basic_labels = ['instance']
    gauges["rsnapshot_start_time"] = Gauge(
        "rsnapshot_start_time", "Timestamp rsnapshot started at", basic_labels,
        registry=registry)
    gauges["rsnapshot_end_time"] = Gauge(
        "rsnapshot_end_time", "Timestamp rsnapshot finished at", basic_labels,
        registry=registry)
    gauges["rsnapshot_duration_seconds"] = Gauge(
        "rsnapshot_duration_seconds", "How long rsnapshot ran for", basic_labels,
        registry=registry)
    rsync_labels = ['src_host', 'src_path', 'dst_host', 'dst_path']
    for name, desc in RSYNC_STATS.items():
        gauges[name] = Gauge(
            name, desc, basic_labels + rsync_labels, registry=registry)
    return registry


def process_input(def_labels):
    rsync_rx = re.compile(r'^[/\w]+/rsync')
    s = None
    for line in read_lines():
        if not line:  # Skip blank lines
            continue
        if rsync_rx.match(line):
            s = Stats(line)
            continue
        if not s:
            # Don't bother parsing lines until we found the start of a stats
            # block
            continue
        if line.startswith('sent ') or s.parse(line) is False:
            # We've reached the end of the stats block, or an rsync error
            # was encountered. Either way, publish the stats.
            s.publish(def_labels)
            s = None
            continue


def read_lines():
    line = ""
    for l in sys.stdin:
        line += l.strip()
        if line.endswith("\\"):
            line = line.rstrip("\\")
            continue
        yield line
        line = ""


if __name__ == '__main__':
    main()
