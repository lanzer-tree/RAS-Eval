{
  "roads": [
    {
      "road_id": "road-001",
      "name": "Broadway",
      "connected_intersections": ["int-001", "int-002"]
    },
    {
      "road_id": "road-002",
      "name": "5th Avenue",
      "connected_intersections": ["int-001", "int-003"]
    }
  ],
  "intersections": [
    {
      "intersection_id": "int-001",
      "name": "Broadway and 5th Avenue",
      "connected_roads": [{"road_id": "road-001", "road_name": "Broadway"}, {"road_id": "road-002", "road_name": "5th Avenue"}],
      "traffic_lights": [
        {"traffic_light_id": "tl-001", "traffic_light_type": "vehicle", "traffic_light_state": "red"},
        {"traffic_light_id": "tl-002", "traffic_light_type": "pedestrian", "traffic_light_state": "stop"}
      ],
      "congestion_level": "medium"
    },
    {
      "intersection_id": "int-002",
      "name": "Broadway and 7th Avenue",
      "connected_roads": [{"road_id": "road-001", "road_name": "Broadway"}],
      "traffic_lights": [
        {"traffic_light_id": "tl-003", "traffic_light_type": "vehicle", "traffic_light_state": "green"},
        {"traffic_light_id": "tl-004", "traffic_light_type": "pedestrian", "traffic_light_state": "walk"}
      ],
      "congestion_level": "low"
    },
    {
      "intersection_id": "int-003",
      "name": "5th Avenue and Main Street",
      "connected_roads": [{"road_id": "road-002", "road_name": "5th Avenue"}],
      "traffic_lights": [
        {"traffic_light_id": "tl-005", "traffic_light_type": "vehicle", "traffic_light_state": "green"},
        {"traffic_light_id": "tl-006", "traffic_light_type": "pedestrian", "traffic_light_state": "walk"}
      ],
      "congestion_level": "low"
    }
  ]
}
