# resolve.py
A nodes.json command line data tool

<pre>
usage: resolve [-h] [-f MAC/IPv6/HOSTNAME/BRANCH/FW_VERSION] [-m MODEL] [-c] [-i NAME] [--gen-bat-hosts]

optional arguments:
  -h, --help            show this help message and exit
  -f MAC/IPv6/HOSTNAME/BRANCH/FW_VERSION
                        filter for specific nodes
  -m MODEL              filter for specific nodes by hardware model
  -c                    try to use cached nodes json (from previous run of this tool)
  -i NAME               display only a single information machine readable
  --gen-bat-hosts       generate a /etc/bat-hosts file
</pre>
