
/* Netlink Generic Attributes */
enum {
	GENZ_A_UNSPEC,
	GENZ_A_GCID,
	GENZ_A_CCLASS,
	GENZ_A_UUID,
	__GENZ_A_MAX,
};


/* Message Props used in user_send to consolidate parameters received by kernel. */
struct MsgProps {
    char* uuid;
    char* cclass;
    char* gcid;
};

#define GENZ_A_MAX (__GENZ_A_MAX - 1)

/* Netlink Generic Commands */
enum {
	GENZ_C_ADD_COMPONENT,
	GENZ_C_REMOVE_COMPONENT,
	GENZ_C_SYMLINK_COMPONENT,
	__GENZ_C_MAX,
};
#define GENZ_C_MAX (__GENZ_C_MAX - 1)

#define UUID_LEN	16	/* 16 uint8_t's */

#define NLINK_MSG_LEN 1024
#define GENZ_FAMILY_NAME "genz_cmd"
// #define GENZ_FAMILY_NAME "NETLINK_USERSOCK"
