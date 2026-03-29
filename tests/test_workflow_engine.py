#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workflow Engine Test
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.step_workflow_engine import (
    StepWorkflowEngine, StepType, StepStatus
)

def test_workflow_engine():
    print('='*60)
    print('Step Workflow Engine Test')
    print('='*60)
    print()
    
    # Initialize engine
    print('1. Initializing engine...')
    engine = StepWorkflowEngine(storage_path='data/test_workflow')
    print('   OK')
    print()
    
    # Create step
    print('2. Creating Step1...')
    step1 = engine.create_step(
        step_type=StepType.STEP1_DIAG,
        project_id='test-001',
        input_data={'requirement': 'Learn Python'},
        created_by='test_user'
    )
    print(f'   Created: {step1.id}')
    print(f'   Status: {step1.status.value}')
    print()
    
    # Start step
    print('3. Starting step...')
    engine.start_step(step1.id)
    status = engine.get_step_status(step1.id)
    print(f'   Status: {status["status"]}')
    print(f'   Progress: {status["progress"]}%')
    print()
    
    # Complete AI work
    print('4. Completing AI work...')
    engine.complete_ai_work(step1.id, {'report': 'Test output'})
    status = engine.get_step_status(step1.id)
    print(f'   Status: {status["status"]}')
    print(f'   Next action: {status["next_action"]["action"] if status["next_action"] else "None"}')
    print()
    
    # Approve
    print('5. Reviewing step...')
    engine.submit_for_review(step1.id)
    engine.review_step(step1.id, decision='approve')
    status = engine.get_step_status(step1.id)
    print(f'   Status: {status["status"]}')
    print()
    
    # Archive
    print('6. Archiving step...')
    engine.archive_step(step1.id)
    print('   Archived')
    print()
    
    print('='*60)
    print('All tests passed!')
    print('='*60)

if __name__ == '__main__':
    test_workflow_engine()
