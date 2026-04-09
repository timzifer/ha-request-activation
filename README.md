# Request Activation

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A Home Assistant helper integration that combines multiple boolean entities with OR logic and an optional enable/disable override.

## Use Case

You have multiple independent reasons (requests) to activate something — a pump, a light, a fan, etc. Instead of creating template sensors and automations for each case, this integration handles it all in one place:

**Formula:** `enabled && (request_a || request_b || request_c || ...)`

### Examples

| Group | Request Sources | Target |
|---|---|---|
| Hot Water Circulation Pump | Timer, Boost, Heat Dump | `switch.circulation_pump` |
| Pool Filter Pump | Filtering, Heat Dump, Heating | `switch.pool_filter_pump` |
| Entrance Lighting | Time-based, Movement, Darkness | `light.entrance` |

## Features

- **Config Flow** — set up everything through the Home Assistant UI, no YAML needed
- **OR Logic** — output is ON when any request source is ON
- **Enable/Disable Override** — an optional entity can disable the entire group regardless of active requests
- **Direct Target Control** — optionally controls a target entity (switch, light, fan, etc.) directly, eliminating the need for a separate automation
- **Level Sensor** — shows how many request sources are currently active
- **Extra Attributes** — the binary sensor exposes `active_requests` and `total_requests` for diagnostics
- **Options Flow** — modify request sources, enabled entity, and target entity at any time after setup

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots in the top right corner and select **Custom repositories**
3. Add `https://github.com/timzifer/ha-request-activation` with category **Integration**
4. Search for **Request Activation** and install it
5. Restart Home Assistant

### Manual

1. Copy `custom_components/request_activation/` to your Home Assistant `custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** > **Devices & Services** > **Helpers**
2. Click **+ Create Helper** and select **Request Activation**
3. Enter a name for the group (e.g., "Hot Water Circulation Pump")
4. Select the **Request Entities** (boolean entities that act as request sources)
5. Optionally select an **Enabled Entity** (when OFF, the output is always OFF)
6. Optionally select a **Target Entity** (will be turned on/off automatically)

## Entities Created

For each request group, two entities are created:

| Entity | Type | Description |
|---|---|---|
| `binary_sensor.<name>` | Binary Sensor | `enabled && (a \|\| b \|\| c \|\| ...)` |
| `sensor.<name>_level` | Sensor | Count of currently active request sources |

### Binary Sensor Attributes

| Attribute | Description |
|---|---|
| `active_requests` | List of entity IDs that are currently ON |
| `total_requests` | Total number of configured request sources |

## Example

**Before** (template sensor + automation):

```yaml
template:
  - sensor:
      - name: "request_hot_water_circulation_pump_level"
        state: >-
          {% set level = 0 %}
          {% if is_state("input_boolean.request_by_timer", "on") %}{% set level = level +1 %}{% endif %}
          {% if is_state("input_boolean.request_for_boost", "on") %}{% set level = level +1 %}{% endif %}
          {% if is_state("input_boolean.request_for_heat_dump", "on") %}{% set level = level +1 %}{% endif %}
          {{ level }}

automation:
  - trigger:
      - platform: state
        entity_id: sensor.request_hot_water_circulation_pump_level
    action:
      - if: "{{ trigger.to_state.state | int > 0 }}"
        then:
          - service: switch.turn_on
            target:
              entity_id: switch.circulation_pump
        else:
          - service: switch.turn_off
            target:
              entity_id: switch.circulation_pump
```

**After** (Request Activation integration):

Just configure through the UI — select the three `input_boolean` entities as request sources and `switch.circulation_pump` as the target entity. Done.
