#!/usr/bin/python3

import os
import sys
import json
import argparse
import ipaddress
import urllib.request

upstream = 'https://harvester.ffh.zone/nodes.json'
tmp_file = '/tmp/nodes.json'


def load(force_update=False):
    if not os.path.exists(tmp_file) or force_update:
        sys.stderr.write('Downloading data from {}...\n'.format(upstream))
        response = urllib.request.urlopen(upstream).read()
        with open(tmp_file, 'wb') as f:
            f.write(response)

    with open(tmp_file) as f:
        return json.loads(f.read())


def prepare(nodes):
    for n in nodes:
        nodeinfo = n['nodeinfo']
        network = nodeinfo['network']

        if 'addresses' in network:
            network['addresses'] = [ipaddress.ip_address(a)
                                    for a in network['addresses']]

    return nodes

def _check_mac_equality(a, b):
    remove_signs = lambda x: x.replace(':', '').replace('-', '')
    return remove_signs(a) == remove_signs(b)

def filter_nodes(nodes, search):
    for n in nodes:
        nodeinfo = n['nodeinfo']
        network = nodeinfo['network']

        if search.lower() in nodeinfo['hostname'].lower():
            yield n

        if _check_mac_equality(search, network['mac']):
            yield n

        try:
            ip = ipaddress.ip_address(search)

            if 'mesh_interfaces' in network \
               and ip in network['mesh_interfaces']:
                yield n

            if 'addresses' in network and ip in network['addresses']:
                yield n
        except ValueError:
            pass

        if 'mesh' in network:
            for mesh_definition in network['mesh'].values():
                for iface_macs in mesh_definition['interfaces'].values():
                    for mac in iface_macs:
                        if _check_mac_equality(search, mac):
                            yield n



def nodeinfo(node):
    nodeinfo = node['nodeinfo']
    network = nodeinfo['network']

    yield 'hostname', nodeinfo['hostname']
    yield 'primary-mac', network['mac']

    if 'addresses' in network:
        for addr in network['addresses']:
            if str(addr).startswith('fe80'):
                yield 'll-addr', addr
            else:
                yield 'addr', addr

    if 'mesh' in network:
        for mesh_name, mesh_definition in network['mesh'].items():
            for iface_name, iface_macs in mesh_definition['interfaces'].items():
                for mac in iface_macs:
                    yield 'secondary-mac', mac + ' (' + iface_name + ')'

    if 'hardware' in nodeinfo:
        yield 'model', nodeinfo['hardware']['model']

    if 'software' in nodeinfo:
        software = nodeinfo['software']

        if 'fastd' in software:
            yield 'fastd_enabled', ('true'
                                    if 'enabled' in software['fastd'] and software['fastd']['enabled']
                                    else 'false')


def print_nodeinfo(nodeinfo):
    for n in nodeinfo:
        print('{:>15}: {}'.format(*n))


def information_printer(information):
    def print_it(nodeinfo):
        for k, v in nodeinfo:
            if k != information:
                continue
            print(v)
    return print_it

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-f', dest='filter', default=None,
                        metavar='MAC/IPv6/HOSTNAME',
                        help="filter for a specific node")
    parser.add_argument('-u', dest='force_update', default=False,
                        action='store_true',
                        help="force update data from upstream")
    parser.add_argument('-i', dest='information', default=None,
                        metavar='NAME',
                        help="display only a single information "
                        "machine readable")

    args = parser.parse_args()

    data = load(args.force_update)
    nodes = data['nodes'] #.values()
    nodes = prepare(nodes)

    if args.filter is not None:
        nodes = filter_nodes(nodes, args.filter)

    human = args.information is None

    def line():
        print('-'*60)

    if args.information is None:
        printer = print_nodeinfo
    else:
        printer = information_printer(args.information)

    for n in nodes:
        if human:
            line()
        printer(nodeinfo(n))
    if human:
        line()
