import serial
import struct
import threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

HEADER = b'\xF4\xF3\xF2\xF1'
TAIL = b'\xF8\xF7\xF6\xF5'
FRAME_SIZE = 45

distance_values = deque(maxlen=100)  # smooth scrolling window

def parse_frame(frame_bytes):
    data_len = struct.unpack('<H', frame_bytes[4:6])[0]
    flag = frame_bytes[6]
    distance = struct.unpack('<H', frame_bytes[7:9])[0]
    #print(frame_bytes[7], frame_bytes[8])
    #print(">>>", int(frame_bytes[7]) + int(frame_bytes[8])*256)
    values = [struct.unpack('<H', frame_bytes[9 + 2*i:11 + 2*i])[0] for i in range(16)]

    return {
        "header": list(frame_bytes[0:4]),
        "data_length": data_len,
        "flag": flag,
        "distance_raw": distance,
        "values": values,
        "tail": list(frame_bytes[-4:])
    }


def serial_reader(port_name="COM3"):
    ser = serial.Serial(port_name, 115200, timeout=0.1)
    buffer = bytearray()
    while True:
        buffer += ser.read(ser.in_waiting or 1)
        while True:
            start = buffer.find(HEADER)
            end = buffer.find(TAIL, start + 4)
            if start != -1 and end != -1 and (end + 4 - start) == FRAME_SIZE:
                frame = buffer[start:end + 4]
                try:
                    distance = parse_frame(frame)
                    print(distance["distance_raw"]/100)
                    distance_values.append(distance["distance_raw"]/100)
                except Exception as e:
                    print(f"Parse error: {e}")
                buffer = buffer[end + 4:]
            else:
                break

def animate(i, line):
    line.set_ydata(distance_values)
    line.set_xdata(range(len(distance_values)))
    return line,

def start_plot():
    plt.style.use('ggplot')
    fig, ax = plt.subplots()
    line, = ax.plot([], [], lw=2)
    ax.set_ylim(0, 10)  # up to 10 meters
    ax.set_xlim(0, 100)
    ax.set_title("Distance from Radar")
    ax.set_ylabel("Distance (meters)")
    ax.set_xlabel("Time steps")
    ani = animation.FuncAnimation(fig, animate, fargs=(line,), interval=100)
    plt.show()


if __name__ == "__main__":
    threading.Thread(target=serial_reader, args=("COM3",), daemon=True).start()
    start_plot()
