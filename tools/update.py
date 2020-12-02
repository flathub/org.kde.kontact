#!/bin/python3

"""
Tool to automatically update KDE packages in flatpak manifests
"""

import argparse
import json
from math import ceil
import hashlib
import tempfile
import subprocess
import sys
import requests
from tqdm import tqdm
import yaml

def build_url(product, name, version, porting_aids=False):
    url = 'https://download.kde.org'
    if product == 'frameworks':
        short_version = '.'.join(version.split('.')[0:2])
        if porting_aids:
            product_url = f'stable/frameworks/{short_version}/portingAids'
        else:
            product_url = f'stable/frameworks/{short_version}'
    elif product == 'applications':
        stream = 'unstable' if version.endswith('.90') else 'stable'
        product_url = f'{stream}/release-service/{version}/src'

    return f'{url}/{product_url}/{name}-{version}.tar.xz'


def download_tarball(new_url):
    print('Downloading %s' % new_url)
    request = requests.get(new_url, stream = True)
    request.raise_for_status()
    total_size = int(request.headers.get('content-length', 0))
    block_size = 4096
    written = 0
    buffer = bytes()
    checksum = hashlib.new('sha256')
    for data in tqdm(request.iter_content(block_size), total=ceil(total_size/block_size), unit='KB',
                     unit_scale = True):
        written += len(data)
        checksum.update(data)
        buffer += data
    if total_size not in (0, written):
        print("File download failed, size mismatch (%d/%d)" % (written, total_size))
        sys.exit(1)

    return (buffer, checksum)

def verify_signature(new_url, buffer):
    sig = requests.get(new_url + '.sig')
    sig.raise_for_status()
    with tempfile.NamedTemporaryFile(mode='w') as sigfile:
        sigfile.write(sig.text)
        sigfile.flush()

        gpg = subprocess.Popen(['gpg2', '--verify', sigfile.name, '-'],
                               stdin = subprocess.PIPE, stdout = None,
                               stderr = subprocess.PIPE)
        gpg.stdin.write(buffer)
        gpg.stdin.close()
        gpg.wait()
        if gpg.returncode != 0:
            print("Failed to verify GPG signature")
            print(gpg.stderr.read().decode())
            sys.exit(1)

def update_source(source, new_url):
    buffer, checksum = download_tarball(new_url)
    verify_signature(new_url, buffer)

    source['url'] = new_url
    source['sha256'] = checksum.hexdigest()

def update_applications_url(source, name, version):
    new_url = build_url('applications', name, version)
    update_source(source, new_url)

def update_frameworks_url(source, name, version):
    new_url = build_url('frameworks', name, version, porting_aids='portingAids' in source['url'])
    update_source(source, new_url)

def update_modules(args, modules):
    for module in modules:
        # Skip external submodules
        if isinstance(module, str):
            continue
        sources = module['sources']
        for source in sources:
            if source['type'] != 'archive':
                continue
            if '/applications/' in source['url']:
                update_applications_url(source, module['name'], args.version)
            elif '/frameworks/' in source['url']:
                update_frameworks_url(source, module['name'], args.kf5version)
        if 'modules' in module:
            update_modules(args, module['modules'])

def update_json_file(args, filename):
    with open(filename, 'r', encoding='utf-8') as infile:
        manifest = json.load(infile)
        update_modules(args, manifest['modules'])

    with open(filename, 'w', encoding='utf-8') as outfile:
        json.dump(manifest, outfile, indent=4, ensure_ascii = False)

def update_yaml_file(args, filename):
    with open(filename, 'r', encoding='utf-8') as infile:
        manifest = yaml.load(infile, Loader=yaml.Loader)
        update_modules(args, manifest['modules'])

    with open(filename, 'w', encoding='utf-8') as outfile:
        outfile.write(yaml.dump(manifest, Dumper=yaml.Dumper))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', action='store', required=True, dest='version')
    parser.add_argument('-k', '--kf5version', action='store', required=True, dest='kf5version')
    parser.add_argument('file', action='store')

    args = parser.parse_args()
    if args.file.endswith('.json'):
        update_json_file(args, args.file)
    elif args.file.endswith('.yaml'):
        update_yaml_file(args, args.file)
    else:
        raise RuntimeError("Unrecognized manifest file type")

if __name__ == "__main__":
    main()
