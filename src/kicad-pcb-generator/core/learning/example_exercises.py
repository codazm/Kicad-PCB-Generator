"""Example practice exercises for the KiCad PCB Generator."""

from typing import Dict, Any, List
from .learning_data import PracticeExercise

def get_audio_exercises() -> List[Dict[str, Any]]:
    """Get example audio PCB design exercises."""
    return [
        {
            'id': 'opamp_circuit',
            'title': 'Op-Amp Circuit Design',
            'description': 'Design a basic op-amp circuit with proper decoupling and feedback.',
            'category': 'audio',
            'difficulty': 'beginner',
            'validation_categories': ['audio', 'component', 'signal'],
            'instructions': '''
Design a non-inverting op-amp amplifier circuit with the following requirements:
1. Gain of 2x
2. Input impedance > 10kΩ
3. Output impedance < 100Ω
4. Proper decoupling capacitors
5. Feedback network with appropriate values

Use the following components:
- Op-amp: TL072
- Resistors: 10kΩ, 20kΩ
- Capacitors: 100nF ceramic
''',
            'solution_template': {
                'components': {
                    'U1': {
                        'type': 'opamp',
                        'value': 'TL072',
                        'position': {'x': 0, 'y': 0}
                    },
                    'R1': {
                        'type': 'resistor',
                        'value': '10k',
                        'position': {'x': 0, 'y': 1}
                    },
                    'R2': {
                        'type': 'resistor',
                        'value': '20k',
                        'position': {'x': 0, 'y': 2}
                    },
                    'C1': {
                        'type': 'capacitor',
                        'value': '100n',
                        'position': {'x': 1, 'y': 0}
                    },
                    'C2': {
                        'type': 'capacitor',
                        'value': '100n',
                        'position': {'x': 1, 'y': 1}
                    }
                },
                'nets': {
                    'VCC': ['U1.8', 'C1.1'],
                    'GND': ['U1.4', 'C1.2', 'C2.2'],
                    'IN': ['R1.1'],
                    'OUT': ['U1.1'],
                    'FB': ['R1.2', 'R2.1', 'U1.2']
                }
            },
            'validation_rules': [
                {
                    'name': 'gain_check',
                    'description': 'Check if gain is approximately 2x',
                    'validator': lambda x: abs(x['components']['R2']['value'] / x['components']['R1']['value'] - 2) < 0.1,
                    'error_message': 'Gain should be 2x (R2/R1 = 2)'
                },
                {
                    'name': 'decoupling_check',
                    'description': 'Check if decoupling capacitors are properly placed',
                    'validator': lambda x: all(
                        c['type'] == 'capacitor' and c['value'] == '100n'
                        for c in [x['components']['C1'], x['components']['C2']]
                    ),
                    'error_message': 'Decoupling capacitors should be 100nF ceramic'
                }
            ]
        },
        {
            'id': 'power_supply',
            'title': 'Power Supply Design',
            'description': 'Design a power supply for an audio circuit with proper filtering and regulation.',
            'category': 'audio',
            'difficulty': 'intermediate',
            'validation_categories': ['power', 'component', 'signal'],
            'instructions': '''
Design a power supply for an audio circuit with the following requirements:
1. Dual rail ±15V output
2. Ripple < 100mV
3. Current capacity > 500mA
4. Proper filtering and regulation
5. Protection circuits

Use the following components:
- Regulators: LM317, LM337
- Capacitors: 1000µF electrolytic, 100nF ceramic
- Diodes: 1N4007
- Resistors: 240Ω, 2.2kΩ
''',
            'solution_template': {
                'components': {
                    'U1': {
                        'type': 'regulator',
                        'value': 'LM317',
                        'position': {'x': 0, 'y': 0}
                    },
                    'U2': {
                        'type': 'regulator',
                        'value': 'LM337',
                        'position': {'x': 0, 'y': 1}
                    },
                    'C1': {
                        'type': 'capacitor',
                        'value': '1000u',
                        'position': {'x': 1, 'y': 0}
                    },
                    'C2': {
                        'type': 'capacitor',
                        'value': '100n',
                        'position': {'x': 1, 'y': 1}
                    },
                    'R1': {
                        'type': 'resistor',
                        'value': '240',
                        'position': {'x': 2, 'y': 0}
                    },
                    'R2': {
                        'type': 'resistor',
                        'value': '2.2k',
                        'position': {'x': 2, 'y': 1}
                    }
                },
                'nets': {
                    'VIN': ['U1.1', 'U2.1', 'C1.1'],
                    'GND': ['U1.2', 'U2.2', 'C1.2', 'C2.2'],
                    'VOUT+': ['U1.3', 'C2.1', 'R1.1'],
                    'VOUT-': ['U2.3', 'R2.1']
                }
            },
            'validation_rules': [
                {
                    'name': 'voltage_check',
                    'description': 'Check if output voltage is correct',
                    'validator': lambda x: all(
                        abs(float(r['value']) / 240 * 1.25 - 15) < 0.5
                        for r in [x['components']['R1'], x['components']['R2']]
                    ),
                    'error_message': 'Output voltage should be ±15V'
                },
                {
                    'name': 'filtering_check',
                    'description': 'Check if filtering capacitors are properly placed',
                    'validator': lambda x: all(
                        c['type'] == 'capacitor' and c['value'] in ['1000u', '100n']
                        for c in [x['components']['C1'], x['components']['C2']]
                    ),
                    'error_message': 'Filtering capacitors should be 1000µF electrolytic and 100nF ceramic'
                }
            ]
        },
        {
            'id': 'signal_integrity',
            'title': 'Signal Integrity',
            'description': 'Design a PCB layout with proper signal integrity considerations.',
            'category': 'audio',
            'difficulty': 'advanced',
            'validation_categories': ['signal', 'layout', 'component'],
            'instructions': '''
Design a PCB layout for an audio circuit with the following requirements:
1. Proper ground plane
2. Signal traces < 2mm from ground
3. Power traces > 0.5mm width
4. Component placement for minimal noise
5. Proper decoupling

Use the following components:
- Op-amp: OPA1612
- Resistors: 10kΩ, 20kΩ
- Capacitors: 100nF ceramic
''',
            'solution_template': {
                'components': {
                    'U1': {
                        'type': 'opamp',
                        'value': 'OPA1612',
                        'position': {'x': 0, 'y': 0}
                    },
                    'R1': {
                        'type': 'resistor',
                        'value': '10k',
                        'position': {'x': 1, 'y': 0}
                    },
                    'R2': {
                        'type': 'resistor',
                        'value': '20k',
                        'position': {'x': 1, 'y': 1}
                    },
                    'C1': {
                        'type': 'capacitor',
                        'value': '100n',
                        'position': {'x': 2, 'y': 0}
                    }
                },
                'traces': {
                    'signal': {
                        'width': 0.2,
                        'clearance': 0.2
                    },
                    'power': {
                        'width': 0.5,
                        'clearance': 0.3
                    },
                    'ground': {
                        'width': 0.3,
                        'clearance': 0.2
                    }
                },
                'layers': {
                    'top': {
                        'type': 'signal',
                        'components': ['U1', 'R1', 'R2', 'C1']
                    },
                    'bottom': {
                        'type': 'ground',
                        'fill': True
                    }
                }
            },
            'validation_rules': [
                {
                    'name': 'trace_width_check',
                    'description': 'Check if trace widths are appropriate',
                    'validator': lambda x: all(
                        x['traces'][t]['width'] >= w
                        for t, w in {'signal': 0.2, 'power': 0.5, 'ground': 0.3}.items()
                    ),
                    'error_message': 'Trace widths should be: signal ≥ 0.2mm, power ≥ 0.5mm, ground ≥ 0.3mm'
                },
                {
                    'name': 'ground_plane_check',
                    'description': 'Check if ground plane is properly implemented',
                    'validator': lambda x: (
                        'bottom' in x['layers'] and
                        x['layers']['bottom']['type'] == 'ground' and
                        x['layers']['bottom']['fill']
                    ),
                    'error_message': 'Bottom layer should be a filled ground plane'
                }
            ]
        }
    ] 
