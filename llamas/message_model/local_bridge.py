from pyroute2.netlink import nla, genlmsg


class ModelLocalBridge(genlmsg):
    """
        The set of all Netlink Attributes (NLAs) that could be passed.
    This is the analog of the kernel "struct nla_policy".
    """

    nla_map = (
        ('UnUsed',                 'none'),
        ('GENZ_A_FC_GCID',         'uint32'),
        ('GENZ_A_FC_BRIDGE_GCID',  'uint32'),
        ('GENZ_A_FC_TEMP_GCID',    'uint32'),
        ('GENZ_A_FC_DR_GCID',      'uint32'),
        ('GENZ_A_FC_DR_INTERFACE', 'uint16'),
        ('GENZ_A_FC_MGR_UUID',     'string'),
    ),
