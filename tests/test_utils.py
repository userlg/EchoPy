import unittest
import numpy as np
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from utils import SmoothingBuffer, map_range, clamp

class TestUtils(unittest.TestCase):
    
    def test_map_range(self):
        self.assertEqual(map_range(5, 0, 10, 0, 100), 50)
        self.assertEqual(map_range(0, 0, 10, 0, 100), 0)
        self.assertEqual(map_range(10, 0, 10, 0, 100), 100)
        
    def test_clamp(self):
        self.assertEqual(clamp(5, 0, 10), 5)
        self.assertEqual(clamp(-5, 0, 10), 0)
        self.assertEqual(clamp(15, 0, 10), 10)
        
    def test_smoothing_buffer_initialization(self):
        size = 10
        sb = SmoothingBuffer(size, 0.8)
        self.assertEqual(sb.size, size)
        self.assertEqual(sb.smoothing, 0.8)
        self.assertEqual(len(sb.buffer), size)
        self.assertTrue(all(v == 0.0 for v in sb.buffer))
        
    def test_smoothing_buffer_update(self):
        sb = SmoothingBuffer(1, 0.5)
        # First update: 0.0 * 0.5 + 10.0 * 0.5 = 5.0
        result = sb.update([10.0])
        self.assertEqual(result[0], 5.0)
        
        # Second update: 5.0 * 0.5 + 10.0 * 0.5 = 7.5
        result = sb.update([10.0])
        self.assertEqual(result[0], 7.5)
        
    def test_smoothing_buffer_resize(self):
        sb = SmoothingBuffer(5, 0.8)
        new_values = [1.0, 2.0, 3.0]
        result = sb.update(new_values)
        self.assertEqual(sb.size, 3)
        self.assertEqual(len(result), 3)

if __name__ == '__main__':
    unittest.main()
