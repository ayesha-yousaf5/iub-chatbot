#!/usr/bin/env python3
"""Test script to evaluate the IUB chatbot with various questions."""

import sys
from terminal_chat import ask_chatbot, answer_from_kb

# Test questions covering different categories
TEST_QUESTIONS = [
    # General admission questions
    "What is the admission process at IUB?",
    "What are the entry requirements for undergraduate programs?",
    "How much does it cost to study at IUB?",
    
    # Program-specific questions
    "What is the Computer Science program like?",
    "Tell me about the Business Administration program",
    "What programs does IUB offer?",
    
    # Campus and facilities
    "Where is IUB located?",
    "What facilities are available on campus?",
    "Does IUB have a library?",
    
    # Student life
    "Are there student clubs at IUB?",
    "What is student life like at IUB?",
    "Do you have scholarships available?",
    
    # Academic questions
    "What is the grading system?",
    "How many semesters per year?",
    "What is the academic calendar?",
    
    # Edge cases
    "xyz random nonsense question abc",
    "",  # Empty question
]


def test_chatbot():
    """Run tests on the chatbot."""
    print("=" * 70)
    print("IUB CHATBOT TEST SUITE")
    print("=" * 70)
    
    passed = 0
    failed = 0
    errors = []
    
    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"\n[TEST {i}/{len(TEST_QUESTIONS)}]")
        print(f"Question: {question if question else '(empty question)'}")
        print("-" * 70)
        
        try:
            # Try KB answer first
            last_question = ""
            result = answer_from_kb(question, last_question)
            
            # If KB doesn't have an answer, use RAG
            if result is None:
                result = ask_chatbot(question)
            
            # Check if we got a valid response
            if result and isinstance(result, dict):
                answer = result.get("answer", "")
                sources = result.get("sources", [])
                
                # Basic validation
                if answer and isinstance(answer, str):
                    print(f"✓ Answer: {answer[:200]}..." if len(answer) > 200 else f"✓ Answer: {answer}")
                    print(f"✓ Sources found: {len(sources)}")
                    
                    # Check for quality issues
                    if "sorry" in answer.lower() and len(sources) == 0:
                        print("⚠ WARNING: Fallback answer with no sources")
                    
                    passed += 1
                else:
                    print("✗ ERROR: No valid answer in response")
                    errors.append(f"Q{i}: Invalid answer format")
                    failed += 1
            else:
                print("✗ ERROR: Invalid response structure")
                errors.append(f"Q{i}: Invalid response structure")
                failed += 1
                
        except Exception as e:
            print(f"✗ EXCEPTION: {str(e)}")
            errors.append(f"Q{i}: {str(e)}")
            failed += 1
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {len(TEST_QUESTIONS)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/len(TEST_QUESTIONS))*100:.1f}%")
    
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✓ All tests completed without errors!")
    
    print("=" * 70)


if __name__ == "__main__":
    test_chatbot()
