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

from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

DEFAULT_PUSH_GATEWAY = "localhost:9091"
DEFAULT_JOB_NAME = "rsnapshot"

localhost = socket.getfqdn()
gauges = {}
RSYNC_STATS = {
    # Metadata
    "rsync_start": "Time rsync started at",
    "rsync_end": "Time rsync finished at",
    "rsync_duration": "How long rsync ran for",
    # Stats directly from rsync
    "rsync_num_files": "Number of files",
    "rsync_num_files_xferred": "Number of regular files transferred",
    "rsync_total_file_size": "Total file size",
    "rsync_total_xferred_file_size": "Total transferred file size",
    "rsync_literal_data": "Literal data",
    "rsync_matched_data": "Matched data",
    "rsync_file_list_size": "File list size",
    "rsync_file_list_gen_time": "File list generation time",
    "rsync_file_list_xfer_time": "File list transfer time",
    "rsync_total_sent": "Total bytes sent",
    "rsync_total_recv": "Total bytes received",
}


class Stats:
    START_NAME = {v: k for k, v in RSYNC_STATS.items()}

    def __init__(self, line):
        self._metrics = {}
        self._metrics['rsync_start'] = time.time()
        self._end = 0
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
        host = m.group('host') or socket.getfqdn()
        path = m.group('path')
        return host, path

    def parse(self, line):
        parse_rx = re.compile(r'^(?P<desc>[^:]+): (?P<val>\S+)')
        m = parse_rx.match(line)
        if not m:
            return
        name = self.START_NAME.get(m.group('desc'))
        if not name:
            # Skip non-machines lines
            return
        self._metrics[name] = float(m.group('val'))

    def publish(self, def_labels):
        self._metrics['rsync_end'] = time.time()
        self._metrics['rsync_duration'] = (
            self._metrics['rsync_end'] - self._metrics['rsync_start'])
        print("Publishing %s:%s -> %s:%s" % (
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
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--pushgw", default=DEFAULT_PUSH_GATEWAY,
            help="Address of the pushgateway to publish to.")
    parser.add_argument("--job", default=DEFAULT_JOB_NAME,
            help="Pushgateway job name.")
    parser.add_argument("-v", action="store_true",
            help="Print some information to stdout.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    registry = setup_metrics()
    start = time.time()
    if args.v:
        logging.info("started")
    def_labels = {'instance': socket.getfqdn()}
    process_input(def_labels)
    end = time.time()
    if args.v:
        logging.info("finished reading output.")
    gauges["rsnapshot_start"].labels(def_labels).set(start)
    gauges["rsnapshot_end"].labels(def_labels).set(end)
    gauges["rsnapshot_duration"].labels(def_labels).set(end - start)
    if args.v:
        logging.info("publishing to pushgateway @ %s", args.pushgw)
    push_to_gateway(args.pushgw, job=args.job, registry=registry)


def setup_metrics():
    registry = CollectorRegistry()
    basic_labels = ['instance']
    gauges["rsnapshot_start"] = Gauge(
        "rsnapshot_start", "Timestamp rsnapshot started at", basic_labels,
        registry=registry)
    gauges["rsnapshot_end"] = Gauge(
        "rsnapshot_end", "Timestamp rsnapshot finished at", basic_labels,
        registry=registry)
    gauges["rsnapshot_duration"] = Gauge(
        "rsnapshot_duration", "How long rsnapshot ran for", basic_labels,
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
        if line.startswith('sent '):
            s.publish(def_labels)
            s = None
            continue
        s.parse(line)


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
