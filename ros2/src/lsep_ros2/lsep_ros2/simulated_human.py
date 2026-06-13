"""Simulated human for the LSEP demo.

Publishes a human that approaches the robot, lingers dangerously close,
then retreats — cycling forever. Drives the full state ladder:

  IDLE -> AWARENESS -> INTENT -> CARE -> CRITICAL -> THREAT
       -> (dwell-based de-escalation) -> AWARENESS -> IDLE

Topics (std_msgs/Float32):
  lsep/input/distance_m
  lsep/input/closing_velocity_ms   (> 0 approaching, <= 0 retreating)
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32


class SimulatedHuman(Node):

    APPROACH_SPEED = 1.2   # m/s
    RETREAT_SPEED = 0.8    # m/s
    MAX_DISTANCE = 12.0    # m
    MIN_DISTANCE = 0.4     # m
    LINGER_S = 3.0         # s standing close to the robot
    RATE_HZ = 20.0

    def __init__(self):
        super().__init__('simulated_human')
        self._pub_d = self.create_publisher(Float32, 'lsep/input/distance_m', 10)
        self._pub_v = self.create_publisher(Float32, 'lsep/input/closing_velocity_ms', 10)
        self._distance = self.MAX_DISTANCE
        self._phase = 'approach'
        self._linger_left = 0.0
        self._dt = 1.0 / self.RATE_HZ
        self.create_timer(self._dt, self._step)
        self.get_logger().info('Simulated human walking towards the robot…')

    def _step(self):
        if self._phase == 'approach':
            velocity = self.APPROACH_SPEED
            self._distance -= velocity * self._dt
            if self._distance <= self.MIN_DISTANCE:
                self._distance = self.MIN_DISTANCE
                self._phase = 'linger'
                self._linger_left = self.LINGER_S
        elif self._phase == 'linger':
            velocity = 0.0
            self._linger_left -= self._dt
            if self._linger_left <= 0.0:
                self._phase = 'retreat'
        else:  # retreat
            velocity = -self.RETREAT_SPEED
            self._distance += self.RETREAT_SPEED * self._dt
            if self._distance >= self.MAX_DISTANCE:
                self._distance = self.MAX_DISTANCE
                self._phase = 'approach'

        d, v = Float32(), Float32()
        d.data = float(self._distance)
        v.data = float(velocity)
        self._pub_d.publish(d)
        self._pub_v.publish(v)


def main(args=None):
    rclpy.init(args=args)
    node = SimulatedHuman()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
