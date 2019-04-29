
#define GENZ_GENL_FAMILY_NAME 		"genz_cmd"
#define GENZ_GENL_VERSION		1
#define GENZ_GENL_USER_HEADER_SIZE	0
#define UUID_LEN			16	/* array of uint8_t */

/* Netlink Generic Message Attributes */
enum {
	asdf,
	GENZ_A_GCID,
	GENZ_A_CCLASS,
	GENZ_A_UUID,
};

/* user_send attributes to consolidate parameters received by kernel. */
struct MsgProps {
    char* gcid;
    char* cclass;
    char* uuid;
};

/* Netlink Generic Commands */
enum {
	GENZ_C_ADD_COMPONENT,
	GENZ_C_REMOVE_COMPONENT,
	GENZ_C_SYMLINK_COMPONENT,
};
