#!/bin/python3

import argparse
import requests
import json
import hashlib
import sys
import subprocess
import os
import yaml
from math import ceil
from tqdm import tqdm

def update_source(source, name, version, new_url):
    print('Downloading %s' % new_url)
    r = requests.get(new_url, stream = True)
    total_size = int(r.headers.get('content-length', 0))
    block_size = 4096
    wrote = 0
    buffer = bytes()
    checksum = hashlib.new('sha256')
    for data in tqdm(r.iter_content(block_size), total=ceil(total_size/block_size), unit='KB', unit_scale = True, ):
        wrote += len(data)
        checksum.update(data)
        buffer += data
    if total_size !=0 and wrote != total_size:
        print("File download failed, size mismatch (%d/%d)" % (wrote, total_size))
        exit(1)

    sig = requests.get(new_url + '.sig')
    sigfilename = '/tmp/%s.sig' % name
    with open(sigfilename, 'w') as sigfile:
        sigfile.write(sig.text)

    gpg = subprocess.Popen(['gpg2', '--verify', sigfilename, '-'],
                           stdin = subprocess.PIPE, stdout = None,
                           stderr = subprocess.PIPE)
    gpg.stdin.write(buffer)
    gpg.stdin.close()
    gpg.wait()
    if gpg.returncode != 0:
        print("Failed to verify GPG signature")
        print(gpg.stderr.read().decode())
        exit(1)

    source['url'] = new_url
    source['sha256'] = checksum.hexdigest()

def update_applications_url(source, name, new_version):
    new_url = 'https://download.kde.org/stable/applications/%s/src/%s-%s.tar.xz' % (new_version, name, new_version)
    update_source(source, name, new_version, new_url)

def update_frameworks_url(source, name, new_version):
    short_version =  '.'.join(new_version.split('.')[0:2])
    if 'portingAids' in source['url']:
        new_url = 'https://download.kde.org/stable/frameworks/%s/portingAids/%s-%s.tar.xz' % (short_version, name, new_version)
    else:
        new_url = 'https://download.kde.org/stable/frameworks/%s/%s-%s.tar.xz' % (short_version, name, new_version)
    update_source(source,  name, new_version, new_url)

def update_modules(args, modules):
    for module in modules:
        # Skip external submodules
        if isinstance(module, str):
            continue
        sources = module['sources']
        for source in sources:
            if source['type'] != 'archive':
                continue
            if source['url'].startswith('https://download.kde.org/stable/applications'):
                source = update_applications_url(source, module['name'], args.version)
            elif source['url'].startswith('https://download.kde.org/stable/frameworks'):
                source = update_frameworks_url(source, module['name'], args.kf5version)
        if 'modules' in module:
            update_modules(args, module['modules'])

def update_json_file(args, filename):
    with open(filename, 'r', encoding='utf-8') as infile:
        j = json.load(infile)
        update_modules(args, j['modules'])

    with open(filename, 'w', encoding='utf-8') as outfile:
        json.dump(j, outfile, indent=4, ensure_ascii = False)

def update_yaml_file(args, filename):
    with open(filename, 'r', encoding='utf-8') as infile:
        y = yaml.load(infile, Loader=yaml.Loader)
        update_modules(args, y['modules'])

    with open(filename, 'w', encoding='utf-8') as outfile:
        outfile.write(yaml.dump(y, Dumper=yaml.Dumper))

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
