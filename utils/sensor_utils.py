import weakref

import carla
from carla import ColorConverter as cc

class RGBSensor(object):
    def __init__(self, world, transform, time_str, converter=cc.Raw):
        bp = world.get_blueprint_library().find('sensor.camera.rgb')
        bp.set_attribute('image_size_x', str(1280))
        bp.set_attribute('image_size_y', str(720))
        # bp.set_attribute('fov', str(VIEW_FOV))
        self.sensor = world.spawn_actor(bp, transform)
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: RGBSensor._on_rgb_event(weak_self, event))
        self.images = []
        self.time_str = time_str
        self.sensor_type = "rgb"

    @staticmethod
    def _on_rgb_event(weak_self, image):
        _self = weak_self()
        if not _self:
            return
        _self.images.append(image)

class SemanticSegmentationSensor(object):
    def __init__(self, world, transform, time_str, converter=cc.CityScapesPalette):
        bp = world.get_blueprint_library().find('sensor.camera.semantic_segmentation')
        bp.set_attribute('image_size_x', str(1280))
        bp.set_attribute('image_size_y', str(720))
        # bp.set_attribute('fov', str(VIEW_FOV))
        self.sensor = world.spawn_actor(bp, transform)
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: SemanticSegmentationSensor._on_segmented_event(weak_self, event))
        self.images = []
        self.time_str = time_str
        self.sensor_type = "segment"

    @staticmethod
    def _on_segmented_event(weak_self, image):
        _self = weak_self()
        if not _self:
            return
        _self.images.append(image)

sensor_convert_mapping = {
    'rgb': cc.Raw,
    'segment': cc.CityScapesPalette
}
sensor_mapping = {
    'sensor.camera.rgb': RGBSensor,
    'sensor.camera.semantic_segmentation': SemanticSegmentationSensor
}

