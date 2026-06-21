from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "task3_upaal"
OUT_DIR.mkdir(parents=True, exist_ok=True)


GLOBAL_DECLARATIONS = r"""
// CARLA ADAS Task 3 model. Time unit: milliseconds.
const int FRAME_PERIOD = 67;          // approximately 15 camera frames per second
const int PROCESS_MIN = 5;
const int PROCESS_MAX = 60;
const int RESPONSE_DEADLINE = 100;

const int PED_CONF_THRESHOLD = 70;    // my_adas.py: 0.70
const int VEH_CONF_THRESHOLD = 50;    // my_adas.py: 0.50
const int TL_CONF_THRESHOLD = 75;     // my_adas.py: 0.75

const int SC_NONE = 0;
const int SC_PEDESTRIAN = 1;
const int SC_RED_FAST = 2;
const int SC_RED_SLOW = 3;
const int SC_YELLOW_FAST = 4;
const int SC_YELLOW_SLOW = 5;
const int SC_GREEN = 6;
const int SC_CLOSE_VEHICLE = 7;
const int SC_FAR_VEHICLE = 8;
const int SC_LOW_CONFIDENCE = 9;

const int TL_UNKNOWN = 0;
const int TL_RED = 1;
const int TL_YELLOW = 2;
const int TL_GREEN = 3;

broadcast chan frame;
broadcast chan start_object, start_traffic;
broadcast chan object_done, traffic_done, perception_ready;
broadcast chan emergency_cmd, controlled_cmd, notification_cmd, manual_cmd;

int[0,9] scenario = SC_NONE;
int[0,100] obj_conf = 0;
int[0,100] tl_conf = 0;
int[0,120] speed_kmh = 0;

bool pedestrian_valid = false;
bool vehicle_valid = false;
bool vehicle_close = false;
int[0,3] traffic_state = TL_UNKNOWN;

int[0,100] requested_brake = 0;
int[0,9] command_scenario = SC_NONE;
int[0,100] throttle = 0;
int[0,100] brake = 0;
int[-100,100] steer = 0;
bool alert_active = false;
bool warning_active = false;
bool notification_active = false;

void configure_scenario(int s)
{
    scenario = s;
    obj_conf = 0;
    tl_conf = 0;
    speed_kmh = 30;
    vehicle_close = false;

    if (s == SC_PEDESTRIAN) obj_conf = 85;
    if (s == SC_RED_FAST) { tl_conf = 85; speed_kmh = 40; }
    if (s == SC_RED_SLOW) { tl_conf = 85; speed_kmh = 10; }
    if (s == SC_YELLOW_FAST) { tl_conf = 85; speed_kmh = 30; }
    if (s == SC_YELLOW_SLOW) { tl_conf = 85; speed_kmh = 5; }
    if (s == SC_GREEN) { tl_conf = 85; speed_kmh = 20; }
    if (s == SC_CLOSE_VEHICLE) {
        obj_conf = 80; speed_kmh = 40; vehicle_close = true;
    }
    if (s == SC_FAR_VEHICLE) { obj_conf = 80; speed_kmh = 40; }
    if (s == SC_LOW_CONFIDENCE) { obj_conf = 65; tl_conf = 70; }
}

void reset_perception()
{
    pedestrian_valid = false;
    vehicle_valid = false;
    traffic_state = TL_UNKNOWN;
}

void apply_emergency()
{
    command_scenario = scenario;
    throttle = 0; brake = 100; steer = 0;
    alert_active = true;
    warning_active = false;
    notification_active = false;
}

void apply_controlled()
{
    command_scenario = scenario;
    throttle = 0; brake = requested_brake; steer = 0;
    alert_active = requested_brake >= 60;
    warning_active = requested_brake < 60;
    notification_active = false;
}

void apply_notification()
{
    command_scenario = scenario;
    throttle = 0; brake = 0; steer = 0;
    alert_active = false;
    warning_active = false;
    notification_active = true;
}

void apply_manual()
{
    command_scenario = scenario;
    throttle = 0; brake = 0; steer = 0;
    alert_active = false;
    warning_active = false;
    notification_active = false;
}

bool valid_pedestrian()
{
    return scenario == SC_PEDESTRIAN && obj_conf >= PED_CONF_THRESHOLD;
}

bool valid_vehicle()
{
    return (scenario == SC_CLOSE_VEHICLE || scenario == SC_FAR_VEHICLE)
        && obj_conf >= VEH_CONF_THRESHOLD;
}

bool valid_red_light()
{
    return (scenario == SC_RED_FAST || scenario == SC_RED_SLOW)
        && tl_conf >= TL_CONF_THRESHOLD;
}

bool valid_yellow_light()
{
    return (scenario == SC_YELLOW_FAST || scenario == SC_YELLOW_SLOW)
        && tl_conf >= TL_CONF_THRESHOLD;
}

bool valid_green_light()
{
    return scenario == SC_GREEN && tl_conf >= TL_CONF_THRESHOLD;
}

bool need_emergency()
{
    return pedestrian_valid;
}

bool need_red_brake()
{
    return !pedestrian_valid && traffic_state == TL_RED;
}

bool need_yellow_brake()
{
    return !pedestrian_valid && traffic_state == TL_YELLOW && speed_kmh > 10;
}

bool need_vehicle_brake()
{
    return !pedestrian_valid
        && traffic_state != TL_RED
        && !(traffic_state == TL_YELLOW && speed_kmh > 10)
        && vehicle_valid && vehicle_close && speed_kmh > 20;
}

bool need_controlled()
{
    return need_red_brake() || need_yellow_brake() || need_vehicle_brake();
}

bool need_notification()
{
    return !need_emergency() && !need_red_brake()
        && !need_yellow_brake() && !need_vehicle_brake()
        && traffic_state == TL_GREEN;
}

bool need_manual()
{
    return !need_emergency() && !need_red_brake()
        && !need_yellow_brake() && !need_vehicle_brake()
        && !need_notification();
}
""".strip()


QUERIES = [
    (
        "A[] not deadlock",
        "The complete composed ADAS model is deadlock-free.",
    ),
    (
        "A[] (brake > 0 imply throttle == 0)",
        "Safety: throttle and brake are never active simultaneously.",
    ),
    (
        "A[] (control_agent.EmergencyOverride imply brake == 100 && throttle == 0)",
        "Emergency override always applies full brake and zero throttle.",
    ),
    (
        "A[] (control_agent.ControlledOverride imply brake > 0 && brake < 100 && throttle == 0)",
        "Controlled interventions use partial braking and zero throttle.",
    ),
    (
        "A[] (decision.ManualDriving imply brake == 0 && throttle == 0)",
        "Manual-driving mode does not command the vehicle.",
    ),
    (
        "A[] (decision.NotificationOnly imply brake == 0 && throttle == 0)",
        "Green-light notification never takes control.",
    ),
    (
        "object_role.PedestrianDetected --> control_agent.EmergencyOverride",
        "A valid pedestrian detection always leads to emergency braking.",
    ),
    (
        "traffic_role.RedLightDetected --> control_agent.ControlledOverride",
        "A valid red-light detection always leads to controlled braking.",
    ),
    (
        "traffic_role.GreenLightDetected --> decision.NotificationOnly",
        "A valid green-light detection leads to notification-only behavior.",
    ),
    (
        "A[] (monitor.AwaitEmergency imply monitor.response_t <= RESPONSE_DEADLINE)",
        "Emergency commands are issued within the configured response deadline.",
    ),
    (
        "A[] (monitor.AwaitControlled imply monitor.response_t <= RESPONSE_DEADLINE)",
        "Controlled-braking commands are issued within the configured response deadline.",
    ),
    (
        "A[] (monitor.AwaitNotification imply monitor.response_t <= RESPONSE_DEADLINE)",
        "Notification-only commands are issued within the configured response deadline.",
    ),
    (
        "A[] (command_scenario == SC_RED_FAST && control_agent.ControlledOverride imply brake == 90)",
        "A red light above 15 km/h applies the code-derived 0.90 brake command.",
    ),
    (
        "A[] (command_scenario == SC_RED_SLOW && control_agent.ControlledOverride imply brake == 60)",
        "A red light at or below 15 km/h applies the code-derived 0.60 brake command.",
    ),
    (
        "A[] (command_scenario == SC_YELLOW_FAST && control_agent.ControlledOverride imply brake == 45)",
        "A yellow light above 10 km/h applies the code-derived 0.45 brake command.",
    ),
    (
        "A[] (command_scenario == SC_CLOSE_VEHICLE && control_agent.ControlledOverride imply brake == 35)",
        "A close vehicle above 20 km/h applies the code-derived 0.35 brake command.",
    ),
    (
        "A[] (command_scenario == SC_LOW_CONFIDENCE imply control_agent.StandbyHumanControl && brake == 0 && throttle == 0)",
        "Low-confidence perception does not cause an intervention.",
    ),
    (
        "E<> control_agent.EmergencyOverride",
        "Emergency-braking behavior is reachable.",
    ),
    (
        "E<> control_agent.ControlledOverride",
        "Controlled-braking behavior is reachable.",
    ),
    (
        "E<> decision.NotificationOnly",
        "Green notification-only behavior is reachable.",
    ),
]


def add_location(template, loc_id, name, x, y, invariant=None, committed=False):
    loc = ET.SubElement(template, "location", id=loc_id, x=str(x), y=str(y))
    ET.SubElement(loc, "name", x=str(x - 25), y=str(y - 30)).text = name
    if invariant:
        ET.SubElement(
            loc, "label", kind="invariant", x=str(x - 30), y=str(y + 15)
        ).text = invariant
    if committed:
        ET.SubElement(loc, "committed")
    return loc


def add_transition(
    template,
    source,
    target,
    source_xy,
    target_xy,
    guard=None,
    sync=None,
    assignment=None,
    nails=None,
    label_offset=0,
    label_xy=None,
):
    transition = ET.SubElement(template, "transition")
    ET.SubElement(transition, "source", ref=source)
    ET.SubElement(transition, "target", ref=target)
    sx, sy = source_xy
    tx, ty = target_xy
    if label_xy:
        lx, ly = label_xy
    else:
        lx = (sx + tx) // 2 + label_offset
        ly = (sy + ty) // 2 + label_offset
    if guard:
        ET.SubElement(
            transition, "label", kind="guard", x=str(lx), y=str(ly - 36)
        ).text = guard
    if sync:
        ET.SubElement(
            transition, "label", kind="synchronisation", x=str(lx), y=str(ly - 18)
        ).text = sync
    if assignment:
        ET.SubElement(
            transition, "label", kind="assignment", x=str(lx), y=str(ly)
        ).text = assignment
    for nail_x, nail_y in nails or []:
        ET.SubElement(transition, "nail", x=str(nail_x), y=str(nail_y))
    return transition


def new_template(root, name, declaration=""):
    template = ET.SubElement(root, "template")
    ET.SubElement(template, "name").text = name
    ET.SubElement(template, "declaration").text = declaration
    return template


def build_scenario_generator(root):
    template = new_template(root, "ScenarioGenerator", "clock frame_t;")
    coords = {"sg_wait": (-650, 0)}
    add_location(template, "sg_wait", "WaitNextFrame", -650, 0, "frame_t <= FRAME_PERIOD")
    scenarios = [
        ("sg_none", "NoHazard", 0, -720, "SC_NONE"),
        ("sg_ped", "Pedestrian", 0, -560, "SC_PEDESTRIAN"),
        ("sg_red_fast", "RedFast", 0, -400, "SC_RED_FAST"),
        ("sg_red_slow", "RedSlow", 0, -240, "SC_RED_SLOW"),
        ("sg_yellow_fast", "YellowFast", 0, -80, "SC_YELLOW_FAST"),
        ("sg_yellow_slow", "YellowSlow", 0, 80, "SC_YELLOW_SLOW"),
        ("sg_green", "Green", 0, 240, "SC_GREEN"),
        ("sg_close_vehicle", "CloseVehicle", 0, 400, "SC_CLOSE_VEHICLE"),
        ("sg_far_vehicle", "FarVehicle", 0, 560, "SC_FAR_VEHICLE"),
        ("sg_low_conf", "LowConfidence", 0, 720, "SC_LOW_CONFIDENCE"),
    ]
    for index, (loc_id, name, x, y, scenario_const) in enumerate(scenarios):
        coords[loc_id] = (x, y)
        add_location(template, loc_id, name, x, y, committed=True)
        add_transition(
            template,
            "sg_wait",
            loc_id,
            coords["sg_wait"],
            coords[loc_id],
            guard="frame_t >= FRAME_PERIOD",
            assignment=f"configure_scenario({scenario_const})",
            nails=[(-330, y)],
            label_xy=(-600 + (index % 2) * 160, y - 35),
        )
        add_transition(
            template,
            loc_id,
            "sg_wait",
            coords[loc_id],
            coords["sg_wait"],
            sync="frame!",
            assignment="frame_t = 0",
            nails=[(-180, y + 55), (-500, y + 55)],
            label_xy=(-310, y + 60),
        )
    ET.SubElement(template, "init", ref="sg_wait")


def build_perception_agent(root):
    template = new_template(root, "PerceptionAgent", "clock cycle_t;\nbool object_ready = false;\nbool traffic_ready = false;")
    coords = {
        "pa_idle": (-700, 0),
        "pa_start_obj": (-350, 0),
        "pa_start_tl": (0, 0),
        "pa_await": (350, 0),
        "pa_publish": (700, 0),
    }
    add_location(template, "pa_idle", "Idle", *coords["pa_idle"])
    add_location(template, "pa_start_obj", "StartObjectRole", *coords["pa_start_obj"], committed=True)
    add_location(template, "pa_start_tl", "StartTrafficRole", *coords["pa_start_tl"], committed=True)
    add_location(template, "pa_await", "AwaitRoleResults", *coords["pa_await"], "cycle_t <= PROCESS_MAX")
    add_location(template, "pa_publish", "PublishPerception", *coords["pa_publish"], committed=True)
    add_transition(
        template, "pa_idle", "pa_start_obj", coords["pa_idle"], coords["pa_start_obj"],
        sync="frame?",
        assignment="cycle_t = 0, object_ready = false, traffic_ready = false, reset_perception()",
        label_xy=(-590, -70),
    )
    add_transition(template, "pa_start_obj", "pa_start_tl", coords["pa_start_obj"], coords["pa_start_tl"], sync="start_object!", label_xy=(-230, -45))
    add_transition(template, "pa_start_tl", "pa_await", coords["pa_start_tl"], coords["pa_await"], sync="start_traffic!", label_xy=(120, -45))
    add_transition(template, "pa_await", "pa_await", coords["pa_await"], coords["pa_await"], sync="object_done?", assignment="object_ready = true", nails=[(250, -180), (450, -180)], label_xy=(270, -165))
    add_transition(template, "pa_await", "pa_await", coords["pa_await"], coords["pa_await"], sync="traffic_done?", assignment="traffic_ready = true", nails=[(250, 180), (450, 180)], label_xy=(270, 175))
    add_transition(template, "pa_await", "pa_publish", coords["pa_await"], coords["pa_publish"], guard="object_ready && traffic_ready", label_xy=(455, -50))
    add_transition(template, "pa_publish", "pa_idle", coords["pa_publish"], coords["pa_idle"], sync="perception_ready!", nails=[(700, 280), (-700, 280)], label_xy=(-80, 270))
    ET.SubElement(template, "init", ref="pa_idle")


def build_object_role(root):
    template = new_template(root, "ObjectDetectionRole", "clock obj_t;")
    coords = {
        "or_wait": (-650, 0),
        "or_process": (-250, 0),
        "or_ped": (450, -300),
        "or_vehicle": (450, 0),
        "or_none": (450, 300),
    }
    add_location(template, "or_wait", "Waiting", *coords["or_wait"])
    add_location(template, "or_process", "ProcessImage", *coords["or_process"], "obj_t <= PROCESS_MAX")
    add_location(template, "or_ped", "PedestrianDetected", *coords["or_ped"], committed=True)
    add_location(template, "or_vehicle", "VehicleDetected", *coords["or_vehicle"], committed=True)
    add_location(template, "or_none", "NoValidObject", *coords["or_none"], committed=True)
    add_transition(template, "or_wait", "or_process", coords["or_wait"], coords["or_process"], sync="start_object?", assignment="obj_t = 0", label_xy=(-520, -55))
    add_transition(
        template, "or_process", "or_ped", coords["or_process"], coords["or_ped"],
        guard="obj_t >= PROCESS_MIN && valid_pedestrian()",
        assignment="pedestrian_valid = true, vehicle_valid = false",
        nails=[(50, -300)],
        label_xy=(-100, -280),
    )
    add_transition(
        template, "or_process", "or_vehicle", coords["or_process"], coords["or_vehicle"],
        guard="obj_t >= PROCESS_MIN && valid_vehicle()",
        assignment="pedestrian_valid = false, vehicle_valid = true",
        label_xy=(-50, -55),
    )
    add_transition(
        template, "or_process", "or_none", coords["or_process"], coords["or_none"],
        guard="obj_t >= PROCESS_MIN && !valid_pedestrian() && !valid_vehicle()",
        assignment="pedestrian_valid = false, vehicle_valid = false",
        nails=[(50, 300)],
        label_xy=(-100, 270),
    )
    add_transition(template, "or_ped", "or_wait", coords["or_ped"], coords["or_wait"], sync="object_done!", nails=[(450, -430), (-650, -430)], label_xy=(-150, -425))
    add_transition(template, "or_vehicle", "or_wait", coords["or_vehicle"], coords["or_wait"], sync="object_done!", nails=[(450, -100), (-650, -100)], label_xy=(-150, -95))
    add_transition(template, "or_none", "or_wait", coords["or_none"], coords["or_wait"], sync="object_done!", nails=[(450, 430), (-650, 430)], label_xy=(-150, 425))
    ET.SubElement(template, "init", ref="or_wait")


def build_traffic_role(root):
    template = new_template(root, "TrafficLightRole", "clock tl_t;")
    coords = {
        "tr_wait": (-700, 0),
        "tr_process": (-300, 0),
        "tr_red": (500, -450),
        "tr_yellow": (500, -150),
        "tr_green": (500, 150),
        "tr_unknown": (500, 450),
    }
    add_location(template, "tr_wait", "Waiting", *coords["tr_wait"])
    add_location(template, "tr_process", "ProcessImage", *coords["tr_process"], "tl_t <= PROCESS_MAX")
    add_location(template, "tr_red", "RedLightDetected", *coords["tr_red"], committed=True)
    add_location(template, "tr_yellow", "YellowLightDetected", *coords["tr_yellow"], committed=True)
    add_location(template, "tr_green", "GreenLightDetected", *coords["tr_green"], committed=True)
    add_location(template, "tr_unknown", "UnknownOrLowConfidence", *coords["tr_unknown"], committed=True)
    add_transition(template, "tr_wait", "tr_process", coords["tr_wait"], coords["tr_process"], sync="start_traffic?", assignment="tl_t = 0", label_xy=(-570, -55))
    add_transition(
        template, "tr_process", "tr_red", coords["tr_process"], coords["tr_red"],
        guard="tl_t >= PROCESS_MIN && valid_red_light()",
        assignment="traffic_state = TL_RED",
        nails=[(50, -450)],
        label_xy=(-100, -425),
    )
    add_transition(
        template, "tr_process", "tr_yellow", coords["tr_process"], coords["tr_yellow"],
        guard="tl_t >= PROCESS_MIN && valid_yellow_light()",
        assignment="traffic_state = TL_YELLOW",
        nails=[(50, -150)],
        label_xy=(-100, -125),
    )
    add_transition(
        template, "tr_process", "tr_green", coords["tr_process"], coords["tr_green"],
        guard="tl_t >= PROCESS_MIN && valid_green_light()",
        assignment="traffic_state = TL_GREEN",
        nails=[(50, 150)],
        label_xy=(-100, 175),
    )
    add_transition(
        template, "tr_process", "tr_unknown", coords["tr_process"], coords["tr_unknown"],
        guard="tl_t >= PROCESS_MIN && !valid_red_light() && !valid_yellow_light() && !valid_green_light()",
        assignment="traffic_state = TL_UNKNOWN",
        nails=[(50, 450)],
        label_xy=(-100, 475),
    )
    for index, loc_id in enumerate(("tr_red", "tr_yellow", "tr_green", "tr_unknown")):
        x, y = coords[loc_id]
        return_y = y + (-100 if index < 2 else 100)
        nails = [(x + 180, y), (x + 180, return_y), (-700, return_y)]
        add_transition(template, loc_id, "tr_wait", coords[loc_id], coords["tr_wait"], sync="traffic_done!", nails=nails, label_xy=(100, return_y - 10))
    ET.SubElement(template, "init", ref="tr_wait")


def build_decision_role(root):
    template = new_template(root, "DecisionRole")
    coords = {
        "dr_evaluate": (-550, 0),
        "dr_issue_emergency": (0, -600),
        "dr_issue_red_fast": (0, -400),
        "dr_issue_red_slow": (0, -200),
        "dr_issue_yellow": (0, 0),
        "dr_issue_vehicle": (0, 200),
        "dr_issue_notification": (0, 400),
        "dr_issue_manual": (0, 600),
        "dr_emergency": (700, -500),
        "dr_controlled": (700, -100),
        "dr_notification": (700, 300),
        "dr_manual": (700, 600),
    }
    add_location(template, "dr_manual", "ManualDriving", *coords["dr_manual"])
    add_location(template, "dr_emergency", "EmergencyBraking", *coords["dr_emergency"])
    add_location(template, "dr_controlled", "ControlledBraking", *coords["dr_controlled"])
    add_location(template, "dr_notification", "NotificationOnly", *coords["dr_notification"])
    add_location(template, "dr_evaluate", "EvaluateRisk", *coords["dr_evaluate"], committed=True)
    add_location(template, "dr_issue_emergency", "IssueEmergency", *coords["dr_issue_emergency"], committed=True)
    add_location(template, "dr_issue_red_fast", "IssueRedFast", *coords["dr_issue_red_fast"], committed=True)
    add_location(template, "dr_issue_red_slow", "IssueRedSlow", *coords["dr_issue_red_slow"], committed=True)
    add_location(template, "dr_issue_yellow", "IssueYellow", *coords["dr_issue_yellow"], committed=True)
    add_location(template, "dr_issue_vehicle", "IssueVehicle", *coords["dr_issue_vehicle"], committed=True)
    add_location(template, "dr_issue_notification", "IssueNotification", *coords["dr_issue_notification"], committed=True)
    add_location(template, "dr_issue_manual", "IssueManual", *coords["dr_issue_manual"], committed=True)

    stable = ["dr_manual", "dr_emergency", "dr_controlled", "dr_notification"]
    for source_index, source in enumerate(stable):
        sx, sy = coords[source]
        route_y = -760 - source_index * 90
        add_transition(
            template, source, "dr_evaluate", coords[source], coords["dr_evaluate"],
            sync="perception_ready?",
            nails=[(sx + 180, sy), (sx + 180, route_y), (-550, route_y)],
            label_xy=(80, route_y - 10),
        )

    rules = [
        ("dr_issue_emergency", "need_emergency()", None),
        ("dr_issue_red_fast", "need_red_brake() && speed_kmh > 15", "requested_brake = 90"),
        ("dr_issue_red_slow", "need_red_brake() && speed_kmh <= 15", "requested_brake = 60"),
        ("dr_issue_yellow", "need_yellow_brake()", "requested_brake = 45"),
        ("dr_issue_vehicle", "need_vehicle_brake()", "requested_brake = 35"),
        ("dr_issue_notification", "need_notification()", None),
        ("dr_issue_manual", "need_manual()", None),
    ]
    for target, guard, assignment in rules:
        _, ty = coords[target]
        add_transition(
            template, "dr_evaluate", target, coords["dr_evaluate"], coords[target],
            guard=guard, assignment=assignment,
            nails=[(-280, ty)],
            label_xy=(-450, ty - 25),
        )

    add_transition(
        template, "dr_issue_emergency", "dr_emergency", coords["dr_issue_emergency"], coords["dr_emergency"],
        sync="emergency_cmd!",
        assignment="apply_emergency()",
        label_xy=(280, -590),
    )
    for index, source in enumerate(("dr_issue_red_fast", "dr_issue_red_slow", "dr_issue_yellow", "dr_issue_vehicle")):
        _, sy = coords[source]
        route_x = 350 + index * 70
        add_transition(
            template, source, "dr_controlled", coords[source], coords["dr_controlled"],
            sync="controlled_cmd!", assignment="apply_controlled()",
            nails=[(route_x, sy), (route_x, -100)],
            label_xy=(route_x - 50, sy - 20),
        )
    add_transition(
        template, "dr_issue_notification", "dr_notification", coords["dr_issue_notification"], coords["dr_notification"],
        sync="notification_cmd!",
        assignment="apply_notification()",
        label_xy=(280, 360),
    )
    add_transition(
        template, "dr_issue_manual", "dr_manual", coords["dr_issue_manual"], coords["dr_manual"],
        sync="manual_cmd!",
        assignment="apply_manual()",
        label_xy=(280, 550),
    )
    ET.SubElement(template, "init", ref="dr_manual")


def build_control_agent(root):
    template = new_template(root, "ControlAgent")
    coords = {
        "ca_standby": (-500, 0),
        "ca_emergency": (350, -350),
        "ca_controlled": (350, 0),
        "ca_notify": (350, 350),
    }
    add_location(template, "ca_standby", "StandbyHumanControl", *coords["ca_standby"])
    add_location(template, "ca_emergency", "EmergencyOverride", *coords["ca_emergency"], committed=True)
    add_location(template, "ca_controlled", "ControlledOverride", *coords["ca_controlled"], committed=True)
    add_location(template, "ca_notify", "DriverNotification", *coords["ca_notify"], committed=True)
    add_transition(template, "ca_standby", "ca_emergency", coords["ca_standby"], coords["ca_emergency"], sync="emergency_cmd?", label_xy=(-100, -230))
    add_transition(template, "ca_standby", "ca_controlled", coords["ca_standby"], coords["ca_controlled"], sync="controlled_cmd?", label_xy=(-100, -45))
    add_transition(template, "ca_standby", "ca_notify", coords["ca_standby"], coords["ca_notify"], sync="notification_cmd?", label_xy=(-100, 220))
    add_transition(template, "ca_standby", "ca_standby", coords["ca_standby"], coords["ca_standby"], sync="manual_cmd?", nails=[(-650, -120), (-350, -120)], label_xy=(-570, -115))
    for source, y in (("ca_emergency", -350), ("ca_controlled", 0), ("ca_notify", 350)):
        add_transition(
            template, source, "ca_standby", coords[source], coords["ca_standby"],
            nails=[(550, y), (550, 550), (-500, 550)],
        )
    ET.SubElement(template, "init", ref="ca_standby")


def build_response_monitor(root):
    template = new_template(root, "ResponseMonitor", "clock response_t;")
    coords = {
        "rm_idle": (-550, 0),
        "rm_emergency": (450, -400),
        "rm_controlled": (450, 0),
        "rm_notification": (450, 400),
    }
    add_location(template, "rm_idle", "Idle", *coords["rm_idle"])
    add_location(template, "rm_emergency", "AwaitEmergency", *coords["rm_emergency"], "response_t <= RESPONSE_DEADLINE")
    add_location(template, "rm_controlled", "AwaitControlled", *coords["rm_controlled"], "response_t <= RESPONSE_DEADLINE")
    add_location(template, "rm_notification", "AwaitNotification", *coords["rm_notification"], "response_t <= RESPONSE_DEADLINE")
    add_transition(template, "rm_idle", "rm_emergency", coords["rm_idle"], coords["rm_emergency"], guard="need_emergency()", sync="perception_ready?", assignment="response_t = 0", nails=[(-50, -400)], label_xy=(-350, -360))
    add_transition(template, "rm_idle", "rm_controlled", coords["rm_idle"], coords["rm_controlled"], guard="need_controlled()", sync="perception_ready?", assignment="response_t = 0", label_xy=(-200, -55))
    add_transition(template, "rm_idle", "rm_notification", coords["rm_idle"], coords["rm_notification"], guard="need_notification()", sync="perception_ready?", assignment="response_t = 0", nails=[(-50, 400)], label_xy=(-350, 360))
    add_transition(template, "rm_idle", "rm_idle", coords["rm_idle"], coords["rm_idle"], guard="need_manual()", sync="perception_ready?", nails=[(-700, -170), (-400, -170)], label_xy=(-630, -165))
    add_transition(template, "rm_emergency", "rm_idle", coords["rm_emergency"], coords["rm_idle"], sync="emergency_cmd?", nails=[(600, -400), (600, -550), (-550, -550)], label_xy=(-50, -545))
    add_transition(template, "rm_controlled", "rm_idle", coords["rm_controlled"], coords["rm_idle"], sync="controlled_cmd?", nails=[(450, -120), (-550, -120)], label_xy=(-50, -115))
    add_transition(template, "rm_notification", "rm_idle", coords["rm_notification"], coords["rm_idle"], sync="notification_cmd?", nails=[(600, 400), (600, 550), (-550, 550)], label_xy=(-50, 545))
    ET.SubElement(template, "init", ref="rm_idle")


def build_model():
    root = ET.Element("nta")
    ET.SubElement(root, "declaration").text = GLOBAL_DECLARATIONS
    build_scenario_generator(root)
    build_perception_agent(root)
    build_object_role(root)
    build_traffic_role(root)
    build_decision_role(root)
    build_control_agent(root)
    build_response_monitor(root)

    # UPPAAL's flat-system DTD requires strict template child ordering:
    # name/parameter/declaration, all locations, init, then transitions.
    # The builder functions create elements in logical construction order,
    # so normalize every template before serialization.
    for template in root.findall("template"):
        children = list(template)
        ordered = []
        for tag in ("name", "parameter", "declaration"):
            ordered.extend(child for child in children if child.tag == tag)
        ordered.extend(child for child in children if child.tag in ("location", "branchpoint"))
        ordered.extend(child for child in children if child.tag == "init")
        ordered.extend(child for child in children if child.tag == "transition")
        ordered.extend(
            child
            for child in children
            if child.tag not in {
                "name", "parameter", "declaration", "location",
                "branchpoint", "init", "transition",
            }
        )
        template[:] = ordered

    system_text = """
generator = ScenarioGenerator();
perception = PerceptionAgent();
object_role = ObjectDetectionRole();
traffic_role = TrafficLightRole();
decision = DecisionRole();
control_agent = ControlAgent();
monitor = ResponseMonitor();

system generator, perception, object_role, traffic_role, decision, control_agent, monitor;
""".strip()
    ET.SubElement(root, "system").text = system_text
    queries = ET.SubElement(root, "queries")
    for formula, comment in QUERIES:
        query = ET.SubElement(queries, "query")
        ET.SubElement(query, "formula").text = formula
        ET.SubElement(query, "comment").text = comment
    return root


def write_outputs():
    root = build_model()
    body = ET.tostring(root, encoding="unicode")
    header = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<!DOCTYPE nta PUBLIC "-//Uppaal Team//DTD Flat System 1.6//EN" '
        '"http://www.it.uu.se/research/group/darts/uppaal/flat-1_6.dtd">\n'
    )
    xml_path = OUT_DIR / "Carla_ADAS_Task3_UPPAAL.xml"
    xml_path.write_text(header + body + "\n", encoding="utf-8")

    query_path = OUT_DIR / "Carla_ADAS_Task3_Verifier_Queries.q"
    query_lines = []
    for formula, comment in QUERIES:
        query_lines.append(f"// {comment}")
        query_lines.append(formula)
        query_lines.append("")
    query_path.write_text("\n".join(query_lines), encoding="utf-8")

    print(f"Created {xml_path}")
    print(f"Created {query_path}")


if __name__ == "__main__":
    write_outputs()
