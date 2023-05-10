import carla
import py_trees
from carla import ColorConverter as cc
from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import (
    ActorDestroy, ActorTransformSetter, AtomicBehavior, Idle, KeepVelocity,
    StopVehicle, WaypointFollower)


class SaveImagesBehaviour(AtomicBehavior):
    def __init__(self, images, name="SaveImagesBehaviour"):
        super(SaveImagesBehaviour, self).__init__(name)
        self._images = images

    def update(self):
        """
        update value of global osc parameter.
        """
        for image in self._images:
            # self._images.append(image)
            image.save_to_disk(f'_out/123/{image.frame}.jpeg')
        return py_trees.common.Status.SUCCESS

        # self.logger.debug(
        #     "%s.update()[%s->%s]" % (self.__class__.__name__, self.status, new_status))
        # return new_status
