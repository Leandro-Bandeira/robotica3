#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from nav_msgs.msg import Odometry
from cv_bridge import CvBridge
import cv2
import numpy as np
from rclpy.qos import qos_profile_sensor_data


class DetectorCoresNode(Node):

    def __init__(self):
        super().__init__('detector_cores')

        self.bridge = CvBridge()

        # Publishers
        self.pub_cor = self.create_publisher(String, '/cor_atual', 10)
        self.pub_contagem = self.create_publisher(String, '/contagem_cores', 10)

        # Subscriber da câmera
        self.sub_camera = self.create_subscription(
            Image,
            '/frente_camera/frente_camera_sensor/image_raw',
            self.image_callback,
            qos_profile_sensor_data
        )

        # Subscriber da odometria
        self.sub_odom = self.create_subscription(
            Odometry,
            '/odometry/filtered',
            self.odom_callback,
            10
        )

        # posição atual do robô
        self.robot_pos = None

        # contagem
        self.contagem = {
            'vermelho': 0,
            'verde': 0,
            'azul': 0
        }

        # lista de posições detectadas
        self.objetos_detectados = {
            'vermelho': [],
            'verde': [],
            'azul': []
        }

        # distância mínima para considerar novo objeto
        self.map_threshold = 1.5


    def odom_callback(self, msg):

        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y

        self.robot_pos = (x, y)


    def distancia(self, p1, p2):

        return np.sqrt(
            (p1[0] - p2[0])**2 +
            (p1[1] - p2[1])**2
        )


    def ja_detectado(self, cor):

        for pos in self.objetos_detectados[cor]:

            dist = self.distancia(self.robot_pos, pos)

            if dist < self.map_threshold:
                return True

        return False


    def image_callback(self, msg):

        if self.robot_pos is None:
            return

        cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")

        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)

        # máscaras de cor
        mask_red1 = cv2.inRange(hsv, np.array([0,120,70]), np.array([10,255,255]))
        mask_red2 = cv2.inRange(hsv, np.array([170,120,70]), np.array([180,255,255]))
        mask_red = mask_red1 + mask_red2

        mask_green = cv2.inRange(hsv, np.array([36,50,50]), np.array([89,255,255]))
        mask_blue = cv2.inRange(hsv, np.array([90,50,50]), np.array([128,255,255]))

        area_red = cv2.countNonZero(mask_red)
        area_green = cv2.countNonZero(mask_green)
        area_blue = cv2.countNonZero(mask_blue)

        limite_area = 500

        cor_atual = 'nenhuma'

        if area_red > limite_area and area_red > area_green and area_red > area_blue:
            cor_atual = 'vermelho'

        elif area_green > limite_area and area_green > area_red and area_green > area_blue:
            cor_atual = 'verde'

        elif area_blue > limite_area and area_blue > area_red and area_blue > area_green:
            cor_atual = 'azul'


        # -------- CONTAGEM --------

        if cor_atual != 'nenhuma':

            if not self.ja_detectado(cor_atual):

                self.contagem[cor_atual] += 1

                self.objetos_detectados[cor_atual].append(self.robot_pos)

                self.get_logger().info(
                    f'Novo objeto {cor_atual.upper()} detectado '
                    f'na posição x={self.robot_pos[0]:.2f}, y={self.robot_pos[1]:.2f}'
                )


        # -------- PUBLICAÇÃO --------

        msg_cor = String()
        msg_cor.data = cor_atual
        self.pub_cor.publish(msg_cor)

        msg_contagem = String()
        msg_contagem.data = (
            f"Verde: {self.contagem['verde']} | "
            f"Vermelho: {self.contagem['vermelho']} | "
            f"Azul: {self.contagem['azul']}"
        )

        self.pub_contagem.publish(msg_contagem)


def main(args=None):

    rclpy.init(args=args)

    node = DetectorCoresNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
