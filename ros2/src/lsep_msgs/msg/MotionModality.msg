# LSEP motion modality — kinematic expression of intent.

string action           # none | maintain | announce_path | decelerate |
                        # evasive | emergency_stop | cautious | creep | stationary
float32 speed_modifier  # 0.0 .. 1.0 (multiplier on nominal speed)
string trajectory       # free | planned | yield_path | evasive | halt |
                        # conservative | self_test
