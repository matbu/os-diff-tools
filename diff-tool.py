#! /usr/bin/env python
# -*- coding: UTF-8 -*-
"""
    Product name: diff tool
    Copyright (C) matbu 2016
    Author(s): Mathieu BULTEL
    Description : Grab Openstack config and make diff
"""

from os import walk
import os
import shutil
import tarfile

os_services = ['nova', 'neutron']
tmp_dir = '/tmp/os-grab-config'

def _make_tmp():
    if not os.path.exists(tmp_dir):
        os.mkdir(tmp_dir)

def get_conf_files(os_service, config_dir='/etc'):
    for (dirpath, dirnames, files) in walk(config_dir):
        if os_service in dirpath:
            for file in files:
                shutil.copy("%s/%s" % (dirpath, file), "%s/%s" % (tmp_dir, file))

def make_tar(tar_name='config.tar.gz', dir=tmp_dir):
    with tarfile.open("%s/%s" % (dir, tar_name), "w:gz") as tar:
        tar.add(dir, arcname=os.path.basename(dir))

def grab():
    # make temp dir
    _make_tmp()
    # get conf per service
    for service in os_services:
        get_conf_files(service)
    make_tar()

if __name__ == '__main__':
    grab()
