#!/usr/bin/env python3
"""Creation System Full Test Suite
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest

from core.creation_agents import ScriptLongAgent, ScriptShortAgent
from core.script_guard import ScriptGuard
from core.story_analyzer import StoryAnalyzer


class TestScriptShort(unittest.TestCase):
    """Short video script tests"""

    def test_create_project(self):
        agent = ScriptShortAgent()
        session = agent.create_project("Test Title", "douyin", "drama")
        self.assertIsNotNone(session)
        self.assertEqual(session.track, "short")
        print(f"OK: Created short script {session.id}")


class TestScriptLong(unittest.TestCase):
    """Novel tests"""

    def test_create_novel(self):
        agent = ScriptLongAgent()
        session = agent.create_project("Test Novel", "qidian", "fantasy", 100)
        self.assertIsNotNone(session)
        self.assertEqual(session.track, "long")
        print(f"OK: Created novel {session.id}")


class TestStoryAnalyzer(unittest.TestCase):
    """Analyzer tests"""

    def test_analyze(self):
        analyzer = StoryAnalyzer()
        content = "Chapter 1: The beginning. He never expected the betrayal."
        report = analyzer.analyze(content, "Test", "short")
        self.assertGreater(report.hook_score, 0)
        print(f"OK: Hook score = {report.hook_score}")


class TestScriptGuard(unittest.TestCase):
    """Guard tests"""

    def test_validate(self):
        guard = ScriptGuard()
        result = guard.validate({
            "text": "A positive story about growth and success",
            "title": "Test",
            "platform": "douyin",
        })
        self.assertTrue(result.passed)
        print("OK: Guard passed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
