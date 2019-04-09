#include "genz_gnl.h"
#include <ctype.h>
#include <errno.h>
#include <getopt.h>
#include <linux/netlink.h>
#include <malloc.h>
#include <netlink/attr.h>
#include <netlink/genl/ctrl.h>
#include <netlink/genl/genl.h>
#include <netlink/msg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>

// static char *message = "add@media,gcid=23,serial_number=sssjjkkh90,c-uuid=abdc-dkkl-sdkla-ppsk";
// static uint32_t gcid = 58;
// static uint16_t cclass = 13;
static uint8_t uuid[16] = {0x48, 0x13, 0xea, 0x5f, 0x07, 0x4e, 0x4b, 0xe2, 0xa3, 0x55, 0xa3, 0x54, 0x14, 0x5c, 0x99, 0x27};


static int send_msg_to_kernel(struct nl_sock *sock, struct MsgProps *props){
    struct nl_msg* msg;
    int family_id, err = 0;
    int gcid = atoi(props->gcid);
    int cclass = atoi(props->cclass);
    // int uuid = atoi(props->uuid);

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
}//send_msg_to_kernel


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
}//prep_nl_sock


/*
 * Parse command-line arguments and return a MsgProps struct to be used for messaging.
 */
struct MsgProps* parseArgs(int argc, char *argv[]) {
    struct MsgProps* props;
    props = malloc( sizeof *props ); //malloc or segfault

    while (1) {
        static struct option long_options[] = {
            {"cclass",  required_argument, 0, 'c'},
            {"uuid",  required_argument, 0, 'u'},
            {"gcid",  required_argument, 0, 'g'},
            {0, 0, 0, 0}
        };
        // /* getopt_long stores the option index here. */
        int option_index = 0;

        char c = getopt_long (argc, argv, "c:u:g:",
                    long_options, &option_index);

        // /* Detect the end of the options. */
        if (c == -1) break;

        switch (c){
            case 0:
            /* If this option set a flag, do nothing else now. */
                if (long_options[option_index].flag != 0)
                    break;
                printf ("option %s", long_options[option_index].name);
                if (optarg)
                    printf (" with arg %s", optarg);
                printf ("\n");
                break;

            case 'u':
                props->uuid = optarg;
                break;

            case 'c':
                props->cclass = optarg;
                break;

            case 'g':
                props->gcid = optarg;
                break;

            case '?':
                /* getopt_long already printed an error message. */
                break;

            default:
                abort ();
        }//switch
    }//while

    return props;
}//parseArgs



int main(int argc, char *argv[]){
    printf("--- USER_SEND MAIN ---\n");
    struct nl_sock* nlsock = NULL;
    struct nl_cb *cb = NULL;
    int ret;
    struct MsgProps* props = parseArgs(argc, argv);
    if (props->gcid == NULL)
        props->gcid = "-1";
    if (props->cclass == NULL)
        props->cclass = "-1";

    printf("--- UserSend called with gcid=%s; cclass=%s ---\n", props->gcid, props->cclass);
    prep_nl_sock(&nlsock);
    ret = send_msg_to_kernel(nlsock, props);
    nl_socket_free(nlsock);

    return 6666;
}//main
