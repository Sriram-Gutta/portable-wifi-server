#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"
#include "hardware/adc.h"
#include "lwip/tcp.h"
#include "lwip/pbuf.h"

// Access point settings
#define WIFI_SSID "PicoW_Server"
#define WIFI_PASSWORD "12345678"
#define HTTP_PORT 80

// HTML Template
const char *HTML_TEMPLATE = 
"<!DOCTYPE html>\n"
"<html>\n"
"<head><title>Pico W Server</title></head>\n"
"<body>\n"
"<h1>Pico W Portable Server</h1>\n"
"\n"
"<form action=\"/lighton\"><input type=\"submit\" value=\"Light ON\"></form>\n"
"<form action=\"/lightoff\"><input type=\"submit\" value=\"Light OFF\"></form>\n"
"<form action=\"/close\"><input type=\"submit\" value=\"Stop Server\"></form>\n"
"\n"
"<h3>Media Slots</h3>\n"
"<form action=\"/mp4_1\"><input type=\"submit\" value=\"Slot 1 (MP4)\"></form>\n"
"<form action=\"/mp4_2\"><input type=\"submit\" value=\"Slot 2 (MP4)\"></form>\n"
"<form action=\"/mp4_3\"><input type=\"submit\" value=\"Slot 3 (MP4)\"></form>\n"
"<form action=\"/mp4_4\"><input type=\"submit\" value=\"Slot 4 (MP4)\"></form>\n"
"\n"
"<h3>PDF Slots</h3>\n"
"<form action=\"/pdf/test.pdf\"><input type=\"submit\" value=\"Open Test PDF\"></form>\n"
"<form action=\"/pdf_1\"><input type=\"submit\" value=\"Slot 5 (PDF)\"></form>\n"
"<form action=\"/pdf_2\"><input type=\"submit\" value=\"Slot 6 (PDF)\"></form>\n"
"<form action=\"/pdf_3\"><input type=\"submit\" value=\"Slot 7 (PDF)\"></form>\n"
"\n"
"<p>LED State: %s</p>\n"
"<p>Temperature: %.2f C</p>\n"
"</body>\n"
"</html>\n";

// Global state
static bool led_state = false;
static bool server_running = true;

// Function to read temperature from internal sensor
float read_temperature() {
    adc_init();
    adc_set_temp_sensor_enabled(true);
    adc_select_input(4);
    
    uint16_t raw = adc_read();
    float conversion_factor = 3.3f / (1 << 12);
    float voltage = raw * conversion_factor;
    
    // Temperature calculation based on the datasheet formula
    return 27.0f - (voltage - 0.706f) / 0.001721f;
}

// Forward declaration for HTTP request handler (used in tcp_server_recv)
void handle_http_request(struct tcp_pcb *pcb, char *request, size_t len);

// TCP receive callback
static err_t tcp_server_recv(void *arg, struct tcp_pcb *pcb, struct pbuf *p, err_t err) {
    char *http_request = (char *)arg;

    if (!p) {
        if (http_request) {
            free(http_request);
        }
        return tcp_close(pcb);
    }

    if (p->tot_len > 0) {
        // Copy the request data
        pbuf_copy_partial(p, http_request, p->tot_len > 1023 ? 1023 : p->tot_len, 0);
        handle_http_request(pcb, http_request, strlen(http_request));
    }

    pbuf_free(p);
    return ERR_OK;
}

// Function to handle HTTP request
void handle_http_request(struct tcp_pcb *pcb, char *request, size_t len) {
    char *path = request;
    // Skip HTTP method
    while (*path && *path != ' ') path++;
    if (*path) path++;
    
    char *path_end = path;
    while (*path_end && *path_end != ' ' && *path_end != '?') path_end++;
    *path_end = '\0';

    printf("Request path: %s\n", path);

    if (strcmp(path, "/lighton") == 0) {
        led_state = true;
        cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 1);
    } else if (strcmp(path, "/lightoff") == 0) {
        led_state = false;
        cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 0);
    } else if (strcmp(path, "/close") == 0) {
        server_running = false;
        const char *response = "HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n"
                             "<html><body><h1>Server is shutting down...</h1></body></html>";
        tcp_write(pcb, response, strlen(response), TCP_WRITE_FLAG_COPY);
        return;
    }

    // Read current temperature
    float temperature = read_temperature();
    
    // Prepare HTTP response
    char response[4096];
    char html[3072];
    snprintf(html, sizeof(html), HTML_TEMPLATE, 
             led_state ? "ON" : "OFF", temperature);
    
    snprintf(response, sizeof(response),
             "HTTP/1.0 200 OK\r\n"
             "Content-Type: text/html\r\n"
             "Content-Length: %d\r\n"
             "\r\n"
             "%s", strlen(html), html);
             
    tcp_write(pcb, response, strlen(response), TCP_WRITE_FLAG_COPY);
}

// TCP error callback
static void tcp_server_err(void *arg, err_t err) {
    char *http_request = (char *)arg;
    if (http_request) {
        free(http_request);
    }
}

// TCP server callbacks
static err_t tcp_server_accept(void *arg, struct tcp_pcb *pcb, err_t err) {
    if (err != ERR_OK || pcb == NULL) {
        return ERR_VAL;
    }

    // Allocate receive buffer
    char *http_request = calloc(1024, sizeof(char));
    if (!http_request) {
        return ERR_MEM;
    }

    tcp_arg(pcb, http_request);
    tcp_recv(pcb, tcp_server_recv);
    tcp_err(pcb, tcp_server_err);
    
    return ERR_OK;
}

// Main function
int main() {
    stdio_init_all();
    
    // Initialize WiFi chip
    if (cyw43_arch_init() != 0) {
        printf("Failed to initialize WiFi\n");
        return 1;
    }
    
    // Start access point
    cyw43_arch_enable_ap_mode(WIFI_SSID, WIFI_PASSWORD, CYW43_AUTH_WPA2_AES_PSK);
    printf("WiFi AP started: %s\n", WIFI_SSID);
    
    // Initialize TCP server
    struct tcp_pcb *pcb = tcp_new();
    if (!pcb) {
        printf("Failed to create TCP PCB\n");
        return 1;
    }
    
    err_t err = tcp_bind(pcb, IP_ADDR_ANY, HTTP_PORT);
    if (err != ERR_OK) {
        printf("Failed to bind TCP PCB\n");
        return 1;
    }
    
    pcb = tcp_listen(pcb);
    tcp_accept(pcb, tcp_server_accept);
    
    printf("HTTP server started on port %d\n", HTTP_PORT);
    
    // Main loop
    while (server_running) {
        cyw43_arch_poll();
        sleep_ms(1);
    }
    
    // Cleanup
    cyw43_arch_deinit();
    return 0;
}
