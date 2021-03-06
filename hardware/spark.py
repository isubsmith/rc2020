from rev import CANSparkMax, MotorType
from traits import Motor, Encoder, implements


@implements(Encoder, Motor)
class SparkMax(CANSparkMax):
    def __init__(self, can_id):
        super().__init__(can_id, MotorType.kBrushless)
        self.reset()

    def set_percent_output(self, percent):
        super().set(percent)

    def get_percent_output(self):
        return super().get()

    get_pulses = Encoder.get_pulses
    get_revolutions = Encoder.get_revolutions

    def get_counts(self):
        return self.getEncoder().getPosition()

    def get_counts_per_revolution(self):
        return self.getEncoder().getCountsPerRevolution()

    def reset(self):
        self.getEncoder().setPosition(0)
