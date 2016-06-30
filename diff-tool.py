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
import argparse
import subprocess
import datetime

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

def _make_working_dir(working_dir):
    if not os.path.exists(working_dir):
        os.mkdir(working_dir)

class Report(object):
    """ Report class """

    _header = """
    Start diff at : %s\n

    This file show the diff report between:\n
    %s \n
    and: \n
    %s \n
    Report:\n
    """

    _report_tpl = """
    Diff report:
        Total of diffs found: %s

    Diff found in:
    %s

    Details:
        File: %s
            %s
"""

    def __init__(self, log_dir):
        self.log_dir = log_dir
        self.log = open("%s/log.log" % (log_dir), 'a+')

    def init_report(self, path1, path2):
        # init report
        report = open("%s/report.log" % (self.log_dir), 'a+')
        report.write(self._header % (str(datetime.datetime.now()), path1, path2))
        report.flush()

    def generate_report(self):
        pass

    def write(self, *args):
        line = ''
        for arg in args:
            line += ' ' + str(arg)
        self.log.write("%s\n" % line)
        self.log.flush()

class Grabber(object):

    def __init__(self, services, tmp_dir):
        self.os_services = services
        self.tmp_dir = tmp_dir

    def get_conf_files(self, os_service, config_dir='/etc'):
        for (dirpath, dirnames, files) in walk(config_dir):
            if os_service in dirpath:
                for file in files:
                    shutil.copy("%s/%s" % (dirpath, file), "%s/%s" % (self.tmp_dir, file))

    def make_tar(self, dir, tar_name):
        with tarfile.open("%s/%s" % (dir, tar_name), "w:gz") as tar:
            tar.add(dir, arcname=os.path.basename(dir))

    def grab(self, tar_name):
        # make temp dir
        _make_working_dir(self.tmp_dir)
        # get conf per service
        for service in self.os_services:
            self.get_conf_files(service)
        self.make_tar(self.tmp_dir, tar_name)

class Diff(object):

    def __init__(self, working_dir):
        self.wdir = working_dir
        _make_working_dir(self.wdir)
        self.report = Report(self.wdir)

    def preprocess(self, file):
        pass
        #sed -e "s/#.*$//" -e "/^$/d" testfiles/nova.conf
        #sed -i "s/#.*$//" testfiles/nova.conf && sed -i "/^$/d" testfiles/nova.conf

    def diff(self, path1, path2, format="path"):
        self.report.init_report(path1, path2)
        if "tar" in format:
            path1 = self.untarconfig(path1, "%s/path1" % self.wdir)
            path2 = self.untarconfig(path2, "%s/path2" % self.wdir)
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
                self.report.write("\n\n%s" % (f))
                out = open("%s/%s.diff" % (self.wdir, f), 'w')
                with open("%s/%s" % (path1, f), 'rb') as f1, open("%s/%s" % (path2, f), 'rb') as f2:
                    # @TODO remove comment
                    l1 = f1.readlines()
                    l2 = f2.readlines()
                    for line in l1:
                        if not line in l2:
                            l = "-%s" % (line)
                            out.write(l)
                            self.report.write(l)
                    for line in l2:
                        if not line in l1:
                            l = "+%s" % (line)
                            out.write(l)
                            self.report.write(l)
                out.flush()

    def untarconfig(self, file, extract_dir):
        with tarfile.open(file) as tar:
            tar.extractall(extract_dir)
            return "%s/%s" % (extract_dir, tar.getmembers()[0].name)

    def dumpfile(self, filename, path, missing=True):
        """ dumpfile with missing statement (+ or -) """
        with open("%s/%s" % (path, filename), 'rb') as stream:
            f = open("%s/%s.diff" % (self.wdir, filename), 'w')
            self.report.write("\n\n%s/%s" % (path, filename))
            for l in stream.readlines():
                if missing:
                    line = "-%s" % l
                else:
                    line = "+%s" % l
                self.report.write(line)
                f.write(line)
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

    description = """
    This tool give you a way to backup your Openstack config and make a diff on it

    example:
    sudo python diff-tool.py backup -s nova,neutron,glance -w /tmp/os-diff-tools-new/
    sudo python diff-tool.py diff -o /tmp/os-diff-tools -n /tmp/os-diff-tools-new/ -w /tmp/diff-dir
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("action", help="action to do: backup config or make a diff", choices=["backup","diff"])
    parser.add_argument("-o", "--original", help="path of original files is case of the diff option has been choose", default=None)
    parser.add_argument("-n", "--new", help="path of new files is case of the diff option has been choose", default=None)
    parser.add_argument("-s", "--services", help="services to backup, comma delimiter", default=None)
    parser.add_argument("-w", "--workingdir", help="tmp working where the tool will put files", default="/tmp/os-diff-tools")
    parser.add_argument("-t", "--tar", help="name of the tar file", default="config.tar.gz")
    parser.add_argument("-f", "--format", help="format of the input for diff action, could be <path> or <tar>", default="path")
    args = parser.parse_args()

    services = args.services
    tmp_dir = args.workingdir
    tar_name = args.tar
    original_path = args.original
    new_path = args.new
    action = args.action
    format = args.format

    if services is not None:
        services = services.split(",")

    if action == "diff" and original_path is None and new_path is None:
        print "Error, when you select backup action, you need to give an original path and a new path"
        parser.print_usage()
        parser.exit()

    if "diff" in action:
        diff = Diff(tmp_dir)
        diff.diff(original_path, new_path, format)
        print "Done, the diff between %s and %s has been done under %s" % (original_path, new_path, tmp_dir)

    if "backup" in action:
        if services is None:
            print "No services provided, exiting"
            parser.exit()
        else:
            g = Grabber(services, tmp_dir)
            g.grab(tar_name)
