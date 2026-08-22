from attack_generator import generate_attacks

agent_description = "A customer support agent that can look up orders, issue refunds, and answer FAQs."

attacks = generate_attacks(agent_description)

print(f"\nGenerated {len(attacks)} attacks:\n")
for a in attacks:
    print(f"[{a['id']}] {a['type']} ({a['severity']})")
    print(f"    Input: {a['input']}")
    print(f"    Expected defense: {a['expected_defense']}\n")