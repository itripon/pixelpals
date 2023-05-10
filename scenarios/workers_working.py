#!/usr/bin/env python

# Copyright (c) 2018-2020 Intel Corporation
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
Follow leading vehicle scenario:

The scenario realizes a common driving behavior, in which the
user-controlled ego vehicle follows a leading car driving down
a given road. At some point the leading car has to slow down and
finally stop. The ego vehicle has to react accordingly to avoid
a collision. The scenario ends either via a timeout, or if the ego
vehicle stopped close enough to the leading vehicle
"""

import random
import weakref

import carla
import py_trees
from carla import ColorConverter as cc
from save_images_behaviour import SaveImagesBehaviour
from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import (
    ActorDestroy, ActorTransformSetter, Idle, KeepVelocity, StopVehicle,
    WaypointFollower)
from srunner.scenariomanager.scenarioatomics.atomic_criteria import \
    CollisionTest
from srunner.scenariomanager.scenarioatomics.atomic_trigger_conditions import (
    DriveDistance, InTriggerDistanceToNextIntersection,
    InTriggerDistanceToVehicle, StandStill)
from srunner.scenariomanager.timer import TimeOut
from srunner.scenarios.basic_scenario import BasicScenario
from srunner.tools.scenario_helper import get_waypoint_in_distance

conversion_types = {
    "sensor.camera.rgb": cc.Raw,
    "sensor.camera.semantic_segmentation": cc.CityScapesPalette,
}


class WorkersWorkingScenario(BasicScenario):

    """
    This class holds everything required for a simple "Follow a leading vehicle"
    scenario involving two vehicles.  (Traffic Scenario 2)

    This is a single ego vehicle scenario
    """

    timeout = 1020            # Timeout of scenario in seconds

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True,
                 timeout=60):
        """
        Setup all relevant parameters and create scenario

        If randomize is True, the scenario parameters are randomized
        """

        self._map = CarlaDataProvider.get_map()
        self._world = world
        self._first_vehicle_location = 25
        self._first_vehicle_speed = 10
        self._reference_waypoint = self._map.get_waypoint(
            config.trigger_points[0].location)
        self._other_actor_max_brake = 1.0
        self._other_actor_stop_in_front_intersection = 20
        self._other_actor_transform = None
        # Timeout of scenario in seconds
        self.timeout = timeout
        self._images = []
        self._target_speeds = []

        super(WorkersWorkingScenario, self).__init__("WorkersWorking",
                                                     ego_vehicles,
                                                     config,
                                                     world,
                                                     debug_mode,
                                                     criteria_enable=criteria_enable)

    def _setup_scenario_trigger(self, config):
        return None

    def _initialize_actors(self, config):
        """
        Custom initialization
        """
        self.camera_sensors = []
        pedestrian_configs = [
            actor for actor in config.other_actors if actor.model.startswith("walker")]
        pedestrian_actors = CarlaDataProvider.request_new_actors(
            pedestrian_configs)
        for ped_config in pedestrian_configs:
            self._target_speeds.append(float(ped_config.speed))

        self.other_actors.extend(pedestrian_actors)
        misc_actors = CarlaDataProvider.request_new_actors(
            [actor for actor in config.other_actors if actor.model.startswith("static")])
        self.other_actors.extend(misc_actors)

        bp_library = self._world.get_blueprint_library()
        for camera in [camera for camera in config.other_actors if camera.model.startswith("sensor.camera")]:
            bp = bp_library.find(camera.model)
            bp.set_attribute('image_size_x', str(1280))
            bp.set_attribute('image_size_y', str(720))
            bp.set_attribute('sensor_tick', '0')
            # bp.set_attribute('gamma', '2.2')
            camera_actor = self._world.spawn_actor(bp, camera.transform)
            self.camera_sensors.append(
                camera_actor
            )
            actor_ref = weakref.ref(camera_actor)

            def _parse_rgb_image(actor_ref, convert_type, image):
                actor = actor_ref()
                image.convert(convert_type)
                image.save_to_disk(f'_out/{actor.id}/{image.frame}.jpeg')

            def _parse_seg_image(actor_ref, convert_type, image):
                actor = actor_ref()
                image.convert(convert_type)
                self._images.append(image)
                # image.save_to_disk(f'_out/{actor.id}/{image.frame}.jpeg')
            if camera.model.endswith("rgb"):
                camera_actor.listen(
                    lambda image: _parse_rgb_image(actor_ref, conversion_types[camera.model], image))
            else:
                camera_actor.listen(
                    lambda image: _parse_seg_image(actor_ref, conversion_types[camera.model], image))
            # self.other_actors

    def _create_behavior(self):
        """
        The scenario defined after is a "follow leading vehicle" scenario. After
        invoking this scenario, it will wait for the user controlled vehicle to
        enter the start region, then make the other actor to drive until reaching
        the next intersection. Finally, the user-controlled vehicle has to be close
        enough to the other actor to end the scenario.
        If this does not happen within 60 seconds, a timeout stops the scenario
        """

        # to avoid the other actor blocking traffic, it was spawed elsewhere
        # reset its pose to the required one
        # start_transform = ActorTransformSetter(
        #     self.other_actors[0], self._other_actor_transform)

        # let the other actor drive until next intersection
        # @todo: We should add some feedback mechanism to respond to ego_vehicle behavior
        driving_to_next_intersection = py_trees.composites.Parallel(
            "DrivingTowardsIntersection",
            policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL)

        # driving_to_next_intersection.add_child(WaypointFollower(
        #     self.other_actors[0], self._first_vehicle_speed))
        for index, pedestrian in enumerate([_ for _ in self.other_actors if _.type_id.startswith('walker.pedestrian')]):
            driving_to_next_intersection.add_child(KeepVelocity(
                pedestrian,
                target_velocity=self._target_speeds[index],
                duration=10))

        # stop vehicle
        stop = StopVehicle(self.other_actors[0], self._other_actor_max_brake)

        # Build behavior tree
        sequence = py_trees.composites.Sequence("Sequence Behavior")
        # sequence.add_child(start_transform)
        sequence.add_child(driving_to_next_intersection)
        sequence.add_child(stop)
        sequence.add_child(Idle(25))
        # sequence.add_child(SaveImagesBehaviour(self._images))
        # sequence.add_child(ActorDestroy(self.other_actors[0]))

        return sequence

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        criteria = []

        collision_criterion = CollisionTest(self.ego_vehicles[0])

        criteria.append(collision_criterion)

        return criteria

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()
