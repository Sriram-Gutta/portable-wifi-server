import machine

sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / 65535

def read_temperature():
    
    # Reads the internal RP2350 temperature sensor and calculates temperature based on voltage drop. 
    
    reading = sensor_temp.read_u16() * conversion_factor
    # Standard formula for Raspberry Pi silicon internal sensors
    temperature = 27 - (reading - 0.706) / 0.001721
    return temperature