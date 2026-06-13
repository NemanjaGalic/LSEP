# LSEP light modality — semantics, not aesthetics.
# The protocol defines pattern/frequency/intensity; the rendering
# (LED layout, exact hue) remains manufacturer-flexible.

string pattern          # breathe | pulse | wave | strobe | slow_blink | sweep | none
float32 frequency_hz
float32 intensity       # 0.0 .. 1.0
float32[4] bezier       # transition easing curve (cubic-bezier)
