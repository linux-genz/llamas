PKG_CONFIG=$(shell dirname ${CROSS_COMPILE})/pkg-config
NL_LIBNAME=libnl-genl-3.0

NL_LIB_FLAGS=$(shell $(PKG_CONFIG) --cflags $(NL_LIBNAME))
NL_LIBS_L=$(shell $(PKG_CONFIG) --libs-only-L $(NL_LIBNAME))
NL_LIBS_l=$(shell $(PKG_CONFIG) --libs-only-l $(NL_LIBNAME))

KDIR := /lib/modules/$(shell uname -r)/build

obj-m += kern_recv.o

all:
	$(MAKE) -C $(KDIR) SUBDIRS=$(PWD) modules
	gcc -I /usr/include/libnl3 user_send.c -o user_send -lnl-3 -lnl-genl-3

clean:
	rm -rf *.o *.ko *.mod.* *.cmd .module* modules* Module* .*.cmd .tmp*
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean
	rm user_send
