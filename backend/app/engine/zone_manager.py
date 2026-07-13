from shapely.geometry import Point, Polygon

class ZoneManager:
    def __init__(self):
        self.zones = {} # camera_id -> list of zones

    def set_zones(self, camera_id: int, zones_data: list):
        """
        zones_data: [{"name": "zone1", "polygon": [{"x": 10, "y": 20}, ...], "risk_level": "CRITICAL"}]
        """
        parsed_zones = []
        for z in zones_data:
            poly_points = [(pt["x"], pt["y"]) for pt in z["polygon"]]
            if len(poly_points) >= 3:
                parsed_zones.append({
                    "name": z["name"],
                    "polygon": Polygon(poly_points),
                    "risk_level": z["risk_level"]
                })
        self.zones[camera_id] = parsed_zones

    def check_zone_violations(self, camera_id: int, detections: list):
        """
        Checks if the center bottom of a bounding box is within any restricted zone.
        """
        violations = []
        zones = self.zones.get(camera_id, [])
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            center_x = (x1 + x2) / 2
            bottom_y = y2
            pt = Point(center_x, bottom_y)
            
            for z in zones:
                if z["polygon"].contains(pt):
                    violations.append({
                        "track_id": det.get("track_id"),
                        "zone_name": z["name"],
                        "risk_level": z["risk_level"]
                    })
        return violations
