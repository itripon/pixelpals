import carla
import py_trees
from carla import ColorConverter as cc
from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import (
    ActorDestroy, ActorTransformSetter, AtomicBehavior, Idle, KeepVelocity,
    StopVehicle, WaypointFollower)

from utils.sensor_utils import sensor_convert_mapping


class SaveImagesBehaviour(AtomicBehavior):
    def __init__(self, images, sensor_type, date, name="SaveImagesBehaviour"):
        super(SaveImagesBehaviour, self).__init__(name)
        self._images = images
        self.sensor_type = sensor_type
        self.date = date

    def update(self):
        """
        update value of global osc parameter.
        """
        converter = sensor_convert_mapping.get(self.sensor_type)
        for image in self._images:
            image.save_to_disk(f'_out/{self.date}/{self.sensor_type}/{image.frame}.jpeg', converter)
        return py_trees.common.Status.SUCCESS

        # self.logger.debug(
        #     "%s.update()[%s->%s]" % (self.__class__.__name__, self.status, new_status))
        # return new_status
