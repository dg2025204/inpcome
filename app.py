from machine import Pin, ADC
import neopixel
import utime
import random

TIMING = (280, 515, 515, 745)
NUM_LEDS = 10
LED_PIN = 16
MQ2_PIN = 26

np = neopixel.NeoPixel(Pin(LED_PIN), NUM_LEDS, timing=TIMING)
mq2 = ADC(Pin(MQ2_PIN))

BRIGHTNESS = 0.15

SAFE_MIN = 1000
DANGER_LEVEL = 3000
CRITICAL_LEVEL = 4000

current_state = "SAFE"

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def scale(color):
    return tuple(int(c * BRIGHTNESS) for c in color)

def color_gradient(ratio):
    ratio = clamp(ratio, 0.0, 1.0)
    r = int(255 * ratio)
    g = int(255 * (1 - ratio))
    return (r, g, 0)

def show_gauge(value):
    ratio = clamp((value - SAFE_MIN) / (DANGER_LEVEL - SAFE_MIN), 0.0, 1.0)
    lit_count = int(ratio * NUM_LEDS)
    color = color_gradient(ratio)

    for i in range(NUM_LEDS):
        if i < lit_count:
            np[i] = scale(color)
        elif i == lit_count:
            partial = ratio * NUM_LEDS - lit_count
            dim = tuple(int(c * partial) for c in color)
            np[i] = scale(dim)
        else:
            np[i] = (0, 0, 0)
    np.write()

def danger_full_red_pulse():
    brightness_wave = int(128 + 127 * abs(utime.ticks_ms() % 1000 - 500) / 500)
    np.fill(scale((brightness_wave, 0, 0)))
    np.write()

def explosion_effect():
    print("🔥 CRITICAL! 폭발 연출 시작 🔥")

    for _ in range(2):
        np.fill(scale((255, 255, 255)))
        np.write()
        utime.sleep(0.05)
        np.fill((0, 0, 0))
        np.write()
        utime.sleep(0.05)

    for _ in range(15):
        np.fill((0, 0, 0))
        spark_idx = random.randint(0, NUM_LEDS - 1)
        np[spark_idx] = scale((255, random.randint(100, 200), 0))
        np.write()
        utime.sleep(0.03)
        value = mq2.read_u16()
        print("MQ2 raw:", value, "(explosion 중)")

    for _ in range(4):
        np.fill(scale((255, 0, 0)))
        np.write()
        utime.sleep(0.1)
        np.fill(scale((30, 0, 0)))
        np.write()
        utime.sleep(0.1)
        value = mq2.read_u16()
        print("MQ2 raw:", value, "(explosion 중)")

print("MQ2 예열 중...")
utime.sleep(5)

while True:
    value = mq2.read_u16()
    print("MQ2 raw:", value, "| state:", current_state)

    if value >= CRITICAL_LEVEL:
        current_state = "CRITICAL"
    elif value >= DANGER_LEVEL:
        current_state = "DANGER"
    else:
        current_state = "SAFE"

    if current_state == "CRITICAL":
        explosion_effect()
    elif current_state == "DANGER":
        danger_full_red_pulse()
        utime.sleep(0.05)
    else:
        show_gauge(value)
        utime.sleep(0.1)
