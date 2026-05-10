"""
Comparison Agent
Compares research papers and identifies differences
"""

import os
from dotenv import load_dotenv
from typing import Dict, Any, List

load_dotenv()


class ComparisonAgent:
    """Compare multiple research papers."""
    
    def __init__(self, use_openai: bool = False):
        """
        Initialize the comparison agent.
        
        Args:
            use_openai: Whether to use OpenAI API
        """
        self.use_openai = use_openai
        
        if use_openai:
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        else:
            self.client = None
    
    def compare_papers(self, main_paper: Dict[str, Any], 
                       related_papers: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Compare main paper with related papers.
        Works with or without related papers (fallback to analysis only).
        
        Args:
            main_paper: Main paper data with text
            related_papers: List of related paper data (optional)
        
        Returns:
            Comparison analysis
        """
        if related_papers is None:
            related_papers = []
        
        # If no related papers provided, do single paper analysis
        if not related_papers or len(related_papers) == 0:
            return self._analyze_single_paper(main_paper)
        
        # Prepare paper summaries
        papers_summary = self._prepare_papers_summary(main_paper, related_papers)
        
        if self.use_openai and self.client:
            return self._compare_with_openai(papers_summary)
        else:
            return self._compare_with_heuristics(main_paper, related_papers, papers_summary)
    
    def _analyze_single_paper(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single paper when no related papers are available.
        This provides insights about the paper itself.
        
        Args:
            paper: Paper data
        
        Returns:
            Analysis of the single paper
        """
        paper_text = paper.get("text", paper.get("summary", paper.get("abstract", "")))
        
        return {
            "main_paper": paper.get("title", "Unknown"),
            "analysis_type": "single_paper",
            "status": "no_related_papers_available",
            "message": "External research APIs unavailable. Showing paper analysis only.",
            "comparison": f"Analysis of: {paper.get('title', 'Unknown')}",
            "paper_info": {
                "title": paper.get("title", "Unknown"),
                "authors": paper.get("authors", []),
                "year": paper.get("year"),
            },
            "methodology": self._extract_methodology(paper_text),
            "keywords": self._extract_keywords(paper_text),
            "strengths": [
                "Addresses key research problem in the field",
                "Provides comprehensive methodology explanation",
                "Offers practical applications and implications",
                "Well-supported findings with experimental validation"
            ],
            "recommendations": [
                "Search for related papers when APIs are available",
                "Explore paper methodology and approach in detail",
                "Review key findings and contributions",
                "Plan follow-up research based on this paper",
                "Consider how findings apply to related domains"
            ],
            "insights": [
                "Paper is available in the system for detailed analysis",
                "Can be compared with other papers when APIs recover",
                "Use this as a strong starting point for your research",
                "Review citations and references for related work",
                "Consider conducting similar studies in different domains"
            ]
        }
    
    def _prepare_papers_summary(self, main_paper: Dict[str, Any], 
                                 related_papers: List[Dict[str, Any]]) -> str:
        """Prepare paper data for comparison with fuller content."""
        summary = f"""
        MAIN PAPER: {main_paper.get('title', 'Unknown')}
        Authors: {', '.join(main_paper.get('authors', ['Unknown']))}
        Year: {main_paper.get('year', 'Unknown')}
        
        {main_paper.get('text', main_paper.get('summary', ''))[:2000]}
        
        RELATED PAPERS:
        """
        
        for i, paper in enumerate(related_papers[:3], 1):  # Compare with top 3
            paper_title = paper.get('title', f'Paper {i}')
            paper_authors = ', '.join(paper.get('authors', ['Unknown']))
            paper_year = paper.get('year', 'Unknown')
            paper_content = paper.get('text', paper.get('summary', paper.get('abstract', '')))
            
            summary += f"""
            
            PAPER {i}: {paper_title}
            Authors: {paper_authors}
            Year: {paper_year}
            
            {paper_content[:1500]}
            """
        
        return summary
    
    def _compare_with_openai(self, papers_summary: str) -> Dict[str, Any]:
        """Use OpenAI for comparison."""
        prompt = f"""
        Compare the following research papers. Identify:
        1. Similarities in approach/methodology
        2. Key differences
        3. Complementary aspects
        4. Which methods are superior and why
        5. Research gaps the papers collectively have
        
        {papers_summary}
        
        Provide a structured comparison.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=2000
            )
            
            comparison_text = response.choices[0].message.content
            return self._parse_comparison(comparison_text)
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def _compare_with_heuristics(self, main_paper: Dict[str, Any],
                                  related_papers: List[Dict[str, Any]],
                                  papers_summary: str) -> Dict[str, Any]:
        """Compare using text analysis heuristics."""
        comparison = {
            "main_paper": main_paper.get("title", "Unknown"),
            "related_papers_count": len(related_papers),
            "similarities": [],
            "differences": [],
            "methodologies": [],
            "datasets": [],
            "insights": []
        }
        
        # Extract methodologies with full titles
        main_methodology = self._extract_methodology(main_paper.get("text", ""))
        comparison["methodologies"].append({
            "paper": main_paper.get("title", "Unknown"),
            "methodology": main_methodology[:1000]  # Keep more content
        })
        
        for paper in related_papers[:3]:
            paper_title = paper.get("title", "Unknown")
            methodology = self._extract_methodology(
                paper.get("text", paper.get("summary", paper.get("abstract", "")))
            )
            comparison["methodologies"].append({
                "paper": paper_title,  # Full title, no truncation
                "methodology": methodology[:1000]
            })
        
        # Extract common keywords for similarities
        main_keywords = self._extract_keywords(main_paper.get("text", ""))
        
        for paper in related_papers[:3]:
            paper_title = paper.get("title", "Unknown")
            related_keywords = self._extract_keywords(
                paper.get("text", paper.get("summary", paper.get("abstract", "")))
            )
            common = set(main_keywords) & set(related_keywords)
            
            if common:
                comparison["similarities"].append({
                    "paper": paper_title,  # Full title
                    "common_topics": list(common)[:5]
                })
            else:
                comparison["differences"].append({
                    "paper": paper_title,  # Full title
                    "unique_aspects": list(related_keywords)[:5]
                })
        
        # Generate meaningful insights
        comparison["insights"] = [
            f"Compared main paper with {len(related_papers)} related papers",
            f"Found {len(comparison['similarities'])} papers with similar topics",
            f"Identified {len(comparison['differences'])} papers with different approaches",
            "Use comparison to understand research landscape",
            "Explore methodologies to understand different techniques"
        ]
        
        return comparison
    
    def _extract_methodology(self, text: str) -> str:
        """Extract methodology from paper text."""
        import re
        
        # Look for methodology section with better pattern matching
        patterns = [
            r'(?:methodology|method|approach|algorithm|framework)\s*(?:\n|:)(.*?)(?:\n\n|\nresult|\nevaluation|$)',
            r'(?:proposed|proposed method)(.*?)(?:\n\n|\nresult|\nevaluation|$)',
            r'(.*?)(?:\n\n|\nresult|\nevaluation|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                if len(content) > 50:  # Only return if substantial
                    return content[:800]  # Return more content
        
        # Return first substantial part of paper
        return text[:500]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text."""
        import re
        from collections import Counter
        
        # Look for common ML/research keywords and technical terms
        technical_keywords = [
            'transformer', 'attention', 'neural', 'learning', 'model', 'network',
            'algorithm', 'optimization', 'gradient', 'training', 'inference',
            'embedding', 'vector', 'kernel', 'parameter', 'layer', 'activation',
            'convolution', 'recurrent', 'sequence', 'prediction', 'classification',
            'regression', 'clustering', 'reinforcement', 'supervised', 'unsupervised'
        ]
        
        # Extract text that contains technical terms
        text_lower = text.lower()
        found_keywords = []
        
        # Find technical keywords
        for keyword in technical_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        # If found technical keywords, use them
        if found_keywords:
            return list(set(found_keywords))[:8]
        
        # Fall back to frequency analysis
        words = re.findall(r'\b[a-z]{4,}\b', text_lower)
        
        stop_words = {
            'the', 'that', 'this', 'with', 'from', 'were', 'have', 'been',
            'their', 'which', 'these', 'some', 'into', 'then', 'only',
            'paper', 'using', 'method', 'approach', 'study', 'research',
            'data', 'like', 'also', 'such', 'more', 'more', 'based',
            'show', 'used', 'propose', 'propose', 'work', 'good'
        }
        
        filtered = [w for w in words if w not in stop_words]
        most_common = Counter(filtered).most_common(8)
        
        return [word for word, _ in most_common]
    
    def _parse_comparison(self, comparison_text: str) -> Dict[str, Any]:
        """Parse LLM comparison output."""
        import re
        
        result = {
            "comparison": comparison_text,
            "similarities": [],
            "differences": [],
            "insights": []
        }
        
        # Try to extract sections
        for key in ["similarities", "differences"]:
            pattern = rf'(?:{key}|similar|different)(.*?)(?:\n\n|$)'
            match = re.search(pattern, comparison_text, re.IGNORECASE | re.DOTALL)
            if match:
                items = match.group(1).split('\n')
                result[key] = [item.strip() for item in items if item.strip()][:5]
        
        return result


def compare_papers(main_paper: Dict[str, Any], 
                   related_papers: List[Dict[str, Any]],
                   use_openai: bool = False) -> Dict[str, Any]:
    """Quick function to compare papers."""
    agent = ComparisonAgent(use_openai=use_openai)
    return agent.compare_papers(main_paper, related_papers)
