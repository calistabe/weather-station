def set_black_pixel(data, x_coord, y_coord, new_val):
    # TODO error handling
    byte_index = y_coord * 200 // 4 + x_coord // 4
    orig_byte = data[byte_index]
    print_byte(orig_byte)
    shift = ((3 - x_coord % 4) * 2)
    print(shift)
    bit_mask = (0b11 << shift) ^ 0b11111111
    print_byte(bit_mask)
    orig_byte &= bit_mask
    print_byte(orig_byte)
    orig_byte |= new_val << shift
    print_byte(orig_byte)
    data[byte_index] = orig_byte

def print_byte(x):
    print("{0:08b}".format(x))

#data = [0b11111111 for _ in range(200 * 200 // 4)]

#set_black_pixel(data, 0, 0, 0b00)
#print("{0:b}".format(data[0]))

def convert_byte_to_twos_complement(byte):
    leftmost_bit = (1 << 15) & byte
    if not leftmost_bit:
        return int(byte)
    
    flipped_sign = byte & 0b0111111111111111
    return int(flipped_sign) - (1 << 15)

for x in range(-(2 ** 15), 2 ** 15):
    if x != convert_byte_to_twos_complement(x):
        print(f"Problem with {x}")