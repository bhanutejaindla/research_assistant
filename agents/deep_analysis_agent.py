from tools.comparative_analysis_tool import ComparativeAnalysisTool
from tools.trend_analysis_tool import TrendAnalysisTool
from tools.causal_reasoning_tool import CausalReasoningTool
from tools.statistical_analysis_tool import StatisticalAnalysisTool

class DeepAnalysisAgent:
    def __init__(self):
        self.comparative_tool = ComparativeAnalysisTool()
        self.trend_tool = TrendAnalysisTool()
        self.causal_tool = CausalReasoningTool()
        self.stat_tool = StatisticalAnalysisTool()

    def analyze(self, documents):
        """
        Run all deep analysis tools on the provided documents.
        Input: documents - list of strings (document texts)
        Output: dictionary with all analysis results
        """
        output = {}

        # 1. Comparative Analysis
        output['comparative_analysis'] = self.comparative_tool.run(documents=documents)

        # 2. Trend Analysis
        output['trend_analysis'] = self.trend_tool.run(documents=documents)

        # 3. Causal Reasoning
        output['causal_analysis'] = self.causal_tool.run(documents=documents)

        # 4. Statistical Analysis
        output['statistical_analysis'] = self.stat_tool.run(documents=documents)

        return output

if __name__ == "__main__":
    # Test the agent
    documents = [
        "AI is advancing rapidly. Recent research focuses on RAG because it improves retrieval.",
        "Augmented AI models are trending. Many papers report improvements because of new architectures."
    ]
    agent = DeepAnalysisAgent()
    results = agent.analyze(documents)
    print("--- Deep Analysis Results ---")
    for key, value in results.items():
        print(f"{key}: {value}\n")
