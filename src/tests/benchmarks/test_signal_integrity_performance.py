"""
Performance benchmarks for signal integrity and crosstalk analysis.
"""

import unittest
import time
import os
import psutil
from statistics import mean
import pcbnew
from kicad_pcb_generator.audio.analysis.analyzer import AudioPCBAnalyzer

class TestSignalIntegrityPerformance(unittest.TestCase):
    """Performance tests for signal integrity and crosstalk analysis."""
    
    def setUp(self):
        self.test_boards = self._load_test_boards()
        self.metrics = {
            'analysis_times': [],
            'memory_usage': [],
            'crosstalk': [],
            'signal_quality': []
        }
    
    def _load_test_boards(self):
        test_data_dir = os.path.join(
            os.path.dirname(__file__),
            '..', 'e2e', 'test_data'
        )
        return {
            'small': os.path.join(test_data_dir, 'valid_audio_pcb.kicad_pcb'),
            'medium': os.path.join(test_data_dir, 'invalid_signal_paths.kicad_pcb'),
            'large': os.path.join(test_data_dir, 'invalid_manufacturing.kicad_pcb')
        }

    def _measure_performance(self, func, *args, **kwargs):
        process = psutil.Process()
        memory_before = process.memory_info().rss
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        memory_after = process.memory_info().rss
        return {
            'execution_time': end_time - start_time,
            'memory_usage': memory_after - memory_before,
            'result': result
        }

    def test_signal_integrity_speed(self):
        """Test signal integrity analysis speed and crosstalk metrics."""
        for board_name, board_path in self.test_boards.items():
            board = pcbnew.LoadBoard(board_path)
            analyzer = AudioPCBAnalyzer(board, stability_manager=None)
            metrics = self._measure_performance(analyzer.analyze_signal_integrity)
            self.metrics['analysis_times'].append(metrics['execution_time'])
            self.metrics['memory_usage'].append(metrics['memory_usage'])
            # Collect crosstalk and signal quality for all nets
            for net, crosstalk in metrics['result'].crosstalk.items():
                self.metrics['crosstalk'].append(crosstalk)
            for net, quality in metrics['result'].signal_quality.items():
                self.metrics['signal_quality'].append(quality)
            # Assert performance
            self.assertLess(metrics['execution_time'], 2.0)  # <2s per board
            self.assertLess(metrics['memory_usage'], 100 * 1024 * 1024)  # <100MB
        # Assert crosstalk and signal quality are within expected ranges
        for crosstalk in self.metrics['crosstalk']:
            self.assertLessEqual(crosstalk, 0)
            self.assertGreaterEqual(crosstalk, -60)
        for quality in self.metrics['signal_quality']:
            self.assertGreaterEqual(quality, 0)
            self.assertLessEqual(quality, 1)

    def tearDown(self):
        if self.metrics['analysis_times']:
            print("\nSignal Integrity Performance Summary:")
            print(f"Average analysis time: {mean(self.metrics['analysis_times']):.3f}s")
            print(f"Max analysis time: {max(self.metrics['analysis_times']):.3f}s")
            print(f"Min analysis time: {min(self.metrics['analysis_times']):.3f}s")
            print(f"Average crosstalk: {mean(self.metrics['crosstalk']):.2f} dB")
            print(f"Average signal quality: {mean(self.metrics['signal_quality']):.2f}") 