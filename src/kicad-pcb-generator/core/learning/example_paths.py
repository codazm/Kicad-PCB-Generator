"""Example learning paths for the KiCad PCB Generator."""

from typing import Dict, Any
from .learning_data import TutorialStep, Tutorial, LearningModule, LearningPath

def get_basic_audio_path() -> Dict[str, Any]:
    """Get the basic audio PCB design learning path."""
    return {
        'id': 'basic_audio',
        'title': 'Basic Audio PCB Design',
        'description': 'Learn the fundamentals of designing audio PCBs, from basic concepts to manufacturing.',
        'modules': [
            {
                'id': 'audio_basics',
                'title': 'Audio Circuit Basics',
                'description': 'Learn the fundamental concepts of audio circuits and PCB design.',
                'tutorials': [
                    {
                        'id': 'audio_components',
                        'title': 'Audio Components',
                        'description': 'Understanding common audio components and their properties.',
                        'steps': [
                            TutorialStep(
                                id='components_intro',
                                title='Introduction to Audio Components',
                                content='Learn about resistors, capacitors, and inductors in audio circuits.',
                                interactive_elements=[
                                    {
                                        'type': 'checkbox',
                                        'text': 'I understand the basic properties of audio components',
                                        'required': True
                                    }
                                ]
                            ),
                            TutorialStep(
                                id='component_selection',
                                title='Component Selection',
                                content='How to choose the right components for audio circuits.',
                                interactive_elements=[
                                    {
                                        'type': 'checkbox',
                                        'text': 'I can select appropriate components for audio circuits',
                                        'required': True
                                    }
                                ]
                            )
                        ]
                    },
                    {
                        'id': 'audio_circuits',
                        'title': 'Basic Audio Circuits',
                        'description': 'Understanding common audio circuit topologies.',
                        'steps': [
                            TutorialStep(
                                id='circuit_basics',
                                title='Circuit Basics',
                                content='Learn about voltage dividers, filters, and amplifiers.',
                                interactive_elements=[
                                    {
                                        'type': 'checkbox',
                                        'text': 'I understand basic audio circuit topologies',
                                        'required': True
                                    }
                                ]
                            )
                        ]
                    }
                ],
                'practice_exercises': [
                    {
                        'id': 'component_selection_exercise',
                        'title': 'Component Selection Exercise',
                        'description': 'Practice selecting components for a simple audio circuit.',
                        'instructions': 'Select appropriate components for a basic audio amplifier.',
                        'solution': 'Detailed solution with component values and explanations.'
                    }
                ]
            },
            {
                'id': 'pcb_layout',
                'title': 'PCB Layout for Audio',
                'description': 'Learn how to create effective PCB layouts for audio circuits.',
                'tutorials': [
                    {
                        'id': 'layout_basics',
                        'title': 'Layout Basics',
                        'description': 'Understanding PCB layout principles for audio circuits.',
                        'steps': [
                            TutorialStep(
                                id='grounding',
                                title='Grounding Techniques',
                                content='Learn about proper grounding for audio circuits.',
                                interactive_elements=[
                                    {
                                        'type': 'checkbox',
                                        'text': 'I understand audio grounding principles',
                                        'required': True
                                    }
                                ]
                            ),
                            TutorialStep(
                                id='component_placement',
                                title='Component Placement',
                                content='How to place components for optimal audio performance.',
                                interactive_elements=[
                                    {
                                        'type': 'checkbox',
                                        'text': 'I can place components for good audio performance',
                                        'required': True
                                    }
                                ]
                            )
                        ]
                    }
                ],
                'practice_exercises': [
                    {
                        'id': 'layout_exercise',
                        'title': 'Layout Exercise',
                        'description': 'Practice creating a PCB layout for an audio circuit.',
                        'instructions': 'Create a layout for a simple audio amplifier.',
                        'solution': 'Detailed solution with layout guidelines.'
                    }
                ]
            },
            {
                'id': 'manufacturing',
                'title': 'Manufacturing Preparation',
                'description': 'Learn how to prepare your audio PCB for manufacturing.',
                'tutorials': [
                    {
                        'id': 'manufacturing_basics',
                        'title': 'Manufacturing Basics',
                        'description': 'Understanding the manufacturing process for audio PCBs.',
                        'steps': [
                            TutorialStep(
                                id='gerber_files',
                                title='Gerber Files',
                                content='How to generate and check Gerber files.',
                                interactive_elements=[
                                    {
                                        'type': 'checkbox',
                                        'text': 'I can generate and check Gerber files',
                                        'required': True
                                    }
                                ]
                            ),
                            TutorialStep(
                                id='bom_preparation',
                                title='BOM Preparation',
                                content='How to create a Bill of Materials for manufacturing.',
                                interactive_elements=[
                                    {
                                        'type': 'checkbox',
                                        'text': 'I can create a manufacturing BOM',
                                        'required': True
                                    }
                                ]
                            )
                        ]
                    }
                ],
                'practice_exercises': [
                    {
                        'id': 'manufacturing_exercise',
                        'title': 'Manufacturing Exercise',
                        'description': 'Practice preparing manufacturing files for an audio PCB.',
                        'instructions': 'Generate manufacturing files for your audio amplifier.',
                        'solution': 'Detailed solution with file generation steps.'
                    }
                ]
            }
        ],
        'difficulty': 'beginner',
        'category': 'audio',
        'tags': ['audio', 'pcb', 'beginner', 'manufacturing'],
        'estimated_time': '10 hours'
    }

def get_advanced_audio_path() -> Dict[str, Any]:
    """Get the advanced audio PCB design learning path."""
    return {
        'id': 'advanced_audio',
        'title': 'Advanced Audio PCB Design',
        'description': 'Master advanced techniques for high-performance audio PCB design.',
        'prerequisites': ['basic_audio'],
        'modules': [
            {
                'id': 'signal_integrity',
                'title': 'Signal Integrity',
                'description': 'Advanced signal integrity techniques for audio circuits.',
                'tutorials': [
                    {
                        'id': 'impedance_matching',
                        'title': 'Impedance Matching',
                        'description': 'Learn about impedance matching in audio circuits.',
                        'steps': [
                            TutorialStep(
                                id='impedance_basics',
                                title='Impedance Basics',
                                content='Understanding impedance in audio circuits.',
                                interactive_elements=[
                                    {
                                        'type': 'checkbox',
                                        'text': 'I understand audio impedance concepts',
                                        'required': True
                                    }
                                ]
                            ),
                            TutorialStep(
                                id='matching_techniques',
                                title='Matching Techniques',
                                content='How to implement impedance matching in audio circuits.',
                                interactive_elements=[
                                    {
                                        'type': 'checkbox',
                                        'text': 'I can implement impedance matching',
                                        'required': True
                                    }
                                ]
                            )
                        ]
                    }
                ],
                'practice_exercises': [
                    {
                        'id': 'impedance_exercise',
                        'title': 'Impedance Matching Exercise',
                        'description': 'Practice implementing impedance matching in an audio circuit.',
                        'instructions': 'Design an impedance matching network for an audio amplifier.',
                        'solution': 'Detailed solution with matching network design.'
                    }
                ]
            },
            {
                'id': 'noise_reduction',
                'title': 'Noise Reduction',
                'description': 'Advanced techniques for reducing noise in audio circuits.',
                'tutorials': [
                    {
                        'id': 'noise_analysis',
                        'title': 'Noise Analysis',
                        'description': 'Learn how to analyze and reduce noise in audio circuits.',
                        'steps': [
                            TutorialStep(
                                id='noise_sources',
                                title='Noise Sources',
                                content='Understanding common noise sources in audio circuits.',
                                interactive_elements=[
                                    {
                                        'type': 'checkbox',
                                        'text': 'I can identify noise sources in audio circuits',
                                        'required': True
                                    }
                                ]
                            ),
                            TutorialStep(
                                id='reduction_techniques',
                                title='Noise Reduction Techniques',
                                content='How to implement noise reduction in audio circuits.',
                                interactive_elements=[
                                    {
                                        'type': 'checkbox',
                                        'text': 'I can implement noise reduction techniques',
                                        'required': True
                                    }
                                ]
                            )
                        ]
                    }
                ],
                'practice_exercises': [
                    {
                        'id': 'noise_exercise',
                        'title': 'Noise Reduction Exercise',
                        'description': 'Practice reducing noise in an audio circuit.',
                        'instructions': 'Design a low-noise audio amplifier.',
                        'solution': 'Detailed solution with noise reduction techniques.'
                    }
                ]
            }
        ],
        'difficulty': 'advanced',
        'category': 'audio',
        'tags': ['audio', 'pcb', 'advanced', 'signal-integrity', 'noise-reduction'],
        'estimated_time': '15 hours'
    } 