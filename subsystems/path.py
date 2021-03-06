from tools import Timer
from math import degrees, radians, pi
from traits import DriveTrain, Gyro
from wpilib.controller import RamseteController
from wpilib.kinematics import DifferentialDriveOdometry, DifferentialDriveKinematics
from wpilib.geometry import Rotation2d, Pose2d


class Path:
    def __init__(self, kS, kV, trackwidth, trajectory):
        '''
        Creates a controller for following a PathWeaver trajectory.

        __init__(self, kS: Volts, kV: Volts * Seconds / Meters, trackwidth: Meters, trajectory: wpilib.trajectory.Trajectory)

        :param kS: The kS gain determined by characterizing the Robot's drivetrain
        :param kV: The kV gain determined by characterizing the Robot's drivetrain
        :param trackwidth: The horizontal distance between the left and right wheels of the tank drive.
        :param trajectory: The trajectory to follow. This can be generated by PathWeaver, or made by hand.
        '''

        self.kS = kS
        self.kV = kV

        self.trajectory = trajectory

        self.odometry = DifferentialDriveOdometry(
            Rotation2d(radians(0)), self.trajectory.initialPose())

        self.ramsete = RamseteController(2, 0.7)
        self.drive_kinematics = DifferentialDriveKinematics(trackwidth)

        self.are_wheel_speeds_zero = False
        self.timer = Timer()

    def is_done(self):
        '''
        is_done(self) -> bool

        Returns whether or not the path is done.
        '''
        return self.are_wheel_speeds_zero

    def reset(self, chassis, gyro):
        '''
        Re-initializes all of the data in the controller as if the path has not yet been executed.
        This method MUST be called in teleopInit and autonomousInit directly before the controller is used.

        reset(self, chassis: traits.DriveTrain, gyro: traits.Gyro)

        :param chassis: An object that implements the DriveTrain trait. This object's encoders will be reset by this function
        :param gyro: An object that implements the Gyro trait. This object's angle will be reset by this function
        '''

        # Assert the objects implement the proper traits
        assert chassis.implements(DriveTrain)
        assert gyro.implements(Gyro)

        # The encoders and gyro need to be reset so that the Ramsete
        # controller is fed data that looks new.
        # By reseting these sensors, we look like weve never run the path at all!
        chassis.reset_encoders()
        gyro.reset()
        self.are_wheel_speeds_zero = False

        # The odometry object also needs to be re-initialized
        # so that it forgets the state from the previous run
        self.odometry = DifferentialDriveOdometry(
            Rotation2d(radians(0)), self.trajectory.initialPose())

        self.timer.start()

    def follow(self, chassis, gyro):
        '''
        This updates the Path and drives the chassis to follow the path

        update(self, chassis: traits.DriveTrain, gyro: traits.Gyro)

        :param chassis: An object that implements the DriveTrain trait. When this function is called,
                        the object's motors will be driven to follow the last set trajectory.
        :param gyro: An object that implements the gyro trait.
        '''
        # Assert the objects implement the proper traits
        assert chassis.implements(DriveTrain)
        assert gyro.implements(Gyro)

        if self.is_done():
            return

        # Set the chassis to low gear for more precise movements
        chassis.set_low_gear()

        # If a trajectory has been set, run it
        if self.trajectory is not None:
            # Get the accumulated left and right distance of the chass
            ld, rd = chassis.get_left_distance(), chassis.get_right_distance()

            # Ramsete requires the counterclockwise angle of the Robot
            angle = gyro.get_counterclockwise_degrees()

            # Get the current position of the robot
            current_pose = self.odometry.update(
                Rotation2d(radians(angle)),
                ld, rd
            )

            # Calculate the target position using the trajectory, and get the chassis wheel speeds
            target_pose = self.trajectory.sample(self.timer.get())
            chassis_speed = self.ramsete.calculate(current_pose, target_pose)
            wheel_speeds = self.drive_kinematics.toWheelSpeeds(chassis_speed)
            l, r = wheel_speeds.left, wheel_speeds.right

            if abs(l) == 0 and abs(r) == 0:
                self.are_wheel_speeds_zero = True

            # Convert the left and right wheel speeds to volts using the characterized constants,
            # and then convert those to percent values from -1 to 1
            chassis.tank_drive((self.kS + l*self.kV)/12,
                               (self.kS + r*self.kV)/12)
