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
import datetime
import filecmp
import hashlib

tmp_dir = '/tmp/os-grab-config'

def _exec_cmd(cmd):
    """ exec command without shell """
    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    response = process.communicate()[0]
    return response

def _exec_shell_cmd(cmd):
    """ execute shell command """
    shell = subprocess.Popen(cmd,
                                shell=True)
    return shell.wait()

class Logger(object):
    """ Std logger"""

    _log_level = 'DEBUG'

    def __init__(self, log_dir=tmp_dir):
        self.log = open("%s/diff.log" % (log_dir), 'a+')

    def log(self, *args):
        line = str(datetime.datetime.now())
        for arg in args:
            line += ' ' + str(arg)
        self.log.write("%s\n" % line)
        self.log.flush()

class Grab(object):

    os_services = ['nova', 'neutron']

    def _make_tmp(self):
        if not os.path.exists(tmp_dir):
            os.mkdir(tmp_dir)

    def get_conf_files(self, os_service, config_dir='/etc'):
        for (dirpath, dirnames, files) in walk(config_dir):
            if os_service in dirpath:
                for file in files:
                    shutil.copy("%s/%s" % (dirpath, file), "%s/%s" % (tmp_dir, file))

    def make_tar(self, tar_name='config.tar.gz', dir=tmp_dir):
        with tarfile.open("%s/%s" % (dir, tar_name), "w:gz") as tar:
            tar.add(dir, arcname=os.path.basename(dir))

    def grab(self):
        # make temp dir
        self._make_tmp()
        # get conf per service
        for service in self.os_services:
            self.get_conf_files(service)
        self.make_tar()

class Diff(object):

    def __init__(self, working_dir=None):
        if working_dir is None:
            self.wdir = os.curdir
        else:
            self.wdir = working_dir

    def preprocess(self, file):
        pass
        #sed -e "s/#.*$//" -e "/^$/d" testfiles/nova.conf
        #sed -i "s/#.*$//" testfiles/nova.conf && sed -i "/^$/d" testfiles/nova.conf

    def diff(self, path1, path2):
        # compare dir
        dircmp = filecmp.dircmp(path1, path2)
        # missing files
        missing_files = dircmp.left_only
        for missing in missing_files:
            self.dumpfile(missing, path1)
        # new files
        new_files = dircmp.right_only
        for new in new_files:
            self.dumpfile(new, path2, missing=False)
        files = dircmp.same_files
        for f in files:
            if not self.md5cmp("%s/%s" % (path1, f),"%s/%s" % (path2, f)):
                out = open("%s/%s.diff" % (self.wdir, f), 'w')
                with open("%s/%s" % (path1, f), 'rb') as f1, open("%s/%s" % (path2, f), 'rb') as f2:
                    # @TODO remove comment
                    l1 = f1.readlines()
                    l2 = f2.readlines()
                    for line in l1:
                        if not line in l2:
                            out.write("-%s" % (line))
                    for line in l2:
                        if not line in l1:
                            out.write("+%s" % (line))
                out.flush()

    def dumpfile(self, filename, path, missing=True):
        """ dumpfile with missing statement (+ or -) """
        with open("%s/%s" % (path, filename), 'rb') as stream:
            f = open("%s/%s.diff" % (self.wdir, filename), 'w')
            for l in stream.readlines():
                if missing:
                    f.write("-%s" % l)
                else:
                    f.write("+%s" % l)
                f.flush()

    def md5cmp(self, fIn, fOut):
        """ compare md5sum """
        if self._md5(fIn)[1] == self._md5(fOut)[1]:
            return True
        return False

    def _md5(self, file):
        """ generate a md5sum for <file> """
        return [file, hashlib.sha256(open(file, 'rb').read()).digest()]

if __name__ == '__main__':
    d = Diff()
    path1 = "testfiles/org"
    path2 = "testfiles/new"
    d.diff(path1, path2)