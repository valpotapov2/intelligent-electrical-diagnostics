# FAA DRPDS — equipment decomposition and diagnostic dependency register

**Status:** source-backed decomposition proposal; not an as-built equipment inventory.  
**Parent model:** `examples/objects/faa-drpds.generic.json`  
**Primary description:** `docs/objects/faa-drpds-technical-description.md`

## 1. Purpose and modeling rule

The generic graph currently contains 29 component records and intentionally groups several equipment families. This register decomposes those groups into diagnostic entities without pretending that a historical FAA reference architecture identifies the installed equipment at a particular facility.

Three levels are kept separate:

1. **Family node** — the existing group in the generic graph.
2. **Equipment role** — a functional role supported by the source (for example UPS 2 / Critical Bus A).
3. **Installed instance** — a physical device with site tag, manufacturer, model, ratings, terminals and wiring. These details require current site-specific drawings and equipment records.

Only levels 1 and 2 are described here. Level 3 remains unresolved until site evidence is available. No new physical IDs, cable paths, terminal numbers, ratings, or measurement limits are asserted.

## 2. Equipment decomposition

| Existing family node | Source-backed equipment roles | Count evidence in historical FAA reference | Modeling decision / unresolved detail |
|---|---|---|---|
| `EGSET` | Individual engine-generator sets; each has engine, generator, starting system, fuel, lubrication, cooling, controller and output breaker functions | Number is facility-dependent; reference says installed quantity exceeds the number required for supported load by at least two units | Keep a family node plus an indexed role template `EG-i`; actual count, tags, ratings and per-unit auxiliaries are unknown |
| `PSG` | Generator switchgear / common generator bus; generator incomers and standby feeders toward 1M2 and 2M2 | Common bus and two standby paths are described | Separate bus, incomers, outgoing breakers and protection only when the source drawing establishes their identities and connections |
| `SWGR1`, `SWGR2` | Two main switchgear sections; commercial incomer 1M1 / 2M1; standby incomer 1M2 / 2M2; tie breaker; section protection and controls | Two sections and named incomer roles are described | Existing graph has the named breakers but not bus sections, protective relays, sensing fuses, interlocks or internal bus topology as separate entities |
| `ESS-SWBD` | Essential switchboards and downstream feeders | Multiple switchboards; exact count and feeder allocation are facility-specific | Do not model as a single physical board; retain family until one-line drawings provide tags and section boundaries |
| `MCC` | Motor control centers, motor feeders and motor loads | MCCs are described; exact count and outgoing feeder inventory are not established | Decompose to MCC sections/feeders/motors only from equipment schedules and drawings |
| `UPS-GROUP` | Working UPS 1, UPS 2, UPS 3; test UPS | Historical typical arrangement: three working UPS plus a separate test UPS; UPS 1 is bypass reserve for UPS 2/3, UPS 2 supplies Critical Bus A, UPS 3 supplies Critical Bus B | These roles are documented as historical typical configuration, not universal facility count. Internal rectifier, inverter, static bypass, maintenance bypass and battery subassemblies are not yet individually represented |
| `UPS-SWBD` | Separate output switchboard for each working UPS | Per-UPS output switchboards are described | Keep role template `UPS-OUT-i`; actual tags, breaker positions and bus arrangement require site drawings |
| `BUS-A`, `BUS-B` | Critical Bus A and Critical Bus B | Two named critical buses | Preserve as separate buses; exact bus sections, tie arrangements and downstream feeder assignment remain unknown |
| `PDU-GROUP` | Individual PDUs; input, internal conversion/distribution, protective devices and outgoing feeders | Eight PDUs in the described typical configuration; six for HCF | Model indexed roles `PDU-i`; the six/eight variant is facility-specific. Do not infer a pairing map without the source drawing |
| `SATS-GROUP` | Individual SATS; source A input, source B input, selected-source state and output | Each PDU feeds two SATS; each SATS has two independent source inputs. The described typical PDU count implies a family of SATS, but exact installed tags and mapping are not provided in the generic graph | Record the two-source functional role; do not generate a site wiring map or claim all source pairs from aggregate counts |
| `CDP-GROUP` | Individual critical distribution panels; SATS-fed incoming path; outgoing critical branch circuits and assigned loads | Four CDPs in the described typical configuration; three for HCF | Keep the family node. Diagnostic decomposition separates SATS-to-CDP incoming path from CDP outgoing branch/load. Actual CDP tags, incomer assignments, branch identities, protective devices and load allocation require site drawings and schedules |
| `PMCS` | OWS-1, OWS-2, PLC, PowerLogic/metering devices, communications network and software/control interfaces | Two operator stations and PLC are described; exact I/O and network topology are not | Separate monitoring/control equipment roles from power components. Signal-level links remain unmodeled unless documented |
| `DC125` | 125 V DC control-power source, battery system, charger/distribution and control loads | 125 V DC control power and batteries are described | Battery count, charger arrangement, distribution panels, fuses and branch circuits are unknown; no terminal-level point is assigned |
| `LOADBANK-SWBD`, `LOADBANK` | Load-bank switching/distribution and load bank | Test connection function is described | Preserve as test-only path; exact interlocks, disconnects, connectors and ratings require approved drawings/procedure |

### Count and configuration cautions

- The historical description distinguishes a general typical arrangement from the Honolulu Combined Facility (HCF) exception. Counts must therefore be stored with a configuration qualifier, not as universal constants.
- The source does not establish installed serial numbers, site tags, manufacturer/model for every unit, exact protective-device ratings, conductor sizes, or physical locations.
- A family count is not a wiring relationship. For example, knowing that there are PDUs and SATS does not identify which individual PDU output feeds which SATS input.
- The current graph's `ESS-SWBD` and `UPS-SWGR` nodes are functional aggregations, not proof of one physical enclosure each.

## 3. Diagnostic dependency register

These are prerequisite relationships for diagnosis, not fault-causality assertions. A dependency means that a downstream conclusion cannot be made reliably without checking or accounting for the upstream condition.

| Diagnostic question | Required evidence / upstream dependencies | Distinguishing observations | What cannot be concluded from one observation |
|---|---|---|---|
| Is a commercial source unavailable? | Source-side measurement channel health; transformer input/output; sensing fuse/voltage-transformer channel where present; SWGR incomer state | Independent voltage indication, phase values, sensing-channel status, breaker command and position | A zero PMCS value alone does not prove loss of the utility source |
| Did SWGR transfer to standby? (umbrella) | Commercial source; generator bus readiness; control power; control mode; transfer permissives; breaker actuation/feedback | End-to-end event evidence from authority/mode through permissives, command, position and independent electrical state | A CLOSE command or displayed breaker status alone does not prove closed primary contacts |\n| Is SWGR control authority and mode consistent with transfer? | Breaker identity; AUTO/LOCAL/MANUAL selector; active PMCS/local authority; controller availability | Selector state, command origin, controller/PMCS availability and event history | Do not presume AUTO or infer authority from a screen label alone |\n| Are source, tie and interlock permissives satisfied? | Both relevant source states; standby incomer permissives; tie state; documented mutual interlocks; event-time context | Permissive/interlock states at command time and source availability | Do not invent permissive equations, timer values or source-paralleling logic |\n| Did the breaker execute the command and provide trustworthy feedback? | Command and timestamp; control power; actuator response; auxiliary position feedback; independent electrical state | Command/response comparison, position feedback quality and independent section/path state | Auxiliary contact or PMCS status alone does not prove primary-contact condition |
| Is generator capacity available? | Per-generator start/run/ready state; voltage/frequency; output breaker; common bus; load-shed state | Individual unit alarms and electrical output, bus conditions, number of available units, load state | A running engine alone does not establish an electrically available generator |
| Is an essential load unavailable? | Essential source path; switchboard feeder; MCC section; protective device/contactor; motor and local load | Voltage/current at feeder, protective trip, contactor state, motor/controller fault | A downstream stopped motor does not identify whether the cause is upstream supply, protection, control or motor |
| Can an individual generator start and reach run/ready? | Generator identity and start context; starting battery/system; fuel, lubrication, temperature/cooling; controller and alarms | Start/run/ready state, auxiliary-system evidence, controller/alarm state | A start command or cranking alone does not prove a generator is ready |
| Has the running generator reached acceptable electrical output? | Individual generator identity and run/ready state; voltage/frequency; measurement-channel validity | Unit output voltage and frequency with timestamp/quality and independent confirmation where available | Engine running or aggregate bus status does not prove each unit has acceptable output |
| Has the generator synchronized with and connected to the common bus? | Individual unit output; common-bus state; synchronization evidence; output-breaker command and position | Synchronization state, breaker feedback, independent electrical confirmation of connection | A close command or run/ready indication does not prove connection to the bus |
| Is the connected generator fleet sufficient for the documented load? | Connected/available unit count; current load demand; capacity/reserve and load-shed criteria | Bus capacity evidence, load shed/restore state and event context | Historical typical generator count is not a universal site capacity threshold |
| Is generator capacity electrically available? (umbrella) | Start/readiness, electrical output, synchronization/connection and fleet capacity/load-response assessments | Combined unit and bus evidence, available capacity and load-shed/restore context | Do not infer capacity from engine-running state or typical unit counts alone |
| Is a UPS maintaining the critical path? | UPS input; operating mode; rectifier/inverter or bypass status; DC bus/battery; UPS output breaker and output SWBD | Input/output quality, NORMAL/BATTERY/BYPASS/FAULT state, battery test/state, alarms and event history | UPS output voltage alone does not prove inverter operation or battery autonomy |
| Is Critical Bus A/B available? | Assigned UPS output path; output switchboard breaker; bus state; measurement-channel validity | Bus voltage/status, upstream UPS mode and breaker state, independent indication | A PMCS bus indication alone does not prove physical bus condition |
| Is SATS supplying the load from the intended source? | Both SATS input qualities; source-selection logic; transfer state; output path; upstream PDU/bus states | Both input measurements, selected-source indication, transfer events, output measurement | SATS output present does not establish that both redundant inputs are healthy |
| Is the SATS-to-CDP incoming path available? | Individual CDP identity and documented SATS output assignment; SATS output; CDP incomer; incoming protective device where documented | SATS output and CDP incomer states, measurement quality, current one-line assignment | Aggregate SATS-to-CDP relationship does not identify an installed panel or incomer assignment |
| Is a CDP outgoing branch available? | Individual CDP and branch identity; branch protective device; documented critical-load assignment; downstream evidence | Protective-device state, branch/load-side evidence, local load state | A live CDP incomer does not prove every outgoing branch is available; a dead load alone does not localize the fault |
| Is a CDP outgoing circuit unavailable? (umbrella) | Incoming-path assessment plus individual outgoing-branch assessment | Combined localization across SATS output, CDP incomer, branch protection/circuit and local load | Do not infer an installed circuit map from the generic graph |
| Is the PMCS measurement channel valid? | Identified instrument/PowerLogic source and documented signal identity | Instrument/device diagnostics, measurement quality and timestamp, independent comparison where available | A displayed value without source identity and quality does not establish a valid measurement |
| Has the PLC acquired the signal correctly? | Documented source-to-PLC signal mapping; I/O channel; PLC acquisition state | I/O diagnostics, PLC state, source value compared with PLC-acquired value | An OWS display alone does not prove correct PLC acquisition |
| Is current PLC data reaching the active OWS? | Documented data path where available; communications; active OWS; data freshness | Network/communications state, timestamp/quality, PLC value compared with OWS display | Two redundant OWS stations do not prove identical or current displayed data |
| Is PMCS reporting a real equipment state? (umbrella) | Measurement-channel, PLC-acquisition and active-OWS communications/freshness assessments; DC control power; independent physical/electrical cross-check | End-to-end comparison from source instrument through PLC to active OWS, with timestamp/quality and independent equipment evidence | A PMCS screen indication alone is not independent confirmation of physical equipment state |
| Is a switching failure caused by DC control power? | DC source/charger/battery; DC distribution fuse/branch; trip/close coil circuit; control relay | DC bus and branch availability, fuse/relay/coil evidence, command history | A breaker that does not move does not by itself prove a mechanical breaker defect |

## 4. Diagnostic observation-point templates

The existing technical description names functional points TP-U1 through TP-PMCS. This register preserves them as logical observation templates only. They are not physical test terminals.

| Template | Attach to | Minimum evidence package | Site data still required |
|---|---|---|---|
| TP-U1 / TP-U2 | Commercial transformer output / corresponding SWGR incoming path | Per-phase source values, measurement quality, timestamp, related incomer state | Actual terminal IDs, nominal values, instrument/channel and approved access method |
| TP-SWGR1 / TP-SWGR2 | Main switchgear section and its incomers | Source-side and load-side evidence, breaker command/position, mode, interlock state | Breaker tags, terminals, relay/VT channels, exact one-line topology |
| TP-TIE | Tie breaker and both associated sections | Both section states, tie command/position, permissives and interlocks | Actual tie logic, electrical/mechanical interlock details and terminal mapping |
| TP-EG-i / TP-PSG | Individual generator output and common generator bus | Unit ready/run/alarms, voltage/frequency, breaker state, bus condition, synchronization evidence | Installed unit count/tags, ratings, sensing points and approved test access |
| TP-1M2 / TP-2M2 | Standby incomers | Generator-bus availability, incomer command/position, section voltage | Actual apparatus tags, permissives and terminals |
| TP-ESSENTIAL | Essential switchboard / selected MCC feeder | Upstream source, feeder protective state, MCC/control state, load response | Specific board, feeder, motor tags and local control scheme |
| TP-UPS-IN-i / TP-UPS-OUT-i / TP-UPS-DC-i | Individual UPS input, output and DC/battery subsystem | UPS mode, input/output, DC/battery state, alarms, event log | UPS tags/model, battery arrangement, manufacturer test method and safe measurement procedure |
| TP-CRIT-A / TP-CRIT-B | Critical buses | Bus state and quality, assigned UPS/output breaker context | Physical bus sections, sensing channels and approved access |
| TP-PDU-i | Individual PDU input/output | Input and output evidence, protection state, load state | PDU tag, internal topology, output circuit schedule |
| TP-SATS-i | Individual SATS | Both input states, selected source, transfer events, output state | SATS tag, input-source mapping, model-specific status semantics |
| TP-CDP-i | Individual CDP and selected outgoing circuit | Panel input, branch protection, outgoing circuit/load evidence | Panel and circuit tags, cable/load schedule |
| TP-DC125 | 125 V DC control-power system | DC bus/branch state, charger/battery alarms, fuse/branch status | Battery/charger layout, fuse schedule, terminal IDs and approved procedure |
| TP-PMCS | PMCS signal chain | Data timestamp/quality, I/O, PLC, communications and physical cross-check | I/O list, network topology, point list and signal source mapping |

## 5. Rules for promoting a role into the electrical graph

A role may become an individual graph component only when all applicable conditions are met:

1. Its existence is explicitly supported by an identified source.
2. The source distinguishes it as an individual item or a distinct functional node.
3. Its source reference resolves to a page/figure/text passage.
4. Any unknown tag, count, rating or connection remains null/unknown.
5. Connections are added only when the source establishes both endpoints and the relationship.
6. A count from a typical architecture is stored as a qualified variant, not copied into a site inventory.
7. A logical observation template is not converted into a physical terminal or measurement point without site drawings and an approved procedure.

## 6. Explicit open items

- Obtain current site-specific one-line diagrams and equipment schedules before creating installed instances.
- Obtain UPS, PDU, SATS and CDP schedules to resolve individual equipment mapping.
- Obtain generator lineup and switchgear control/interlock drawings.
- Obtain PMCS I/O list, network architecture and point database to split combined control/monitoring edges.
- Obtain DC control-power schematic and battery/charger schedule.
- Obtain protective-device coordination/settings documents before modeling trip curves, selectivity or ZSI behavior.
- Confirm current applicable FAA policy and site-approved maintenance procedures before defining field measurement methods.

## 7. Source boundary

This register derives equipment roles and functional dependencies from the repository's FAA DRPDS technical description and its cited historical FAA JO 6480.22 figures/paragraphs. The historical order is cancelled and is used as a detailed architecture reference only. The register does not claim that its example counts, device allocation, or operating logic describe a current named facility. Current policy context is recorded separately in the technical description.

No electrical ratings, live measurements, terminal references, protective settings, or field switching instructions are introduced by this register.
