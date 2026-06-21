// The complete composed ADAS model is deadlock-free.
A[] not deadlock

// Safety: throttle and brake are never active simultaneously.
A[] (brake > 0 imply throttle == 0)

// Emergency override always applies full brake and zero throttle.
A[] (control_agent.EmergencyOverride imply brake == 100 && throttle == 0)

// Controlled interventions use partial braking and zero throttle.
A[] (control_agent.ControlledOverride imply brake > 0 && brake < 100 && throttle == 0)

// Manual-driving mode does not command the vehicle.
A[] (decision.ManualDriving imply brake == 0 && throttle == 0)

// Green-light notification never takes control.
A[] (decision.NotificationOnly imply brake == 0 && throttle == 0)

// A valid pedestrian detection always leads to emergency braking.
object_role.PedestrianDetected --> control_agent.EmergencyOverride

// A valid red-light detection always leads to controlled braking.
traffic_role.RedLightDetected --> control_agent.ControlledOverride

// A valid green-light detection leads to notification-only behavior.
traffic_role.GreenLightDetected --> decision.NotificationOnly

// Emergency commands are issued within the configured response deadline.
A[] (monitor.AwaitEmergency imply monitor.response_t <= RESPONSE_DEADLINE)

// Controlled-braking commands are issued within the configured response deadline.
A[] (monitor.AwaitControlled imply monitor.response_t <= RESPONSE_DEADLINE)

// Notification-only commands are issued within the configured response deadline.
A[] (monitor.AwaitNotification imply monitor.response_t <= RESPONSE_DEADLINE)

// A red light above 15 km/h applies the code-derived 0.90 brake command.
A[] (command_scenario == SC_RED_FAST && control_agent.ControlledOverride imply brake == 90)

// A red light at or below 15 km/h applies the code-derived 0.60 brake command.
A[] (command_scenario == SC_RED_SLOW && control_agent.ControlledOverride imply brake == 60)

// A yellow light above 10 km/h applies the code-derived 0.45 brake command.
A[] (command_scenario == SC_YELLOW_FAST && control_agent.ControlledOverride imply brake == 45)

// A close vehicle above 20 km/h applies the code-derived 0.35 brake command.
A[] (command_scenario == SC_CLOSE_VEHICLE && control_agent.ControlledOverride imply brake == 35)

// Low-confidence perception does not cause an intervention.
A[] (command_scenario == SC_LOW_CONFIDENCE imply control_agent.StandbyHumanControl && brake == 0 && throttle == 0)

// Emergency-braking behavior is reachable.
E<> control_agent.EmergencyOverride

// Controlled-braking behavior is reachable.
E<> control_agent.ControlledOverride

// Green notification-only behavior is reachable.
E<> decision.NotificationOnly
