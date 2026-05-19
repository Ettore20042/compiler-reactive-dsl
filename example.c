#include <stdio.h>
#include <stdbool.h>

int calculateSpeed(int base, int bonus) {
        printf("%s\n", "Calcolo in corso...");
        return (base + bonus);
}

int main() {
    int speed = 0;
    int max_speed = 100;
    bool running = true;
    if ((speed < max_speed)) {
        speed = calculateSpeed(speed, 10);
        printf("%d\n", speed);
    }
    while ((running == true)) {
        running = false;
        printf("%s\n", "Sistema fermato!");
    }
    return 0;
}
