"""
Experiment runner - core execution engine.
"""
import asyncio
import json
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

from .models import OceanProfile
from .input_systems import get_input_system
from .instruments import get_instrument
from .clients import create_client


@dataclass
class RunnerConfig:
    """Configuration for experiment runner."""
    api_keys: dict
    retry_attempts: int = 3
    retry_delay: float = 5.0
    longitudinal: bool = False  # accumulate conversation history within test case


class ExperimentRunner:
    """Runs experiments from database queue."""
    
    def __init__(self, config: RunnerConfig):
        self.config = config
        self._clients = {}
    
    def _get_client(self, provider: str):
        if provider not in self._clients:
            api_key = self.config.api_keys.get(provider)
            if not api_key:
                raise ValueError(f"No API key for {provider}")
            self._clients[provider] = create_client(provider, api_key)
        return self._clients[provider]
    
    async def run_test_case(self, test_case: Dict[str, Any]) -> bool:
        """Run a single test case."""
        from . import db
        
        try:
            provider = test_case['provider']
            instrument_name = test_case['instrument']
            input_system_name = test_case['input_system']
            
            client = self._get_client(provider)
            instrument = get_instrument(instrument_name)
            input_system = get_input_system(input_system_name)
            
            profile = OceanProfile(
                test_case['O'],
                test_case['C'],
                test_case['E'],
                test_case['A'],
                test_case['N']
            )
            
            # Update status
            db.update_test_case_status(test_case['id'], 'running')
            
            mode_label = "LONGITUDINAL" if self.config.longitudinal else "INDEPENDENT"
            print(f"  Running {provider}/{input_system_name}/{instrument_name} - {profile} [{mode_label}]")

            # Build system prompt once
            personality_text = input_system.build_preamble(profile)
            scale_instructions = instrument.get_scale_instructions()
            system_prompt = f"{personality_text}\n\nBased on these personality traits, {scale_instructions}"

            responses = {}
            messages = []  # conversation history for longitudinal mode
            
            for seq_position, question in enumerate(instrument.get_questions(), start=1):
                user_msg = f'Statement: "{question.text}"\n\nRespond with ONLY a single number (1, 2, 3, 4, or 5).'
                
                if self.config.longitudinal:
                    # Longitudinal: accumulate conversation history
                    messages.append({"role": "user", "content": user_msg})
                    result = await client.complete_with_messages(
                        messages,
                        system=system_prompt,
                        max_tokens=10,
                        temperature=0.3
                    )
                    # Add assistant response to history for next iteration
                    messages.append({"role": "assistant", "content": result.text})
                else:
                    # Independent: fresh prompt each time (original behavior)
                    prompt = f"{system_prompt}\n\n{user_msg}"
                    result = await client.complete(prompt, max_tokens=10, temperature=0.3)
                
                score = client._parse_digit(result.text)
                responses[question.number] = score
                
                # Store response with sequence metadata
                db.insert_response({
                    'test_case_id': test_case['id'],
                    'question_number': question.number,
                    'question_text': question.text,
                    'factor': question.factor,
                    'is_reversed': question.is_reversed,
                    'raw_response': result.text,
                    'parsed_score': score,
                    'response_time_ms': result.latency_ms,
                    'sequence_position': seq_position if self.config.longitudinal else None,
                    'context_tokens': result.prompt_tokens if self.config.longitudinal else None,
                })
                
                factor_short = question.factor[0].upper()
                rev = "R" if question.is_reversed else ""
                ctx = f" ctx={result.prompt_tokens}" if self.config.longitudinal and result.prompt_tokens else ""
                print(f"    Q{question.number}({factor_short}{rev}): {score}{ctx}")
            
            # Calculate and store result
            result = instrument.calculate_scores(responses)
            db.insert_result({
                'test_case_id': test_case['id'],
                'total_score': result.total_score,
                'factor_scores': json.dumps(result.factor_scores),
                'questions_answered': result.questions_answered,
                'questions_total': result.questions_total,
            })
            
            db.update_test_case_status(test_case['id'], 'complete')
            print(f"  ✓ Complete: Total={result.total_score:.1f}")
            return True
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            db.update_test_case_status(test_case['id'], 'error', str(e))
            return False
    
    async def run_experiment(self, experiment_id: int) -> Dict:
        """Run all pending test cases for an experiment."""
        from . import db
        
        pending = db.get_pending_test_cases_for_experiment(experiment_id)
        
        if not pending:
            print(f"No pending test cases for experiment {experiment_id}")
            return {'total': 0, 'success': 0, 'failed': 0}
        
        # Mark experiment as started
        db.start_experiment(experiment_id)
        
        mode = "LONGITUDINAL" if self.config.longitudinal else "INDEPENDENT"
        print(f"Running {len(pending)} test cases in {mode} mode...")
        
        success = 0
        failed = 0
        
        for i, test_case in enumerate(pending, 1):
            print(f"\n[{i}/{len(pending)}] Test case {test_case['id']}")
            if await self.run_test_case(test_case):
                success += 1
            else:
                failed += 1
        
        # Mark experiment as complete
        db.complete_experiment(experiment_id)
        
        print(f"\nComplete: {success} success, {failed} failed")
        return {'total': len(pending), 'success': success, 'failed': failed}
    
    async def run_pending(self, limit: Optional[int] = None) -> Dict:
        """Run all pending test cases."""
        from . import db
        
        pending = db.get_pending_test_cases(limit)
        
        if not pending:
            print("No pending test cases")
            return {'total': 0, 'success': 0, 'failed': 0}
        
        mode = "LONGITUDINAL" if self.config.longitudinal else "INDEPENDENT"
        print(f"Running {len(pending)} test cases in {mode} mode...")
        
        success = 0
        failed = 0
        
        for i, test_case in enumerate(pending, 1):
            print(f"\n[{i}/{len(pending)}] Test case {test_case['id']}")
            if await self.run_test_case(test_case):
                success += 1
            else:
                failed += 1
        
        print(f"\nComplete: {success} success, {failed} failed")
        return {'total': len(pending), 'success': success, 'failed': failed}


async def run_quick_test(config: RunnerConfig, provider: str = 'deepseek'):
    """Quick integration test - single profile, single instrument."""
    from .instruments import LevensonInstrument
    from .input_systems import OceanDirectSystem
    
    instrument = LevensonInstrument()
    input_system = OceanDirectSystem()
    
    api_key = config.api_keys.get(provider)
    if not api_key:
        print(f"ERROR: No API key for {provider}")
        return
    
    client = create_client(provider, api_key)
    profile = OceanProfile(50, 25, 50, 0, 50)
    
    mode = "LONGITUDINAL" if config.longitudinal else "INDEPENDENT"
    print(f"Quick test: {provider} + Levenson + OCEAN Direct [{mode}]")
    print(f"Profile: {profile}")
    print()
    
    # Build system prompt once
    personality_text = input_system.build_preamble(profile)
    scale_instructions = instrument.get_scale_instructions()
    system_prompt = f"{personality_text}\n\nBased on these personality traits, {scale_instructions}"
    
    responses = {}
    messages = []
    
    for question in instrument.get_questions():
        user_msg = f'Statement: "{question.text}"\n\nRespond with ONLY a single number (1, 2, 3, 4, or 5).'
        
        if config.longitudinal:
            messages.append({"role": "user", "content": user_msg})
            result = await client.complete_with_messages(
                messages,
                system=system_prompt,
                max_tokens=10,
                temperature=0.3
            )
            messages.append({"role": "assistant", "content": result.text})
        else:
            prompt = f"{system_prompt}\n\n{user_msg}"
            result = await client.complete(prompt, max_tokens=10, temperature=0.3)
        
        score = client._parse_digit(result.text)
        responses[question.number] = score
        
        factor_short = question.factor[0].upper()
        rev = "R" if question.is_reversed else ""
        ctx = f" ctx={result.prompt_tokens}" if config.longitudinal and result.prompt_tokens else ""
        print(f"Q{question.number}({factor_short}{rev}): {score} [{result.text.strip()}]{ctx}")
    
    result = instrument.calculate_scores(responses)
    print()
    print(f"Total: {result.total_score:.1f}")
    print(f"Primary: {result.factor_scores['primary']:.1f}")
    print(f"Secondary: {result.factor_scores['secondary']:.1f}")
    
    return result