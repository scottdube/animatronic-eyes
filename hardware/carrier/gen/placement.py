"""Footprint placement, KiCad board frame (mm, y down, board origin = DXF origin).
Written by capture_placement.py from Scott's GUI placement; H1-H4 come from
gen_pcb.HOLES (the DXF) and are not captured.
ref: (footprint, value, x, y, rot)
"""
PLACE = {
    "U1": ("D1_Mini_ESP32_THT", "D1 Mini ESP32 (Type-C)", -37.5, -6.5, 270),
    "U2": ("PCA9685_Adafruit_Module", "PCA9685 16ch servo", 0.016, 24.795, 0),
    "U3": ("LM2596_Module", "LM2596 buck 12V->5.05V", 43.3, 8.4, 180),
    "J1": ("KF301_1x02_P5.08", "12V pigtail", 41.5, 16.5, 0),
    "C1": ("CP_Radial_D6.3_P2.5", "220u", -42.5, 18.0, 0),
    "C2": ("C_Disc_P5.08", "100n", -51.5, 13.0, 0),
    "TP1": ("TestPoint_THT_D2.2_1.181", "+12V", 52.0, 13.0, 0),
    "TP2": ("TestPoint_THT_D2.2_1.181", "+5V", -35.0, 17.0, 0),
    "TP3": ("TestPoint_THT_D2.2_1.181", "+3V3", -40.0, -27.0, 0),
    "TP5": ("TestPoint_THT_D2.2_1.181", "GND", 52.0, 19.0, 0),
    "TP6": ("TestPoint_THT_D2.2_1.181", "GND", -54.5, -25.0, 0),
}
