# Task 3 MUML Diagrams

These diagrams document the community, role interactions, and overall agent behavior represented by the UPPAAL timed automata.

## Community and Component Structure

```mermaid
flowchart LR
    Sensor(("Camera and speed sensors"))
    Actuator(("CARLA vehicle actuator"))
    Driver(("Human driver / HUD"))

    subgraph ADAS["ADAS Community"]
        subgraph PA["Perception Agent"]
            OR["Object Detection Role"]
            TR["Traffic Light Detection Role"]
            PC["Perception Coordinator Role"]
        end

        subgraph DA["Decision Agent"]
            DR["Risk Decision Role"]
        end

        subgraph CA["Control Agent"]
            CR["Control Override Role"]
            NR["Driver Notification Role"]
        end
    end

    Sensor --> PC
    PC --> OR
    PC --> TR
    OR --> PC
    TR --> PC
    PC --> DR
    DR --> CR
    DR --> NR
    CR --> Actuator
    NR --> Driver
```

## Role Interaction Sequence

```mermaid
sequenceDiagram
    participant E as Environment
    participant P as Perception Agent
    participant O as Object Detection Role
    participant T as Traffic Light Role
    participant D as Decision Role
    participant C as Control Agent
    participant M as Response Monitor

    E->>P: frame + current speed
    P->>O: start_object
    P->>T: start_traffic
    O-->>P: pedestrian / vehicle / no valid object
    T-->>P: red / yellow / green / unknown
    P->>D: perception_ready
    P->>M: start bounded-response observation

    alt pedestrian detected
        D->>C: emergency_cmd, brake = 100
    else red, relevant yellow, or close vehicle
        D->>C: controlled_cmd, brake = 90 / 60 / 45 / 35
    else green
        D->>C: notification_cmd, no control intervention
    else no hazard or low confidence
        D->>C: manual_cmd, human retains control
    end

    D-->>M: issued command within response deadline
```

## Overall ADAS State Behavior

```mermaid
stateDiagram-v2
    [*] --> ManualDriving
    ManualDriving --> EmergencyBraking: valid pedestrian
    ManualDriving --> ControlledBraking: valid red light
    ManualDriving --> ControlledBraking: yellow and speed > 10
    ManualDriving --> ControlledBraking: close vehicle and speed > 20
    ManualDriving --> NotificationOnly: valid green light

    EmergencyBraking --> EmergencyBraking: pedestrian remains
    EmergencyBraking --> ControlledBraking: lower-priority braking hazard
    EmergencyBraking --> NotificationOnly: green, no braking hazard
    EmergencyBraking --> ManualDriving: no hazard

    ControlledBraking --> EmergencyBraking: pedestrian appears
    ControlledBraking --> ControlledBraking: braking hazard remains
    ControlledBraking --> NotificationOnly: green, no braking hazard
    ControlledBraking --> ManualDriving: no hazard

    NotificationOnly --> EmergencyBraking: pedestrian appears
    NotificationOnly --> ControlledBraking: braking hazard appears
    NotificationOnly --> NotificationOnly: green remains
    NotificationOnly --> ManualDriving: no hazard
```

## Decision Priority

```mermaid
flowchart TD
    Start["Combined perception result"] --> P{"Valid pedestrian?"}
    P -->|Yes| E["Emergency brake: 100%"]
    P -->|No| R{"Valid red light?"}
    R -->|Yes, speed > 15| R90["Controlled brake: 90%"]
    R -->|Yes, speed <= 15| R60["Controlled brake: 60%"]
    R -->|No| Y{"Valid yellow and speed > 10?"}
    Y -->|Yes| Y45["Controlled brake: 45%"]
    Y -->|No| V{"Valid close vehicle and speed > 20?"}
    V -->|Yes| V35["Controlled brake: 35%"]
    V -->|No| G{"Valid green light?"}
    G -->|Yes| N["Notify driver only"]
    G -->|No| M["Return manual control"]
```

