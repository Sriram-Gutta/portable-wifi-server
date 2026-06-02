#ifndef __LWIPOPTS_H__
#define __LWIPOPTS_H__

/* Minimal lwip options for Pico W webserver */
#define NO_SYS                          1
#define MEM_ALIGNMENT                   4
#define LWIP_RAW                        0
#define LWIP_NETCONN                    0
#define LWIP_SOCKET                     0
#define LWIP_DHCP                       0
#define LWIP_ICMP                       1
#define LWIP_UDP                        1
#define LWIP_TCP                        1
#define LWIP_IPV4                       1
#define LWIP_IPV6                       0
#define ETH_PAD_SIZE                    0

#define TCP_MSS                         (1500 - 20 - 20)
#define TCP_SND_BUF                     (4 * TCP_MSS)
#define TCP_WND                         (4 * TCP_MSS)

#define PBUF_POOL_SIZE                  4

#endif /* __LWIPOPTS_H__ */
