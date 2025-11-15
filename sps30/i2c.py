import io
from fcntl import ioctl
import errno, time

I2C_SLAVE = 0x0703


class I2C:

    def __init__(self, bus: int, address: int):

        self.fr = io.open("/dev/i2c-"+str(bus), "rb", buffering=0)
        self.fw = io.open("/dev/i2c-"+str(bus), "wb", buffering=0)

        # set device address
        ioctl(self.fr, I2C_SLAVE, address)
        ioctl(self.fw, I2C_SLAVE, address)

    def write(self, data: list):
        self.fw.write(bytearray(data))

    def _retry(self, fn, *args, retries=3, delay=0.05):
        for i in range(retries):
            try: return fn(*args)
            except OSError as e:
                if e.errno != errno.EIO or i == retries-1: raise
                time.sleep(delay*(i+1))  # brief backoff

    def read(self, nbytes: int) -> list[int]:
        return list(self._retry(self.fr.read, nbytes))

    def close(self):
        self.fw.close()
        self.fr.close()
