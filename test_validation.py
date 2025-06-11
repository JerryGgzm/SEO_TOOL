#!/usr/bin/env python3

"""Quick validation test"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.review_optimization.models import ReviewDecisionRequest, ReviewDecision

def test_validation():
    print("Testing ReviewDecisionRequest validation...")
    
    # Test 1: Should work fine with APPROVE
    try:
        request1 = ReviewDecisionRequest(
            decision=ReviewDecision.APPROVE,
            feedback="Good content"
        )
        print("✅ APPROVE decision works fine")
    except Exception as e:
        print(f"❌ APPROVE failed: {e}")
    
    # Test 2: Should work with EDIT_AND_APPROVE when edited_content provided
    try:
        request2 = ReviewDecisionRequest(
            decision=ReviewDecision.EDIT_AND_APPROVE,
            edited_content="Edited content here",
            feedback="Minor edits needed"
        )
        print("✅ EDIT_AND_APPROVE with content works fine")
    except Exception as e:
        print(f"❌ EDIT_AND_APPROVE with content failed: {e}")
    
    # Test 3: Should FAIL with validation error when EDIT_AND_APPROVE without edited_content
    try:
        request3 = ReviewDecisionRequest(
            decision=ReviewDecision.EDIT_AND_APPROVE,
            feedback="Minor edits needed"
            # edited_content is missing
        )
        print("❌ EDIT_AND_APPROVE without content should have failed!")
    except ValueError as e:
        if "edited_content is required" in str(e):
            print("✅ Validation correctly caught missing edited_content")
        else:
            print(f"❌ Wrong error message: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_validation() 