#include <linux/module.h>
#include <net/sock.h>
#include <linux/netlink.h>
#include <net/genetlink.h>
#include <linux/skbuff.h>
#include "genz_gnl.h"


/* Netlink Generic Attribute Policy */
static struct nla_policy genz_genl_policy[GENZ_A_MAX + 1] = {
    [GENZ_A_GCID] = { .type = NLA_U32 },
    [GENZ_A_CCLASS] = { .type = NLA_U16 },
    [GENZ_A_UUID] = { .len = UUID_LEN },
};

/* Netlink Generic Handler: return 0 on success else -ESOMETHING */
static int genz_add_component(struct sk_buff *skb, struct genl_info *info){
    int retval = 0;

    pr_info("%s: message from port ID %u\n", __FUNCTION__, info->snd_portid);
    if (!info->attrs[GENZ_A_GCID]) {
        pr_err("\tmissing GCID\n");
	retval = -ENOMSG;
    } else
	pr_info("\tGCID = %d\n", nla_get_u32(info->attrs[GENZ_A_GCID]));

    if (!info->attrs[GENZ_A_CCLASS]) {
        pr_err("\tmissing CCLASS\n");
	retval = -ENOMSG;
    } else
        pr_info("\tC-Class = %u\n", nla_get_u32(info->attrs[GENZ_A_CCLASS]));
    
    if (!info->attrs[GENZ_A_UUID]) {
        pr_err("\tmissing UUID\n");
	retval = -ENOMSG;
    } else {
        uint8_t * uuid;

        uuid = nla_data(info->attrs[GENZ_A_UUID]);
        pr_info("\tUUID @ 0x%p\n", uuid);
    }
    return retval;
}//genz_add_component


static int genz_remove_component(struct sk_buff *skb, struct genl_info *info){
    /*
     * message handling code goes here; return 0 on success,
     * negative value on failure.
     */
    pr_info("Remove component\n");
    return 0;
}//genz_remove_component


static int genz_symlink_component(struct sk_buff *skb, struct genl_info *info){
    /*
     * message handling code goes here; return 0 on success,
     * negative value on failure.
     */
    pr_info("Symlink component\n");
    return 0;
}//genz_symlink_component


/* Netlink Generic Operations */
static struct genl_ops genz_gnl_ops[] = {
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
};//genz_gnl_ops


/* Netlink Generic Family Definition */
static struct genl_family genz_gnl_family = {
    .hdrsize = 0,
    .name = GENZ_FAMILY_NAME,
    .version = 1,
    .maxattr = GENZ_A_MAX,
    .ops = genz_gnl_ops,
    .n_ops = ARRAY_SIZE(genz_gnl_ops)
};//genz_gnl_family


static int __init nl_init(void) {
    int ret;

    printk(KERN_INFO "Entering: %s\n",__FUNCTION__);
    ret = genl_register_family(&genz_gnl_family);
    if (ret != 0) {
        printk(KERN_INFO "genl_register_family returned %d\n", ret);
        return -1;
    }

    return 0;
}//nl_init


static void __exit nl_exit(void) {
    printk(KERN_INFO "exiting nl module\n");
    genl_unregister_family(&genz_gnl_family);
}//nl_exit


module_init(nl_init); module_exit(nl_exit);

MODULE_LICENSE("GPL");

