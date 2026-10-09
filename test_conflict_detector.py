from conflict_detection.detector import (
    detect_conflict_signals,
)


test_messages = [
    "Come fight me.",
    "Wag kayong mag-away.",
    "Nag-away sila kahapon.",
    "Ayoko makipag-away.",
    "Hello everyone, let's play.",
    "Tigil na kayo.",
    "I am so angry at you.",
    "Stop fighting, guys.",
    "I don't want to fight with you.",
    "They fought yesterday, but everything is okay now.",
    "Ikaw talaga, tumahimik ka.",
    "Dili ko gusto makig-away.",
]


for message in test_messages:
    result = detect_conflict_signals(message)

    print(f"\nMessage: {message}")
    print(f"Signals: {result['signals']}")
    print(f"Assessment: {result['assessment']}")