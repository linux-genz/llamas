#include <linux/module.h>
#include <net/sock.h>
#include <linux/netlink.h>
#include <net/genetlink.h>
#include <linux/skbuff.h>
#include "genz_gnl.h"

/* Netlink Generic Attribute Policy */
static struct nla_policy genz_genl_policy[] = {
    [GENZ_A_GCID] = { .type = NLA_U32 },
    [GENZ_A_CCLASS] = { .type = NLA_U16 },
    [GENZ_A_UUID] = { .len = UUID_LEN },
};

static int getattrs(const char *funcname, struct genl_info *info,
		    uint32_t *GCID, uint16_t *CCLASS, uint8_t **UUID)
{
	struct nlattr *tmp;
	int errors = 0;

	pr_info("%s: cmd=%u portid=%u (0x%x) seq=%u\n", funcname,
		info->genlhdr->cmd,
		info->snd_portid,
		info->snd_portid,
		info->snd_seq);

	if (!(tmp = info->attrs[GENZ_A_GCID])) {
		pr_err("\tmissing GCID\n");
		errors++;
	} else {
		*GCID = nla_get_u32(tmp);
		pr_info("\tGCID = %u\n", *GCID);
	}

	if (!(tmp = info->attrs[GENZ_A_CCLASS])) {
		pr_err("\tmissing CCLASS\n");
		errors++;
	} else {
		*CCLASS = nla_get_u16(tmp);
		pr_info("\tCCLASS = %u\n", *CCLASS);
	}

	if (!(tmp = info->attrs[GENZ_A_UUID])) {
		pr_err("\tmissing UUID\n");
		errors++;
		*UUID = NULL;	// safe from inadvertent kfree
	} else {
		unsigned i;

		*UUID = nla_memdup(tmp, GFP_KERNEL);
		pr_info("\tUUID = ");
		for (i = 0; i < UUID_LEN; i++)
			pr_cont("%02x", *(*UUID + i));
		pr_info("\n");
		if (tmp->nla_len != UUID_LEN)
			pr_warn("\tnla length = %d\n", tmp->nla_len);
	}
	if (errors && *UUID) {
		kfree(*UUID);
		*UUID = NULL;
	}
	return errors;
}

/* Netlink Generic Handler: return 0 on success else -ESOMETHING */
static int genz_add_component(struct sk_buff *skb, struct genl_info *info)
{
    uint32_t GCID;
    uint16_t CCLASS;
    uint8_t *UUID;	// must be kfree'd
    int errors;

    errors = getattrs(__FUNCTION__, info, &GCID, &CCLASS, &UUID);
    if (UUID) kfree(UUID);
    return errors ? -ENOMSG : 0;
}

static int genz_remove_component(struct sk_buff *skb, struct genl_info *info)
{
    uint32_t GCID;
    uint16_t CCLASS;
    uint8_t *UUID;	// must be kfree'd
    int errors;

    errors = getattrs(__FUNCTION__, info, &GCID, &CCLASS, &UUID);
    if (UUID) kfree(UUID);
    return errors ? -ENOMSG : 0;
}

static int genz_symlink_component(struct sk_buff *skb, struct genl_info *info)
{
    uint32_t GCID;
    uint16_t CCLASS;
    uint8_t *UUID;	// must be kfree'd
    int errors;

    errors = getattrs(__FUNCTION__, info, &GCID, &CCLASS, &UUID);
    if (UUID) kfree(UUID);
    return errors ? -ENOMSG : 0;
}

/* Netlink Generic Operations */
static struct genl_ops genz_genl_ops[] = {
    {
    .cmd = GENZ_C_ADD_COMPONENT,
    .doit = genz_add_component,
    .policy = genz_genl_policy,
    },
    {
    .cmd = GENZ_C_REMOVE_COMPONENT,
    .doit = genz_remove_component,
    .policy = genz_genl_policy,
    },
    {
    .cmd = GENZ_C_SYMLINK_COMPONENT,
    .doit = genz_symlink_component,
    .policy = genz_genl_policy,
    },
};//genz_genl_ops

/* Netlink Generic Family Definition */
static struct genl_family genz_genl_family = {
    .name = GENZ_GENL_FAMILY_NAME,
    .version = GENZ_GENL_VERSION,
    .hdrsize = GENZ_GENL_USER_HEADER_SIZE,
    .maxattr = ARRAY_SIZE(genz_genl_policy),
    .ops = genz_genl_ops,
    .n_ops = ARRAY_SIZE(genz_genl_ops)
};//genz_genl_family

static int __init nl_init(void) {
    int ret;

    pr_info("Entering %s()\n", __FUNCTION__);
    ret = genl_register_family(&genz_genl_family);
    if (ret != 0) {
        pr_err("genl_register_family() returned %d\n", ret);
        return -1;
    }
    return 0;
}//nl_init


static void __exit nl_exit(void) {
    printk(KERN_INFO "exiting nl module\n");
    genl_unregister_family(&genz_genl_family);
}//nl_exit


module_init(nl_init); module_exit(nl_exit);

MODULE_LICENSE("GPL");

