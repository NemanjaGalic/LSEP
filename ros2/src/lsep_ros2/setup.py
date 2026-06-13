from setuptools import find_packages, setup

package_name = 'lsep_ros2'

setup(
    name=package_name,
    version='0.2.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/lsep_demo.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Nemanja Galic',
    maintainer_email='info@experiencedesigninstitute.ch',
    description='LSEP reference implementation for ROS 2 (lifecycle node).',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'lsep_node = lsep_ros2.lsep_lifecycle_node:main',
            'simulated_human = lsep_ros2.simulated_human:main',
        ],
    },
)
