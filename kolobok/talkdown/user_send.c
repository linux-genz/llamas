#include <sys/socket.h>
#include <linux/netlink.h>
#include <stdio.h>
#include <malloc.h>
#include <string.h>
#include <unistd.h>
#include <netlink/msg.h>
#include <netlink/attr.h>
#include <sys/time.h>
#include <errno.h>
#include <ctype.h>
#include <netlink/genl/genl.h>
#include <netlink/genl/ctrl.h>
#include "genz_gnl.h"

static char *message = "add@media,gcid=23,serial_number=sssjjkkh90,c-uuid=abdc-dkkl-sdkla-ppsk";
static uint32_t gcid = 58;
static uint16_t cclass = 13;
static uint8_t uuid[16] = {0x48, 0x13, 0xea, 0x5f, 0x07, 0x4e, 0x4b, 0xe2, 0xa3, 0x55, 0xa3, 0x54, 0x14, 0x5c, 0x99, 0x27};

static int send_msg_to_kernel(struct nl_sock *sock){
	struct nl_msg* msg;
	int family_id, err = 0;

	family_id = genl_ctrl_resolve(sock, GENZ_FAMILY_NAME);
	if(family_id < 0){
		fprintf(stderr, "Unable to resolve family name to send a message!\n");
		exit(EXIT_FAILURE);
	}

	msg = nlmsg_alloc();
	if (!msg) {
		fprintf(stderr, "failed to allocate netlink message\n");
		exit(EXIT_FAILURE);
	}

	if(!genlmsg_put(msg, NL_AUTO_PID, NL_AUTO_SEQ, family_id, 0,
		NLM_F_REQUEST, GENZ_C_ADD_COMPONENT, 0)) {
		fprintf(stderr, "failed to put nl hdr!\n");
		err = -ENOMEM;
		goto out;
	}

	err = nla_put_u32(msg, GENZ_A_GCID, gcid);
	if (err) {
		fprintf(stderr, "failed to put gcid!\n");
		goto out;
	}

	err = nla_put_u16(msg, GENZ_A_CCLASS, cclass);
	if (err) {
		fprintf(stderr, "failed to put cclass!\n");
		goto out;
	}

	err = nla_put(msg, GENZ_A_UUID, UUID_LEN, uuid);
	if (err) {
		fprintf(stderr, "failed to put uuid!\n");
		goto out;
	}

	err = nl_send_auto(sock, msg);
	if (err < 0) {
		fprintf(stderr, "failed to send nl message!\n");
	}

out:
	nlmsg_free(msg);
	return err;
}

static void prep_nl_sock(struct nl_sock** nlsock){
	int family_id, grp_id;
	unsigned int bit = 0;

	*nlsock = nl_socket_alloc();
	if(!*nlsock) {
		fprintf(stderr, "Unable to alloc nl socket!\n");
		exit(EXIT_FAILURE);
	}

	/* disable seq checks on multicast sockets */
	nl_socket_disable_seq_check(*nlsock);
	nl_socket_disable_auto_ack(*nlsock);

	/* connect to genl */
	if (genl_connect(*nlsock)) {
		fprintf(stderr, "Unable to connect to genl!\n");
		goto exit_err;
	}

	/* resolve the generic nl family id*/
	family_id = genl_ctrl_resolve(*nlsock, GENZ_FAMILY_NAME);
	if(family_id < 0){
		fprintf(stderr, "Unable to resolve family name to open a socket!\n");
		goto exit_err;
	}

	return;

exit_err:
	nl_socket_free(*nlsock); // this call closes the socket as well
	exit(EXIT_FAILURE);
}

int main(int argc, char** argv){
	struct nl_sock* nlsock = NULL;
	struct nl_cb *cb = NULL;
	int ret;

	prep_nl_sock(&nlsock);

	ret = send_msg_to_kernel(nlsock);

	nl_socket_free(nlsock);
	return 0;
}
