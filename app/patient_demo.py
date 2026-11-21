#!/usr/bin/env python3
"""Terminal demonstration of the hospital reception/intake state machine.
DEMO ONLY. No medical inference; no personal records are stored.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from typing import NamedTuple

LOCATIONS = Path(__file__).resolve().parents[1] / 'config' / 'locations.json'

class RoutingDecision(NamedTuple):
    destination: str | None
    reason: str
    urgent: bool = False

# Conservative wording; these are flags for a human, NOT medical diagnosis.
URGENT = (
    'chest pain', 'difficulty breathing', 'cant breathe', "can't breathe",
    'severe bleeding', 'unconscious', 'fainted', 'collapse', 'stroke',
    'seizure', 'severe shortness of breath'
)
ORTHO = ('knee', 'joint', 'bone', 'fracture', 'sprain', 'back pain',
         'wrist', 'ankle', 'shoulder pain', 'orthopedic', 'orthopaedic')
GENERAL = ('fever', 'cough', 'cold', 'headache', 'stomach', 'vomit',
           'tired', 'fatigue', 'general checkup', 'routine checkup', 'rash')
LAB = ('blood test', 'urine test', 'sample collection', 'laboratory', 'lab test')

def reason_to_destination(reason: str, has_lab_referral: bool = False) -> RoutingDecision:
    text = re.sub(r'\s+', ' ', reason.lower().strip())
    if any(term in text for term in URGENT):
        return RoutingDecision(None, 'Possible urgent concern: call a human clinician immediately.', True)
    if any(term in text for term in ORTHO):
        return RoutingDecision('orthopedics', 'Possible musculoskeletal concern; staff must confirm department.')
    if any(term in text for term in GENERAL):
        return RoutingDecision('general_medicine', 'General medical concern; staff/patient must confirm department.')
    if any(term in text for term in LAB):
        if has_lab_referral:
            return RoutingDecision('laboratory', 'Patient has a laboratory referral; confirm the requested test with staff.')
        return RoutingDecision('nurse_station', 'Lab requested without confirmed referral; ask staff first.')
    return RoutingDecision('nurse_station', 'Unclear destination; ask nurse/reception staff to direct the patient.')

def prompt(question: str, default: str = '') -> str:
    response = input(question).strip()
    return response or default

def main() -> None:
    parser = argparse.ArgumentParser(description='Hospital intake/routing DEMO (fictional data only)')
    parser.add_argument('--example', action='store_true', help='run noninteractive fictional patient example')
    parser.add_argument('--reason', help='test routing with fictional free-text reason')
    args = parser.parse_args()
    loc = json.loads(LOCATIONS.read_text())['destinations']
    print('\n=== NAV CARE HOSPITAL RECEPTION | SIMULATION ONLY ===')
    print('No real patient information is required or stored. Simulated readings are NOT medical measurements.\n')
    if args.example or args.reason:
        name = 'Demo Patient'
        age = '30'
        reason = args.reason or 'I have knee pain'
        referral = False
    else:
        ok = prompt('Use fictional information only. Continue? [y/N]: ').lower()
        if ok != 'y':
            print('Demo cancelled.')
            return
        name = prompt('Fictional patient name [Demo Patient]: ', 'Demo Patient')
        age = prompt('Fictional age [30]: ', '30')
        reason = prompt('What is the reason for your visit? ')
        referral = prompt('Do you have a laboratory referral? [y/N]: ').lower() == 'y'
    print(f'\nPatient: {name} | Age: {age} (DEMO INPUT)')
    print('Pulse: 76 bpm | SpO2: 98% | BP: 120/80 mmHg (SIMULATED EXAMPLE VALUES ONLY)')
    decision = reason_to_destination(reason, referral)
    print(f'Stated concern: {reason}')
    print(f'Routing note: {decision.reason}')
    if decision.urgent:
        print('STOP routine process. Alert the nearby nurse/reception staff immediately.')
        print('Do not navigate away or delay emergency medical evaluation.')
        return
    dest = decision.destination
    if not dest:
        print('No route selected.')
        return
    print(f'Suggested destination: {loc[dest]["label"]}')
    if not (args.example or args.reason):
        print('IMPORTANT: Staff should confirm department based on hospital protocol.')
        ok = prompt('Has the patient/staff confirmed this destination? [y/N]: ').lower()
        if ok != 'y':
            print('Routine escort cancelled; request staff assistance.')
            return
    xyz = loc[dest]
    print(f'ROUTE READY -> {loc[dest]["label"]} at (x={xyz["x"]}, y={xyz["y"]}, yaw={xyz["yaw_deg"]}deg)')
    print(f'After Nav2 + SLAM are running, command: python3 app/nav2_escort.py {dest}')
    print('NOTE: This demo does not move the robot by itself. Escort requires navigation + human monitoring.')

if __name__ == '__main__':
    main()
