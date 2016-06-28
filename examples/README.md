Examples:
========

This example show a diff from a tripleo Undercloud config between Liberty and Mitaka:


Services backuped: nova neutron glance heat keystone and mysql

Command lines:

```
python diff-tool.py backup -s nova,neutron,glance,heat,keystone,my.cnf.d -w /home/stack/uc-conf-liberty/

yum update -y

python diff-tool.py backup -s nova,neutron,glance,heat,keystone,my.cnf.d -w /home/stack/uc-conf-mitaka/

python diff-tool.py diff -o /home/stack/uc-conf-liberty/ -n /home/stack/uc-conf-mitaka/ -w /home/stack/diff-dir
```

The output of the diff between the both config is under ~/diff-dir
