import machine

# the internal temperature sensor lives on ADC channel 4
sensor = machine.ADC(4)


def read_temperature():
    # convert the 16-bit reading to a voltage between 0 and 3.3V
    raw = sensor.read_u16()
    volts = raw * 3.3 / 65535
    # formula from the datasheet
    return 27 - (volts - 0.706) / 0.001721
