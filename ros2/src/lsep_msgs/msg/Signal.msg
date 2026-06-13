# LSEP v2.1-draft — full protocol signal (typed transport).
# Replaces the JSON-in-String transport of lsep_ros2 v0.1.

std_msgs/Header header

string protocol                 # "LSEP"
string version                  # "2.1-draft"

# ---- state enum -------------------------------------------------------
uint8 STATE_IDLE=0
uint8 STATE_AWARENESS=1
uint8 STATE_INTENT=2
uint8 STATE_CARE=3
uint8 STATE_CRITICAL=4
uint8 STATE_THREAT=5
uint8 STATE_MED_CONF=6
uint8 STATE_LOW_CONF=7
uint8 STATE_INTEGRITY=8

uint8 state                     # reported state (watchdog + confidence overlay)
string state_name               # human-readable mirror of `state`
uint8 core_state                # core kinematic state (forensics)
string core_state_name

# ---- physics ----------------------------------------------------------
float32 ttc_seconds             # NaN if undefined (no closing motion)
float32 distance_m              # NaN if unknown
float32 closing_velocity_ms     # > 0 approaching; NaN if unknown

# ---- trimodal expression ----------------------------------------------
LightModality light
SoundModality sound
MotionModality motion

# ---- trust metadata ----------------------------------------------------
float32 confidence              # sensor fusion confidence 0.0 .. 1.0
string[] sensor_fusion          # e.g. ["lidar", "camera", "ultrasonic"]
bool stale_input                # true => input watchdog tripped
