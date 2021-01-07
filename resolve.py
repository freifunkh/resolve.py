#!/usr/bin/python3

import os
import sys
import json
import argparse
import datetime
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

        if search == n['nodeinfo']['software']['firmware']['release']:
            yield n

        if 'autoupdater' in n['nodeinfo']['software'] and search == n['nodeinfo']['software']['autoupdater'].get('branch', 'None'):
            yield n

        if search.lower().startswith('=='):
            if search[2:].lower() == nodeinfo['hostname'].lower():
                yield n

        if search.lower() in nodeinfo['hostname'].lower():
            yield n

        if _check_mac_equality(search, network['mac']):
            yield n


        if network is not None:
            try:
                ip = ipaddress.ip_address(search)

                if 'mesh_interfaces' in network \
                   and network['mesh_interfaces'] is not None \
                   and ip in network['mesh_interfaces']:
                    yield n

                if 'addresses' in network and ip in network['addresses']:
                    yield n
            except ValueError:
                pass

        if 'mesh' in network and network['mesh'] is not None:
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
    nodeid = network['mac'].replace(':', '')
    yield 'node-id', nodeid
    yield 'map-link', 'https://hannover.freifunk.net/karte/#/de/map/{}'.format(nodeid)
    yield 'stats-link', 'https://stats.ffh.zone/d/000000021/router-fur-meshviewer?var-node={}'.format(nodeid)

    yield 'online', str(node['flags']['online'])

    if 'addresses' in network:
        for addr in network['addresses']:
            if str(addr).startswith('fe80'):
                yield 'll-addr', addr
            else:
                yield 'addr', addr

    yield 'lastseen', node['lastseen']

    if 'mesh' in network and network['mesh'] is not None:
        for mesh_name, mesh_definition in network['mesh'].items():
            for iface_name, iface_macs in mesh_definition['interfaces'].items():
                for mac in iface_macs:
                    yield 'secondary-mac', mac + ' (' + iface_name + ')'

    if 'hardware' in nodeinfo and 'model' in nodeinfo['hardware']:
        yield 'model', nodeinfo['hardware']['model']

    if 'owner' in nodeinfo and nodeinfo['owner'] is not None and 'contact' in nodeinfo['owner']:
        yield 'owner', nodeinfo['owner']['contact']

    if 'system' in nodeinfo and 'site_code' in nodeinfo['system']:
        yield 'site_code', nodeinfo['system']['site_code']

    if 'software' in nodeinfo:
        software = nodeinfo['software']

        if 'fastd' in software:
            yield 'fastd_enabled', ('true'
                                    if 'enabled' in software['fastd'] and software['fastd']['enabled']
                                    else 'false')

        if 'firmware' in software and software['firmware'] is not None:
            if 'base' in software['firmware'] and software['firmware']['base'] is not None:
                yield 'firmware_base', software['firmware']['base']
            yield 'firmware_rel', software['firmware']['release']

        if 'autoupdater' in software and software['firmware'] is not None:
            yield 'autoupdater_br', software['autoupdater'].get('branch', 'None')
            yield 'autoupdater_en', software['autoupdater'].get('enabled', False)

    statistics = node['statistics']

    connected_peers = []

    if 'mesh_vpn' in statistics:
        mesh_vpn = statistics['mesh_vpn']
        if 'groups' in mesh_vpn:
            bb_peers = mesh_vpn['groups']['backbone']['peers']

            for name, conn in bb_peers.items():
                if conn is None:
                    continue

                yield 'fastd_sn', name

                connected_peers += [name]
        if 'peers' in mesh_vpn:
            bb_peers = mesh_vpn['peers']

            for name, conn in bb_peers.items():
                if conn is None:
                    continue

                yield 'fastd_sn', name

                connected_peers += [name]

    gw = None

    if 'uptime' in statistics:
        yield 'uptime', "{}".format(datetime.timedelta(seconds=int(statistics['uptime'])))

    gw_macs = {}
    for i in range(0, 256):
        gw_macs.update({
            '88:e6:40:ba:10:%02x' % i: 'sn01',
            '88:e6:40:ba:20:%02x' % i: 'sn02',
            '88:e6:40:ba:30:%02x' % i: 'sn03',
            '88:e6:40:ba:40:%02x' % i: 'sn04',
            '88:e6:40:ba:50:%02x' % i: 'sn05',
            '88:e6:40:ba:60:%02x' % i: 'sn06',
            '88:e6:40:ba:70:%02x' % i: 'sn07',
            '88:e6:40:ba:80:%02x' % i: 'sn08',
            '88:e6:40:ba:90:%02x' % i: 'sn09',
            '88:e6:40:ba:a0:%02x' % i: 'sn10'
        })
        gw_macs.update({
            '88:e6:40:20:10:%02x' % i: 'sn01',
            '88:e6:40:20:20:%02x' % i: 'sn02',
            '88:e6:40:20:30:%02x' % i: 'sn03',
            '88:e6:40:20:40:%02x' % i: 'sn04',
            '88:e6:40:20:50:%02x' % i: 'sn05',
            '88:e6:40:20:60:%02x' % i: 'sn06',
            '88:e6:40:20:70:%02x' % i: 'sn07',
            '88:e6:40:20:80:%02x' % i: 'sn08',
            '88:e6:40:20:90:%02x' % i: 'sn09',
            '88:e6:40:20:a0:%02x' % i: 'sn10'
        })

    if 'gateway' in statistics:

        mac = statistics['gateway']

        if mac in gw_macs:
            gw = gw_macs[mac]
        else:
            gw = 'unknown mac! (' + mac + ')'

        yield 'dhcp_gateway', gw

        rep = lambda x: x.replace('gw', '').replace('sn', '')

        if len(connected_peers) != 0:

            if rep(gw) in map(rep, connected_peers):
                yield 'gw_eq_fastd', 'true'
            else:
                yield 'gw_eq_fastd', 'false'

    if 'gateway6' in statistics:

        mac = statistics['gateway6']

        if mac in gw_macs:
            gw = gw_macs[mac]
        else:
            gw = 'unknown mac! (' + mac + ')'

        yield 'radv_gateway', gw

def print_nodeinfo(nodeinfo):
    for n in nodeinfo:
        print('{:>15}: {}'.format(*n))

def print_bat_hosts(nodeinfo):
    hostname = None
    i = 0
    for k, v in nodeinfo:
        if k == 'hostname':
            hostname = v.replace(' ','_')
        if k == 'secondary-mac':
            i += 1
            t = v.split(' ')[1][1]
            print(v.split(' ')[0], hostname+'_'+'('+t+')'+str(i))

def information_printer(information):
    def print_it(nodeinfo):
        for k, v in nodeinfo:
            if k != information:
                continue
            print(v)
    return print_it

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-f', dest='filter', type=str, action='append', default=[],
                        metavar='MAC/IPv6/HOSTNAME/BRANCH/FW_VERSION',
                        help="filter for specific nodes")
    parser.add_argument('-u', dest='force_update', default=False,
                        action='store_true',
                        help="force update data from upstream")
    parser.add_argument('-i', dest='information', default=None,
                        metavar='NAME',
                        help="display only a single information "
                        "machine readable")
    parser.add_argument('--gen-bat-hosts', dest='gen_bat_hosts', default=False,
                        action='store_true',
                        help='generate a /etc/bat-hosts file')

    args = parser.parse_args()

    data = load(args.force_update)
    nodes = data['nodes'] #.values()
    nodes = prepare(nodes)

    for f in args.filter:
        nodes = filter_nodes(nodes, f)

    human = args.information is None

    def line():
        print('-'*60)

    if args.gen_bat_hosts:
        printer = print_bat_hosts
        human = False
    elif args.information is None:
        printer = print_nodeinfo
    else:
        printer = information_printer(args.information)

    for n in nodes:
        if human:
            line()
        printer(nodeinfo(n))
    if human:
        line()
