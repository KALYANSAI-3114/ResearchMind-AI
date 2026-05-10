"""
Summary Agent
Generates summaries of research papers
"""

import os
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()


class SummaryAgent:
    """Generate paper summaries using LLMs."""
    
    def __init__(self, use_openai: bool = False):
        """
        Initialize the summary agent.
        
        Args:
            use_openai: Whether to use OpenAI API (default: False for offline)
        """
        self.use_openai = use_openai
        
        if use_openai:
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        else:
            # For offline/open-source LLMs, would integrate with Ollama or similar
            self.client = None
    
    def generate_summary(self, paper_text: str) -> Dict[str, str]:
        """
        Generate a structured summary of a paper.
        
        Args:
            paper_text: Full text of the paper
        
        Returns:
            Dictionary with objective, methodology, results, limitations
        """
        if not paper_text or len(paper_text) < 100:
            raise ValueError("Paper text too short for summarization")
        
        # Truncate to first 2000 tokens to avoid API limits
        paper_text = paper_text[:8000]
        
        prompt = f"""
        Analyze the following research paper and provide a structured summary.
        
        PAPER:
        {paper_text}
        
        Provide your response in this format:
        
        OBJECTIVE:
        [What is the main objective of this paper?]
        
        METHODOLOGY:
        [What methods/approach does the paper use?]
        
        RESULTS:
        [What are the key findings/results?]
        
        LIMITATIONS:
        [What are the acknowledged limitations?]
        
        KEY CONTRIBUTIONS:
        [What is novel/important about this work?]
        """
        
        if self.use_openai and self.client:
            return self._summarize_with_openai(prompt)
        else:
            return self._summarize_with_extraction(paper_text)
    
    def _summarize_with_openai(self, prompt: str) -> Dict[str, str]:
        """
        Use OpenAI API for summarization.
        
        Args:
            prompt: Summary prompt
        
        Returns:
            Structured summary
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=1500
            )
            
            summary_text = response.choices[0].message.content
            return self._parse_summary(summary_text)
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def _summarize_with_extraction(self, paper_text: str) -> Dict[str, str]:
        """
        Extract summary from paper text without API calls.
        Uses text extraction heuristics.
        
        Args:
            paper_text: Full paper text
        
        Returns:
            Structured summary
        """
        # Extract abstract if available
        abstract = self._extract_abstract(paper_text)
        
        # Extract introduction
        introduction = self._extract_section(paper_text, "introduction|background")
        
        # Extract methodology
        methodology = self._extract_section(paper_text, "methodology|method|approach|proposed|algorithm|framework")
        
        # Extract results
        results = self._extract_section(paper_text, "results|findings|experiment|evaluation|performance|outcomes")
        
        # Extract conclusions
        conclusions = self._extract_section(paper_text, "conclusion|conclusions|discussion|future")
        
        # Extract limitations (try harder)
        limitations = self._extract_section(paper_text, "limitations|limitations and future|challenges|drawback")
        if not limitations or "See paper" in limitations:
            limitations = self._extract_from_discussion(paper_text)
        
        # Build comprehensive summary with better content
        summary = {
            "objective": (abstract[:1500] if abstract else introduction[:1500] if introduction else paper_text[:1500]),
            "methodology": (methodology[:2000] if methodology else self._infer_methodology(paper_text)),
            "results": (results[:2000] if results else self._infer_results(paper_text)),
            "limitations": (limitations[:1000] if limitations else self._infer_limitations(paper_text)),
            "key_contributions": self._extract_key_points(abstract, paper_text)
        }
        
        # Remove any truly empty values but keep extraction results
        for key in summary:
            if not summary[key]:
                summary[key] = self._generate_fallback(paper_text, key)
        
        return summary
    
    def _extract_abstract(self, text: str) -> str:
        """Extract abstract from paper."""
        import re
        
        # Look for abstract section
        abstract_match = re.search(
            r'(?:abstract|summary)\s*(?:\n|:)(.*?)(?:\n\n|\nintroduction)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if abstract_match:
            return abstract_match.group(1).strip()[:1000]
        
        # Return first paragraph if no abstract found
        return text.split('\n\n')[0][:1000]
    
    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a section from paper."""
        import re
        
        pattern = rf'(?:{section_name})\s*(?:\n|:)(.*?)(?:\n\n|\n[A-Z]{{2,}}|$)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            return match.group(1).strip()[:1000]
        
        return ""
    
    def _extract_from_discussion(self, text: str) -> str:
        """Extract limitations from discussion section."""
        import re
        
        # Try to find discussion section
        discussion = self._extract_section(text, "discussion")
        if discussion:
            # Look for limitation keywords in discussion
            limitation_keywords = ["limit", "challenge", "future", "open", "weakness", "drawback"]
            sentences = discussion.split('.')
            limitations = [s.strip() for s in sentences if any(kw in s.lower() for kw in limitation_keywords)]
            return '. '.join(limitations[:3]) + '.' if limitations else discussion[:300]
        
        return ""
    
    def _infer_limitations(self, text: str) -> str:
        """Infer limitations from the paper text."""
        import re
        
        # Common limitation indicators
        limitation_phrases = [
            r'(?:limited|scope|future work|open question|challenge|drawback)',
            r'(?:not addressed|beyond scope|leave for future)',
            r'(?:computational cost|scalability|efficiency)',
            r'(?:dataset limitation|data constraint)'
        ]
        
        for phrase in limitation_phrases:
            matches = re.finditer(phrase, text, re.IGNORECASE)
            for match in matches:
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 200)
                context = text[start:end].strip()
                if context:
                    return context
        
        return ""
    
    def _infer_methodology(self, text: str) -> str:
        """Infer methodology when not explicitly found."""
        import re
        
        # Look for algorithm or approach descriptions
        patterns = [
            r'propose[d]?\s+(?:a\s+)?([^.]+)',
            r'(?:algorithm|framework|approach).*?(?:uses?|employs?)\s+([^.]+)',
            r'(?:method|technique)\s+(?:is\s+)?(?:based on|uses?|employs?)\s+([^.]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                if len(content) > 50:
                    return content[:1000]
        
        # Return paper intro which usually describes the approach
        return text[:800]
    
    def _infer_results(self, text: str) -> str:
        """Infer results when not explicitly found."""
        import re
        
        # Look for achievement/performance descriptions
        patterns = [
            r'(?:achieve|obtain|show|demonstrate)\s+([^.!?]+[.!?])',
            r'(?:performance|accuracy|metric)\s+(?:of|is)\s+([^.!?]+[.!?])',
            r'(?:result|finding).*?(?:shows?|indicates?|demonstrates?)\s+([^.!?]+[.!?])',
        ]
        
        matches = []
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
                matches.append(match.group(1).strip())
        
        if matches:
            return ' '.join(matches[:3])[:1000]
        
        # Look for evaluation/experimental section
        eval_section = re.search(
            r'(?:evaluation|experiment|result)\s*(?:\n|:)(.*?)(?:\n\n|$)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if eval_section:
            return eval_section.group(1).strip()[:800]
        
        return ""
    
    def _extract_key_points(self, abstract: str, text: str) -> str:
        """Extract key contributions/points from paper."""
        import re
        
        # Combine abstract and first part of full text
        search_text = abstract if abstract else text[:1000]
        
        # Look for contribution statements
        contributions = []
        patterns = [
            r'(?:we\s+)?(?:propose|introduce|present|develop)\s+(?:a\s+)?([^.!?]+)',
            r'(?:novel|new|first|innovative|original)\s+([^.!?]+)',
            r'(?:our\s+)?(?:main\s+)?contribution.*?(?:is|:)?\s*([^.!?]+)',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, search_text, re.IGNORECASE | re.DOTALL):
                contribution = match.group(1).strip()
                if len(contribution) > 10 and contribution not in contributions:
                    contributions.append(contribution[:200])
        
        # Return top contributions
        if contributions:
            return '. '.join(contributions[:2]) + '.'
        
        # Fallback: key sentences from abstract
        sentences = search_text.split('.')
        key_sentences = [s.strip() for s in sentences if len(s.strip()) > 20][:2]
        if key_sentences:
            return '. '.join(key_sentences) + '.'
        
        return "Paper presents original research contributions to the field"
    
    def _generate_fallback(self, paper_text: str, section: str) -> str:
        """Generate context-aware fallback content for missing sections."""
        fallbacks = {
            "objective": "The paper addresses a specific research question or problem in its domain through systematic investigation.",
            "methodology": "The research employs a structured approach combining theoretical analysis with empirical methodology.",
            "results": "The study presents key findings and results that validate or advance the research objectives.",
            "limitations": "The work has specific scope boundaries and identifies areas for future research and improvement.",
            "key_contributions": "The paper makes original and significant contributions to advancing knowledge in the field."
        }
        
        return fallbacks.get(section, "Information available in the paper")
    
    def _parse_summary(self, summary_text: str) -> Dict[str, str]:
        """Parse LLM summary output into structured format."""
        sections = {
            "objective": "",
            "methodology": "",
            "results": "",
            "limitations": "",
            "key_contributions": ""
        }
        
        import re
        
        for key in sections.keys():
            pattern = rf'{key.upper()}:\s*(.*?)(?:\n\n|$)'
            match = re.search(pattern, summary_text, re.IGNORECASE | re.DOTALL)
            if match:
                sections[key] = match.group(1).strip()[:1500]  # Increased from 500 to 1500
        
        return sections


# Convenience function
def summarize_paper(paper_text: str, use_openai: bool = False) -> Dict[str, str]:
    """Quick function to summarize a paper."""
    agent = SummaryAgent(use_openai=use_openai)
    return agent.generate_summary(paper_text)
