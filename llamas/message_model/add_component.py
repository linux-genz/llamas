from pyroute2.netlink import nla, genlmsg


# class ModelAddComponent(genlmsg):
#     """
#         The set of all Netlink Attributes (NLAs) that could be passed.
#     This is the analog of the kernel "struct nla_policy".
#     """

#     # Zero-based arrays are sort-of needed here, but also somewhat frowned
#     # upon. This needs further research, maybe in pyroute2 itself.
#     nla_map = None

#     class resources(nla):
#         nla_map = None

#         class resource_entry(nla):
#             nla_map = None

#             class mrl(nla):
#                 nla_map = None

#                 class mrl_entry(nla):
#                     nla_map = None

class ModelAddComponent(genlmsg):
    """
        The set of all Netlink Attributes (NLAs) that could be passed.
    This is the analog of the kernel "struct nla_policy".
    """

    # Zero-based arrays are sort-of needed here, but also somewhat frowned
    # upon. This needs further research, maybe in pyroute2 itself.
    nla_map = (
        ('UnUsed',             'none'),
        ('GENZ_A_BRIDGE_GCID', 'uint32'),
        ('GENZ_A_GCID',        'uint32'),
        ('GENZ_A_CCLASS',      'uint16'),
        ('GENZ_A_FRU_UUID',    'string'),
        ('GENZ_A_MGR_UUID',    'string'),
        ('GENZ_A_CUUID',       'string'),
        ('GENZ_A_SERIAL',      'uint64'),
        ('GENZ_A_RESOURCE_LIST', 'resources'),
    ),


    class resources(nla):
        nla_map = (
            ('GENZ_A_UL_UNSPEC', 'none'),
            ('GENZ_A_UL', 'resource_entry')
        )

        class resource_entry(nla):
            nla_map = (
                ('GENZ_A_UL_UNSPEC', 'none'),
                ('GENZ_A_U_CLASS_UUID', 'string'),
                ('GENZ_A_U_INSTANCE_UUID', 'string'),
                ('GENZ_A_U_FLAGS', 'uint64'),
                ('GENZ_A_U_CLASS', 'uint16'),
                ('GENZ_A_U_MRL', 'mrl'),
                ('GENZ_A_U_REFERENCE_UUID', 'string'),
            )


            class mrl(nla):
                nla_map = (
                    ('GENZ_A_MRL_UNSPEC', 'none'),
                    ('GENZ_A_MRL', 'mrl_entry')
                )

                class mrl_entry(nla):
                    nla_map = (
                        ('GENZ_A_MR_UNSPEC', 'none'),
                        ('GENZ_A_MR_START', 'uint64'),
                        ('GENZ_A_MR_LENGTH', 'uint64'),
                        ('GENZ_A_MR_TYPE', 'uint8'),
                        ('GENZ_A_MR_RO_RKEY', 'uint32'),
                        ('GENZ_A_MR_RW_RKEY', 'uint32'),
                    )
