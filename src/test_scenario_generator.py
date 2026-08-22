from scenario_generator import generate_scenarios

agent_description = "A customer support agent that can look up orders, issue refunds, and answer FAQs."
tools = ["lookup_order", "issue_refund", "search_faq"]

results = generate_scenarios(agent_description, tools)

for category, scenarios in results.items():
    print(f"\n=== {category.upper()} ({len(scenarios)}) ===")
    for s in scenarios[:2]:  # just print first 2 per category as a sanity check
        print(f"- [{s['id']}] {s['input']}")