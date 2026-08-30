import sys
sys.path.append('./backend')

from workflow import run_workflow

def test_financial_query():
    print("Initializing RAG Multi-Agent System...")
    
    # Example Complex Financial Query
    query = (
        "Calculate the PE ratio for Apple if its current stock price is $150 "
        "and EPS is $5. Also, search the Knowledge Graph for Apple's major subsidiaries."
    )
    
    print(f"\nUser Query: {query}\n")
    print("Routing through agents (QueryRefiner -> Researcher -> DocumentProcessor)...\n")
    
    try:
        # None is passed as data_retriever (assuming no user PDF uploaded for this test)
        response = run_workflow(query, None)
        print("--- FINAL AGENT RESPONSE ---")
        print(response)
        
    except Exception as e:
        print(f"Workflow failed: {e}")

if __name__ == "__main__":
    test_financial_query()
