# research_pdf_report.py
from fpdf import FPDF
import os
import re
from agents.research_coordinator_agent import ResearchCoordinatorAgent


class StyledPDF(FPDF):
    def header(self):
        # Add top banner
        self.set_fill_color(33, 37, 41)  # Dark gray background
        self.rect(0, 0, 210, 20, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", 'B', 14)
        self.cell(0, 10, "AI Research Report", 0, 1, 'C')
        self.ln(5)

    def footer(self):
        # Footer page number
        self.set_y(-15)
        self.set_font("Helvetica", 'I', 9)
        self.set_text_color(128)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, 'C')


class PDFReportGenerator:
    def __init__(self, report, output_file="reports/Research_Report.pdf"):
        self.report = report
        self.output_file = output_file
        self.pdf = StyledPDF()
        # Set proper margins to ensure enough horizontal space
        self.pdf.set_margins(left=15, top=25, right=15)
        self.pdf.set_auto_page_break(auto=True, margin=20)

    def sanitize_text(self, text, max_len=2500):
        """Ensure safe, readable content that won't break PDF rendering."""
        if text is None or (isinstance(text, str) and not text.strip()):
            return "No content available."

        text = str(text)
        
        # Remove/replace Unicode characters that FPDF can't handle
        try:
            # Try to encode as latin-1, which FPDF supports
            text = text.encode('latin-1', 'ignore').decode('latin-1')
        except:
            # Fallback to ASCII if latin-1 fails
            text = text.encode('ascii', 'ignore').decode('ascii')
        
        # Remove zero-width and invisible characters
        text = text.replace('\u200b', '')
        text = text.replace('\ufeff', '')
        text = text.replace('\x00', '')
        
        # Replace problematic Unicode characters
        replacements = {
            '\u2013': '-',
            '\u2014': '--',
            '\u2018': "'",
            '\u2019': "'",
            '\u201c': '"',
            '\u201d': '"',
            '\u2026': '...',
            '\u2022': '*',  # bullet point
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Replace tabs and carriage returns
        text = text.replace("\t", "    ").replace("\r", "")
        
        # Reduce multiple spaces/newlines
        text = re.sub(r" +", " ", text)
        text = re.sub(r"\n\n+", "\n\n", text)
        
        # Remove any remaining non-printable characters except newlines
        text = ''.join(char for char in text if char.isprintable() or char == '\n')
        
        # Break very long words/URLs to prevent rendering issues
        words = text.split()
        processed_words = []
        for word in words:
            if len(word) > 50:
                # Insert spaces every 50 characters for very long words
                word = ' '.join([word[i:i+50] for i in range(0, len(word), 50)])
            processed_words.append(word)
        text = ' '.join(processed_words)
        
        # Truncate if too long
        if len(text) > max_len:
            text = text[:max_len] + "..."
        
        # Final check - ensure it's not empty
        if not text or text.isspace():
            return "No content available."
            
        return text

    def add_title_page(self, title, subtitle):
        self.pdf.add_page()
        self.pdf.set_text_color(0, 51, 102)
        self.pdf.set_font("Helvetica", 'B', 20)
        
        # Use cell instead of multi_cell for title to avoid issues
        safe_title = self.sanitize_text(title, max_len=100)
        self.pdf.cell(0, 60, safe_title, ln=True, align='C')
        
        self.pdf.set_font("Helvetica", 'I', 14)
        self.pdf.set_text_color(80)
        safe_subtitle = self.sanitize_text(subtitle, max_len=150)
        self.pdf.cell(0, 10, safe_subtitle, ln=True, align='C')
        self.pdf.ln(20)

    def add_section(self, heading, content):
        """Safely adds a section with multiple fallback mechanisms."""
        try:
            self.pdf.set_text_color(0, 0, 0)
            self.pdf.set_fill_color(240, 240, 240)
            self.pdf.set_font("Helvetica", 'B', 13)
            
            # Sanitize heading
            safe_heading = self.sanitize_text(heading, max_len=200)
            self.pdf.cell(0, 8, safe_heading, ln=True, fill=True)
            self.pdf.ln(2)

            self.pdf.set_font("Helvetica", '', 11)
            self.pdf.set_text_color(30, 30, 30)

            # Sanitize content
            safe_content = self.sanitize_text(content)

            # Try to add content with multiple fallback strategies
            try:
                # Strategy 1: Direct multi_cell
                self.pdf.multi_cell(0, 6, safe_content)
            except Exception as e1:
                print(f"Warning: multi_cell failed for '{heading}': {e1}")
                try:
                    # Strategy 2: Split into smaller chunks
                    chunk_size = 500
                    chunks = [safe_content[i:i+chunk_size] for i in range(0, len(safe_content), chunk_size)]
                    for chunk in chunks:
                        self.pdf.multi_cell(0, 6, chunk)
                except Exception as e2:
                    print(f"Warning: chunked multi_cell failed for '{heading}': {e2}")
                    try:
                        # Strategy 3: Use cell() for line-by-line
                        lines = safe_content.split('\n')
                        for line in lines[:20]:  # Limit to 20 lines
                            if line.strip():
                                # Truncate line if too long
                                if len(line) > 100:
                                    line = line[:100] + "..."
                                self.pdf.cell(0, 6, line, ln=True)
                    except Exception as e3:
                        print(f"Warning: All rendering strategies failed for '{heading}': {e3}")
                        # Strategy 4: Simple fallback message
                        self.pdf.cell(0, 6, "[Content could not be rendered]", ln=True)
            
            self.pdf.ln(6)
            
        except Exception as e:
            print(f"Error in add_section for '{heading}': {e}")
            # Skip this section if all else fails

    def add_chart(self, chart_path, caption=""):
        if os.path.exists(chart_path):
            try:
                # Check if we need a new page
                if self.pdf.get_y() > 220:
                    self.pdf.add_page()
                
                self.pdf.image(chart_path, w=170)
                if caption:
                    self.pdf.set_font("Helvetica", 'I', 10)
                    self.pdf.set_text_color(100)
                    safe_caption = self.sanitize_text(caption, max_len=200)
                    try:
                        self.pdf.multi_cell(0, 5, safe_caption)
                    except:
                        self.pdf.cell(0, 5, safe_caption[:50] + "...", ln=True)
                self.pdf.ln(8)
            except Exception as e:
                print(f"Warning: Could not add chart '{chart_path}': {e}")

    def generate(self):
        try:
            os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
            
            self.add_title_page(
                "Automated AI Research Report",
                "Compiled using Multi-Agent MCP System"
            )

            # Executive Summary
            exec_summary = self.report.get("Executive_Summary", "No executive summary available.")
            if not exec_summary or str(exec_summary).strip() == "":
                exec_summary = "No executive summary available."
            self.add_section("Executive Summary", exec_summary)

            # Keywords
            keywords_list = self.report.get("Keywords", [])
            if keywords_list:
                keywords = ", ".join(str(k) for k in keywords_list if k)
            else:
                keywords = "No keywords extracted."
            self.add_section("Keywords", keywords)

            # Content by Keyword
            content_by_kw = self.report.get("Content_By_Keyword", {})
            if content_by_kw:
                for kw, doc in content_by_kw.items():
                    if doc:
                        self.add_section(f"Content for '{kw}'", doc)
            else:
                self.add_section("Content by Keyword", "No content available.")

            # Semantic Highlights
            semantic_highlights = self.report.get("Semantic_Highlights", [])
            if semantic_highlights:
                try:
                    semantic_data = "\n".join(
                        str(item)
                        for sublist in semantic_highlights
                        for item in (sublist if isinstance(sublist, list) else [sublist])
                        if item
                    )
                except:
                    semantic_data = str(semantic_highlights)
            else:
                semantic_data = "No highlights found."
            self.add_section("Semantic Highlights", semantic_data)

            # Deep Analysis
            deep_analysis = self.report.get("Deep_Analysis", {})
            if deep_analysis:
                deep = str(deep_analysis)
            else:
                deep = "No deep analysis data available."
            self.add_section("Deep Analysis", deep)

            # Visualizations
            visuals = self.report.get("Visualizations", {})
            if visuals:
                for caption, path in visuals.items():
                    self.add_chart(path, caption)
            else:
                self.add_section("Visualizations", "No charts or visual data generated.")

            self.pdf.output(self.output_file)
            print(f"\n✅ Report successfully generated at: {self.output_file}")
            
        except Exception as e:
            print(f"\n❌ Error generating PDF: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    query = "Generate a summary comparing AI retrieval models and their recent progress."
    
    print("Starting research coordinator...")
    agent = ResearchCoordinatorAgent(max_workers=5)
    report = agent.handle_query(query)

    print("\nGenerating PDF report...")
    pdf_generator = PDFReportGenerator(report)
    pdf_generator.generate()