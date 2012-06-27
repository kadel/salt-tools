'''
Work with virtual machines managed by OpenVz

'''
# Some methods are named after virt.py module for libvirt

import re


def is_openvz_hyper():
    '''
    Return a bool whether or not this node is a OpenVZ hypervizor
    '''
    return __grains__['virtual'] == 'openvzhn'


def is_openvz_ve():
    '''
    Return a bool whether or not this node is a OpenVZ container (virtual environment)
    '''
    return  __grains__['virtual'] == 'openvzve'



def _list_vms(all_ve=False):
    if all_ve:
        cmd = "vzlist -a | tail -n +2"
    else:
        cmd = "vzlist | tail -n +2"
    vms = []
    output = __salt__["cmd.run"](cmd)
    for line in output.strip().split('\n'):
        # line format: CTID NPROC STATUS IP_ADDR HOSTNAME
        ve_info = re.split('\s+',line.strip())
        vms.append({
            "ctid": ve_info[0],
            "nproc": ve_info[1],
            "status": ve_info[2],
            "ip_addr": ve_info[3],
            "hostname": ve_info[4]
        })
    return vms

def _parse_beancounters_line(line):
    # line format: resource held maxheld barrier limit failcnt
    out = {}
    values = re.split('\W+', line)
    out = {
            "held": values[1],
            "maxheld": values[2],
            "barrier": values[3],
            "limit": values[4],
            "failcnt": values[5],
           }
    return out


def list_vms():
    '''
    Return a list of virtual machine names on the minion

    CLI Example::

        salt '*' openvz.list_vms
    '''
    return _list_vms(all_ve=True)


def list_active_vms():
    '''
    Return a list of names for active virtual machine on the minion

    CLI Example::

    salt '*' openvz.list_active_vms
    '''
    return _list_vms(all_ve=False)


def get_beancounters(ve_id=None):
    '''
    Return beancounters for VE with ve_id
    If no ve_id is specified, return beancounters for all VEs on the minion

    CLI Example::

    salt '*' openvz.get_beancounters
    '''
    out = {}
    veid = None
    inp = open('/proc/user_beancounters', 'r').read()
    # skip first two lines (version and header)
    for line in inp.split('\n')[2:]:
        line = line.strip()
        # check if this is line with veid
        line_with_veid = re.match('([0-9]+):(.*)', line)
        if line_with_veid:
            #veid
            veid = line_with_veid.group(1)
            # rest of the line  (usualy kmemsize)
            out[veid]={}
            counter = re.split('\W+', line_with_veid.group(2).strip())[0]
            out[veid][counter] = _parse_beancounters_line(line_with_veid.group(2).strip())
            continue
        if len(line) == 0:
            continue
        # rest of counters
        counter = re.split('\W+', line)[0]
        out[veid][counter] = _parse_beancounters_line(line)
    # if specified return counters only for on veid
    if ve_id:
        try:
            out = out[str(ve_id)]
        except KeyError:
            out = {}
    return out
