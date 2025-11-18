# sh1106.py — MicroPython SH1106 I2C driver (chunked writes, 128x64 or 128x32)
from micropython import const
import framebuf

# Commands (SH1106)
SET_CONTRAST        = const(0x81)
SET_NORM_INV        = const(0xA6)
SET_DISP_ON         = const(0xAF)
SET_DISP_OFF        = const(0xAE)
SET_ENTIRE_ON_FOL   = const(0xA4)  # display follows RAM
SET_MEM_MODE        = const(0x20)  # (not used by SH1106; page addr mode fixed)
SET_DISP_START_LINE = const(0x40)
SET_SEG_REMAP_0     = const(0xA0)
SET_SEG_REMAP_1     = const(0xA1)
SET_MUX_RATIO       = const(0xA8)
SET_COM_OUT_DIR_NOR = const(0xC0)
SET_COM_OUT_DIR_REM = const(0xC8)
SET_DISP_OFFSET     = const(0xD3)
SET_COM_PIN_CFG     = const(0xDA)
SET_DISP_CLK_DIV    = const(0xD5)
SET_PRECHARGE       = const(0xD9)
SET_VCOM_DESEL      = const(0xDB)
SET_CHARGE_PUMP     = const(0x8D)  # often ignored on SH1106 modules

class SH1106:
    def __init__(self, width, height, external_vcc=False, col_offset=2):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        self.col_offset = col_offset  # SH1106 has 132 columns; visible window usually starts at 2
        self.buffer = bytearray(self.pages * self.width)
        self.framebuf = framebuf.FrameBuffer(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    # FrameBuffer passthroughs
    def fill(self, c): self.framebuf.fill(c)
    def pixel(self, x, y, c): self.framebuf.pixel(x, y, c)
    def text(self, s, x, y): self.framebuf.text(s, x, y)
    def hline(self, x, y, w, c): self.framebuf.hline(x, y, w, c)
    def vline(self, x, y, h, c): self.framebuf.vline(x, y, h, c)
    def line(self, x1, y1, x2, y2, c): self.framebuf.line(x1, y1, x2, y2, c)
    def rect(self, x, y, w, h, c): self.framebuf.rect(x, y, w, h, c)
    def blit(self, fb_source, x, y, key, pallet): self.framebuf.blit(fb_source, x, y, key, pallet)
    def fill_rect(self, x, y, w, h, c,): self.framebuf.fill_rect(x, y, w, h, c)
    def ellipse(self, x, y, xr, yr, color): self.framebuf.ellipse(x, y, xr, yr, color)
    def poweroff(self): self.write_cmd(SET_DISP_OFF)
    def poweron(self):  self.write_cmd(SET_DISP_ON)
    def invert(self, inv): self.write_cmd(SET_NORM_INV | (inv & 1))
    def contrast(self, val): self.write_cmd(SET_CONTRAST); self.write_cmd(val & 0xFF)

    def init_display(self):
        for cmd in (
            SET_DISP_OFF,
            SET_DISP_CLK_DIV, 0x80,
            SET_MUX_RATIO, self.height - 1,     # 0x3F for 64, 0x1F for 32
            SET_DISP_OFFSET, 0x00,
            SET_DISP_START_LINE | 0x00,
            SET_SEG_REMAP_1,                    # mirror horizontally to match common wiring
            SET_COM_OUT_DIR_REM,                # scan from COM[N-1] to COM0
            SET_COM_PIN_CFG, 0x12 if self.height == 64 else 0x02,
            SET_CONTRAST, 0x8F,
            SET_PRECHARGE, 0x1F,
            SET_VCOM_DESEL, 0x40,
            SET_ENTIRE_ON_FOL,
            SET_NORM_INV,
            SET_DISP_ON,
        ):
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def show(self):
        # SH1106 uses page addressing; set page and column (with offset) per page.
        for page in range(self.pages):
            self.write_cmd(0xB0 | page)                        # set page addr
            self.write_cmd(0x00 | ((self.col_offset) & 0x0F))  # low column start
            self.write_cmd(0x10 | ((self.col_offset) >> 4))    # high column start
            # write one page (width bytes) in safe chunks
            start = self.width * page
            mv = memoryview(self.buffer)[start:start + self.width]
            for i in range(0, self.width, 16):
                self.write_data(mv[i:i+16])

    # Hooks implemented by subclasses
    def write_cmd(self, cmd): raise NotImplementedError
    def write_data(self, buf): raise NotImplementedError

class SH1106_I2C(SH1106):
    def __init__(self, width, height, i2c, addr=0x3C, external_vcc=False, col_offset=2):
        self.i2c = i2c
        self.addr = addr
        super().__init__(width, height, external_vcc, col_offset)

    def write_cmd(self, cmd):
        try:
            self.i2c.writevto(self.addr, (b'\x80', bytes([cmd])))
        except AttributeError:
            self.i2c.writeto(self.addr, bytes((0x80, cmd)))

    def write_data(self, buf):
        try:
            self.i2c.writevto(self.addr, (b'\x40', buf))
        except AttributeError:
            self.i2c.writeto(self.addr, b'\x40' + bytes(buf))

