#!/usr/bin/env python3
"""Bladerunner CLI"""

import asyncio
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def get_api_keys() -> dict:
    return {
        'claude': os.getenv('ANTHROPIC_API_KEY'),
        'openai': os.getenv('OPENAI_API_KEY'),
        'deepseek': os.getenv('DEEPSEEK_API_KEY'),
        'gemini': os.getenv('GEMINI_API_KEY'),
        'xai': os.getenv('XAI_API_KEY'),
    }


async def cmd_quick_test(args):
    import importlib
    folder = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
    runner_module = importlib.import_module(f'{folder}.runner')
    config = runner_module.RunnerConfig(
        api_keys=get_api_keys(),
        longitudinal=args.longitudinal
    )
    await runner_module.run_quick_test(config, provider=args.provider)


def cmd_create(args):
    from bladerunner_runner import db
    
    providers = args.providers.split(',') if args.providers else ['deepseek']
    instruments = args.instruments.split(',') if args.instruments else ['levenson']
    input_systems = args.input_systems.split(',') if args.input_systems else ['ocean_direct']
    profile_set = args.profile_set or '19_strategic'
    
    experiment_id = db.create_experiment(
        name=args.name,
        description=args.description,
        profile_set=profile_set,
        input_systems=input_systems,
        instruments=instruments,
        providers=providers,
        is_longitudinal=args.longitudinal,
    )
    
    status = db.get_experiment_status(experiment_id)
    
    print(f"Created experiment {experiment_id} (#{status['experiment_number']}): {args.name}")
    print(f"  Description: {args.description}")
    print(f"  Providers: {providers}")
    print(f"  Instruments: {instruments}")
    print(f"  Input systems: {input_systems}")
    print(f"  Profile set: {profile_set}")
    print(f"  Longitudinal: {args.longitudinal}")
    print(f"  Test cases: {status['total']}")


def cmd_status(args):
    from bladerunner_runner import db
    
    status = db.get_experiment_status(args.experiment)
    
    if not status:
        print(f"Experiment {args.experiment} not found.")
        return
    
    exp_num = status.get('experiment_number') or '?'
    longitudinal = 'Yes' if status.get('is_longitudinal') else 'No'
    
    print(f"Experiment {status['id']} (#{exp_num}): {status['name']}")
    print(f"  Status: {status['status']}")
    print(f"  Longitudinal: {longitudinal}")
    print(f"  Started: {status['started_at'] or 'Not started'}")
    print(f"  Completed: {status['completed_at'] or 'Not completed'}")
    print(f"  Total: {status['total']}")
    print(f"  Complete: {status['complete']}")
    print(f"  Failed: {status['failed']}")
    print(f"  Pending: {status['pending']}")
    print(f"  Running: {status['running']}")


async def cmd_run(args):
    from bladerunner_runner import db
    from bladerunner_runner.runner import RunnerConfig, ExperimentRunner
    
    config = RunnerConfig(
        api_keys=get_api_keys(),
        longitudinal=args.longitudinal
    )
    runner = ExperimentRunner(config)
    
    if args.experiment:
        await runner.run_experiment(args.experiment)
    else:
        await runner.run_pending(limit=args.limit)


def main():
    parser = argparse.ArgumentParser(description='Bladerunner CLI')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # quick-test
    qt = subparsers.add_parser('quick-test', help='Run quick integration test')
    qt.add_argument('--provider', default='deepseek', choices=['claude', 'openai', 'deepseek', 'gemini'])
    qt.add_argument('--longitudinal', action='store_true', help='Accumulate conversation history')
    
    # create
    cr = subparsers.add_parser('create', help='Create new experiment')
    cr.add_argument('--name', required=True, help='Experiment name')
    cr.add_argument('--description', required=True, help='Experiment description')
    cr.add_argument('--providers', help='Comma-separated providers')
    cr.add_argument('--instruments', help='Comma-separated instruments')
    cr.add_argument('--input-systems', dest='input_systems', help='Comma-separated input systems')
    cr.add_argument('--profile-set', dest='profile_set', help='Profile set name')
    cr.add_argument('--longitudinal', action='store_true', help='Mark as longitudinal experiment')
    
    # status
    st = subparsers.add_parser('status', help='Show experiment status')
    st.add_argument('experiment', type=int, help='Experiment ID')
    
    # run
    rn = subparsers.add_parser('run', help='Run pending test cases')
    rn.add_argument('--experiment', type=int, help='Run specific experiment')
    rn.add_argument('--limit', type=int, help='Max test cases')
    rn.add_argument('--longitudinal', action='store_true', help='Accumulate conversation history')
    
    args = parser.parse_args()
    
    if args.command == 'quick-test':
        asyncio.run(cmd_quick_test(args))
    elif args.command == 'create':
        cmd_create(args)
    elif args.command == 'status':
        cmd_status(args)
    elif args.command == 'run':
        asyncio.run(cmd_run(args))


if __name__ == '__main__':
    main()