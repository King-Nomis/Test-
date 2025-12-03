import os
import re
import html
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from telegram.constants import ParseMode
import tempfile
import json
from typing import Dict, List, Optional, Tuple

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class JEEScorer:
    """JEE Main style scoring system"""
    
    @staticmethod
    def calculate_jee_score(correct_answers: int, wrong_answers: int, 
                           total_questions: int, positive_mark: float = 4.0,
                           negative_mark: float = 1.0) -> Dict:
        """
        Calculate JEE Main style score
        
        JEE Main 2024 Pattern:
        - Each correct answer: +4 marks
        - Each wrong answer: -1 mark (for MCQs)
        - Unanswered: 0 marks
        
        Returns: Dictionary with score details
        """
        # Calculate marks
        correct_marks = correct_answers * positive_mark
        wrong_deduction = wrong_answers * negative_mark
        net_score = correct_marks - wrong_deduction
        
        # Calculate percentage and percentile (simulated)
        max_possible = total_questions * positive_mark
        percentage = (net_score / max_possible * 100) if max_possible > 0 else 0
        
        # Simulated percentile (in real scenario, this would be based on rank)
        percentile = min(99.9, max(0, percentage + (100 - percentage) * 0.3))
        
        return {
            'correct_answers': correct_answers,
            'wrong_answers': wrong_answers,
            'unanswered': total_questions - (correct_answers + wrong_answers),
            'total_questions': total_questions,
            'positive_mark': positive_mark,
            'negative_mark': negative_mark,
            'correct_marks': correct_marks,
            'wrong_deduction': wrong_deduction,
            'net_score': net_score,
            'max_possible': max_possible,
            'percentage': round(percentage, 2),
            'percentile': round(percentile, 2),
            'score_summary': f"Score: {net_score}/{max_possible} ({percentage:.1f}%)",
            'detailed_summary': f"✅ Correct: {correct_answers} (+{correct_marks})\n❌ Wrong: {wrong_answers} (-{wrong_deduction})\n⏭️ Unanswered: {total_questions - (correct_answers + wrong_answers)}\n📊 Net Score: {net_score}/{max_possible}"
        }


class HTMLProcessor:
    @staticmethod
    def process_html(html_content: str, brand_name: str = "Nomis Quiz", 
                    telegram_link: str = "https://t.me/King_Nomis") -> str:
        """
        Process HTML content and apply the Nomis UI modifications.
        """
        try:
            # Extract original content between body tags
            body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL | re.IGNORECASE)
            if not body_match:
                # If no body tag found, use entire content
                body_content = html_content
            else:
                body_content = body_match.group(1)
            
            # Extract title
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.DOTALL | re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else "Nomis Quiz"
            
            # Extract question data for scoring
            question_count = HTMLProcessor.extract_question_count(html_content)
            
            # Replace brand name and link
            processed_html = re.sub(
                r'<a[^>]*href="[^"]*"[^>]*>.*?Boss_Quiz_Robot.*?</a>',
                f'<a class="brand" href="{telegram_link}" target="_blank" rel="noopener">{brand_name}</a>',
                html_content,
                flags=re.DOTALL | re.IGNORECASE
            )
            
            # Replace any other occurrences of Boss_Quiz_Robot
            processed_html = re.sub(
                r'Boss_Quiz_Robot',
                brand_name,
                processed_html,
                flags=re.IGNORECASE
            )
            
            # Apply Nomis UI styles and add JEE scoring functionality
            processed_html = HTMLProcessor.apply_nomis_styles(processed_html, title)
            
            # Add JEE scoring JavaScript
            processed_html = HTMLProcessor.add_jee_scoring_js(processed_html, question_count)
            
            return processed_html
            
        except Exception as e:
            logger.error(f"Error processing HTML: {e}")
            return None
    
    @staticmethod
    def extract_question_count(html_content: str) -> int:
        """Extract number of questions from HTML"""
        try:
            # Look for question indicators
            patterns = [
                r'Question\s+\d+\s+of\s+(\d+)',
                r'Q\.\s*\d+\s*/\s*(\d+)',
                r'Total Questions:\s*(\d+)',
                r'q-num.*?(\d+)',  # Look for question number elements
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                if matches:
                    numbers = [int(m) for m in matches if m.isdigit()]
                    if numbers:
                        return max(numbers)
            
            # Default count
            return 25
        except:
            return 25
    
    @staticmethod
    def add_jee_scoring_js(html_content: str, question_count: int = 25) -> str:
        """Add JavaScript for JEE Main style scoring"""
        
        jee_js = f"""
        <script>
        // JEE Main Scoring System
        class JEEScoringSystem {{
            constructor(totalQuestions = {question_count}) {{
                this.totalQuestions = totalQuestions;
                this.responses = new Array(totalQuestions).fill(null);
                this.answers = new Array(totalQuestions).fill(null);
                this.marks = new Array(totalQuestions).fill(0);
                this.positiveMark = 4.0;
                this.negativeMark = 1.0;
                this.initializeFromStorage();
            }}
            
            initializeFromStorage() {{
                const saved = localStorage.getItem('jee_quiz_responses');
                if (saved) {{
                    this.responses = JSON.parse(saved);
                }}
            }}
            
            saveResponses() {{
                localStorage.setItem('jee_quiz_responses', JSON.stringify(this.responses));
            }}
            
            setAnswer(questionIndex, correctAnswer) {{
                this.answers[questionIndex] = correctAnswer;
            }}
            
            setResponse(questionIndex, response) {{
                this.responses[questionIndex] = response;
                this.calculateQuestionMarks(questionIndex);
                this.saveResponses();
                this.updateScoreDisplay();
            }}
            
            calculateQuestionMarks(questionIndex) {{
                if (this.responses[questionIndex] === null) {{
                    this.marks[questionIndex] = 0;
                    return;
                }}
                
                if (this.answers[questionIndex] === null) {{
                    this.marks[questionIndex] = 0;
                    return;
                }}
                
                if (this.responses[questionIndex] === this.answers[questionIndex]) {{
                    this.marks[questionIndex] = this.positiveMark;
                }} else {{
                    this.marks[questionIndex] = -this.negativeMark;
                }}
            }}
            
            calculateTotalScore() {{
                let correct = 0;
                let wrong = 0;
                let totalScore = 0;
                
                for (let i = 0; i < this.totalQuestions; i++) {{
                    if (this.responses[i] !== null) {{
                        if (this.marks[i] > 0) {{
                            correct++;
                        }} else if (this.marks[i] < 0) {{
                            wrong++;
                        }}
                        totalScore += this.marks[i];
                    }}
                }}
                
                const unanswered = this.totalQuestions - (correct + wrong);
                const maxPossible = this.totalQuestions * this.positiveMark;
                const percentage = maxPossible > 0 ? (totalScore / maxPossible * 100) : 0;
                
                // Simulated percentile
                const percentile = Math.min(99.9, Math.max(0, percentage + (100 - percentage) * 0.3));
                
                return {{
                    correct: correct,
                    wrong: wrong,
                    unanswered: unanswered,
                    totalScore: totalScore,
                    maxPossible: maxPossible,
                    percentage: percentage.toFixed(2),
                    percentile: percentile.toFixed(2),
                    scoreSummary: `Score: ${{totalScore}}/${{maxPossible}} (${{percentage.toFixed(1)}}%)`,
                    detailedSummary: `✅ Correct: ${{correct}} (+${{correct * this.positiveMark}})<br>
                                     ❌ Wrong: ${{wrong}} (-${{wrong * this.negativeMark}})<br>
                                     ⏭️ Unanswered: ${{unanswered}}<br>
                                     📊 Net Score: ${{totalScore}}/${{maxPossible}}`
                }};
            }}
            
            updateScoreDisplay() {{
                const score = this.calculateTotalScore();
                
                // Update score in palette
                const scoreElement = document.getElementById('jee-score-display');
                if (scoreElement) {{
                    scoreElement.innerHTML = `
                        <div class="score-card">
                            <h3>JEE Score</h3>
                            <div class="score-metric">
                                <span class="score-value">${{score.totalScore.toFixed(1)}}</span>
                                <span class="score-label">/${{score.maxPossible}}</span>
                            </div>
                            <div class="score-breakdown">
                                <span class="correct">✅ ${{score.correct}}</span>
                                <span class="wrong">❌ ${{score.wrong}}</span>
                                <span class="unanswered">⏭️ ${{score.unanswered}}</span>
                            </div>
                        </div>
                    `;
                }}
                
                // Update final results if available
                const resultElement = document.getElementById('jee-final-results');
                if (resultElement) {{
                    resultElement.innerHTML = this.generateResultsHTML(score);
                }}
            }}
            
            generateResultsHTML(score) {{
                return `
                <div class="jee-results-section">
                    <h2 class="result-title">JEE Main Style Results</h2>
                    <div class="metrics">
                        <div class="metric">
                            <div class="metric-label">Total Score</div>
                            <div class="metric-value">${{score.totalScore.toFixed(1)}}/${{score.maxPossible}}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Percentage</div>
                            <div class="metric-value">${{score.percentage}}%</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Percentile</div>
                            <div class="metric-value">${{score.percentile}}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Correct Answers</div>
                            <div class="metric-value">${{score.correct}}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Wrong Answers</div>
                            <div class="metric-value">${{score.wrong}}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Unanswered</div>
                            <div class="metric-value">${{score.unanswered}}</div>
                        </div>
                    </div>
                    <div class="score-analysis">
                        <h3>Score Analysis</h3>
                        <p>${{score.detailedSummary.replace('\\n', '<br>')}}</p>
                    </div>
                </div>
                `;
            }}
            
            showFinalResults() {{
                const score = this.calculateTotalScore();
                const resultsHTML = this.generateResultsHTML(score);
                
                // Create modal for results
                const modal = document.createElement('div');
                modal.className = 'jee-results-modal';
                modal.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>🎯 JEE Main Style Results</h2>
                        <button class="close-modal">&times;</button>
                    </div>
                    <div class="modal-body">
                        ${{resultsHTML}}
                    </div>
                    <div class="modal-footer">
                        <button class="btn-primary" onclick="window.print()">Print Results</button>
                        <button class="btn-secondary close-modal">Close</button>
                    </div>
                </div>
                `;
                
                document.body.appendChild(modal);
                
                // Add modal styles
                const style = document.createElement('style');
                style.textContent = `
                    .jee-results-modal {{
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        background: rgba(0,0,0,0.5);
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        z-index: 10000;
                    }}
                    .modal-content {{
                        background: var(--card);
                        border-radius: 12px;
                        width: 90%;
                        max-width: 800px;
                        max-height: 90vh;
                        overflow-y: auto;
                    }}
                    .modal-header {{
                        padding: 20px;
                        border-bottom: 1px solid var(--border);
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }}
                    .modal-body {{
                        padding: 20px;
                    }}
                    .modal-footer {{
                        padding: 20px;
                        border-top: 1px solid var(--border);
                        text-align: right;
                    }}
                    .close-modal {{
                        background: none;
                        border: none;
                        font-size: 24px;
                        cursor: pointer;
                        color: var(--muted);
                    }}
                `;
                document.head.appendChild(style);
                
                // Close modal functionality
                modal.querySelectorAll('.close-modal').forEach(btn => {{
                    btn.addEventListener('click', () => modal.remove());
                }});
            }}
        }}
        
        // Initialize scoring system
        const jeeScoring = new JEEScoringSystem();
        
        // Override quiz submission to show JEE results
        document.addEventListener('DOMContentLoaded', function() {{
            // Add JEE score display to palette
            const palette = document.querySelector('.palette');
            if (palette) {{
                const scoreDisplay = document.createElement('div');
                scoreDisplay.id = 'jee-score-display';
                scoreDisplay.className = 'score-display';
                palette.insertBefore(scoreDisplay, palette.firstChild);
            }}
            
            // Modify final submit button
            const submitBtn = document.querySelector('.submit-btn');
            if (submitBtn) {{
                submitBtn.addEventListener('click', function(e) {{
                    e.preventDefault();
                    jeeScoring.showFinalResults();
                }});
            }}
            
            // Update scores when options are selected
            document.querySelectorAll('.option').forEach(option => {{
                option.addEventListener('click', function() {{
                    // Extract question index and selected answer
                    const questionIndex = 0; // You'll need to implement question index extraction
                    const selectedAnswer = this.getAttribute('data-answer') || this.textContent.trim();
                    
                    jeeScoring.setResponse(questionIndex, selectedAnswer);
                }});
            }});
            
            // Initial score update
            jeeScoring.updateScoreDisplay();
        }});
        </script>
        """
        
        # Insert JEE JavaScript before closing body tag
        body_pattern = r'</body>'
        if re.search(body_pattern, html_content, re.DOTALL | re.IGNORECASE):
            html_content = re.sub(
                body_pattern,
                jee_js + '</body>',
                html_content,
                flags=re.DOTALL | re.IGNORECASE
            )
        else:
            html_content += jee_js
        
        return html_content
    
    @staticmethod
    def apply_nomis_styles(html_content: str, title: str) -> str:
        """
        Apply the Nomis UI styles to the HTML content with JEE scoring enhancements.
        """
        # Nomis CSS styles with JEE scoring additions
        nomis_css = """
        <style>
        /* Existing styles remain... */
        /* Add JEE scoring specific styles */
        
        .score-display {
            background: var(--card);
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 16px;
            border: 2px solid var(--primary);
        }
        
        .score-card {
            text-align: center;
        }
        
        .score-card h3 {
            color: var(--primary);
            margin-bottom: 8px;
            font-size: 14px;
        }
        
        .score-metric {
            display: flex;
            justify-content: center;
            align-items: baseline;
            margin-bottom: 8px;
        }
        
        .score-value {
            font-size: 24px;
            font-weight: 700;
            color: var(--primary);
        }
        
        .score-label {
            font-size: 14px;
            color: var(--muted);
            margin-left: 4px;
        }
        
        .score-breakdown {
            display: flex;
            justify-content: space-around;
            font-size: 12px;
        }
        
        .score-breakdown .correct {
            color: #10b981;
        }
        
        .score-breakdown .wrong {
            color: #ef4444;
        }
        
        .score-breakdown .unanswered {
            color: var(--muted);
        }
        
        .jee-results-section {
            background: var(--card);
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: var(--shadow);
        }
        
        .jee-results-section .result-title {
            text-align: center;
            color: var(--primary);
            margin-bottom: 24px;
        }
        
        .score-analysis {
            background: var(--opt);
            padding: 16px;
            border-radius: 8px;
            margin-top: 20px;
        }
        
        .score-analysis h3 {
            color: var(--primary);
            margin-bottom: 12px;
        }
        
        .marking-scheme {
            background: var(--opt);
            padding: 12px;
            border-radius: 8px;
            margin: 16px 0;
            font-size: 14px;
        }
        
        .marking-scheme h4 {
            color: var(--primary);
            margin-bottom: 8px;
        }
        
        .marking-item {
            display: flex;
            justify-content: space-between;
            padding: 4px 0;
            border-bottom: 1px solid var(--border);
        }
        
        .marking-item:last-child {
            border-bottom: none;
        }
        </style>
        """
        
        # Update title
        html_content = re.sub(
            r'<title[^>]*>.*?</title>',
            f'<title>{title} - JEE Style Quiz</title>',
            html_content,
            flags=re.DOTALL | re.IGNORECASE
        )
        
        # Find and replace the CSS
        style_pattern = r'<style[^>]*>.*?</style>'
        
        if re.search(style_pattern, html_content, re.DOTALL | re.IGNORECASE):
            # Replace existing style with enhanced style
            html_content = re.sub(
                style_pattern,
                nomis_css,
                html_content,
                flags=re.DOTALL | re.IGNORECASE
            )
        else:
            # Insert enhanced style after head tag
            head_pattern = r'</head>'
            html_content = re.sub(
                head_pattern,
                nomis_css + '</head>',
                html_content,
                flags=re.DOTALL | re.IGNORECASE
            )
        
        # Add marking scheme info to the HTML
        marking_scheme_html = """
        <div class="marking-scheme">
            <h4>🎯 JEE Main Marking Scheme</h4>
            <div class="marking-item">
                <span>Correct Answer</span>
                <span class="correct">+4.0 marks</span>
            </div>
            <div class="marking-item">
                <span>Wrong Answer</span>
                <span class="wrong">-1.0 mark</span>
            </div>
            <div class="marking-item">
                <span>Unanswered</span>
                <span>0 marks</span>
            </div>
        </div>
        """
        
        # Insert marking scheme into the quiz
        if re.search(r'<div[^>]*class="[^"]*instructions[^"]*"[^>]*>', html_content):
            html_content = re.sub(
                r'(<div[^>]*class="[^"]*instructions[^"]*"[^>]*>.*?</div>)',
                r'\1' + marking_scheme_html,
                html_content,
                flags=re.DOTALL | re.IGNORECASE
            )
        
        # Update theme button text
        html_content = re.sub(
            r'🌙 Dark Mode',
            '🌙 Dark',
            html_content
        )
        html_content = re.sub(
            r'☀️ Light Mode',
            '☀️ Light',
            html_content
        )
        
        return html_content


class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.application = Application.builder().token(token).build()
        
        # Register handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("html", self.html_command))
        self.application.add_handler(CommandHandler("score", self.score_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
    
    async def start(self, update: Update, context: CallbackContext) -> None:
        """Send a message when the command /start is issued."""
        user = update.effective_user
        await update.message.reply_text(
            f'Hi {user.first_name}! I am the Nomis HTML Processor Bot with JEE Scoring.\n\n'
            'Send me an HTML quiz file to get JEE Main style scoring.\n\n'
            'Commands:\n'
            '/html - Process HTML file with JEE scoring\n'
            '/score - Calculate JEE scores manually\n'
            '/help - Show help information'
        )
    
    async def help(self, update: Update, context: CallbackContext) -> None:
        """Send a message when the command /help is issued."""
        help_text = (
            "📋 *Nomis HTML Processor Bot with JEE Scoring*\n\n"
            "I can process HTML quiz files with JEE Main style scoring system.\n\n"
            "*JEE Main Marking Scheme:*\n"
            "✅ Correct Answer: +4.0 marks\n"
            "❌ Wrong Answer: -1.0 mark\n"
            "⏭️ Unanswered: 0 marks\n\n"
            "*How to use:*\n"
            "1. Send me an HTML quiz file\n"
            "2. Or use the /html command\n"
            "3. I'll add JEE scoring functionality\n\n"
            "*Features:*\n"
            "• JEE Main style scoring system\n"
            "• Real-time score calculation\n"
    )
    async def score_command(self, update: Update, context: CallbackContext) -> None:
        """Calculate JEE scores manually."""
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "Usage: /score correct_answers wrong_answers [total_questions]\n\n"
                "Example: /score 15 5 25\n"
                "This calculates JEE Main style score for 15 correct, 5 wrong out of 25 questions."
            )
            return
        
        try:
            correct = int(context.args[0])
            wrong = int(context.args[1])
            total = int(context.args[2]) if len(context.args) > 2 else (correct + wrong)
            
            if correct + wrong > total:
                await update.message.reply_text("Error: Correct + wrong answers cannot exceed total questions.")
                return
            
            score = JEEScorer.calculate_jee_score(correct, wrong, total)
            
            response = (
                f"🎯 *JEE Main Style Score Calculation*\n\n"
                f"📊 *Total Questions:* {total}\n"
                f"✅ *Correct Answers:* {correct} (+{score['correct_marks']} marks)\n"
                f"❌ *Wrong Answers:* {wrong} (-{score['wrong_deduction']} marks)\n"
                f"⏭️ *Unanswered:* {score['unanswered']}\n\n"
                f"📈 *Net Score:* {score['net_score']}/{score['max_possible']}\n"
                f"📊 *Percentage:* {score['percentage']}%\n"
                f"🏆 *Percentile:* {score['percentile']}\n\n"
                f"*Marking Scheme:*\n"
                f"• Correct: +{score['positive_mark']} marks\n"
                f"• Wrong: -{score['negative_mark']} mark\n"
                f"• Unanswered: 0 marks"
            )
            
            await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
            
        except ValueError:
            await update.message.reply_text("Please provide valid numbers for correct and wrong answers.")
    
    async def html_command(self, update: Update, context: CallbackContext) -> None:
        """Handle the /html command with JEE scoring."""
        await update.message.reply_text(
            "📚 *JEE Main Style Quiz Processor*\n\n"
            "Send me an HTML quiz file and I'll add:\n"
            "✅ JEE Main marking scheme (+4/-1)\n"
            "✅ Real-time score calculation\n"
            "✅ Detailed results analysis\n"
            "✅ Percentile estimation\n\n"
            "Customize with:\n"
            "/html BrandName https://telegram.link"
        )
        
        # Check if custom brand is provided
        if len(context.args) >= 1:
            brand_name = context.args[0]
            telegram_link = context.args[1] if len(context.args) >= 2 else "https://t.me/King_Nomis"
            context.user_data['custom_brand'] = brand_name
            context.user_data['custom_link'] = telegram_link
            
            await update.message.reply_text(
                f"🎯 Brand set to: {brand_name}\n"
                f"🔗 Link: {telegram_link}\n\n"
                "Now send me an HTML quiz file for JEE scoring!"
            )
    
    async def handle_document(self, update: Update, context: CallbackContext) -> None:
        """Handle document upload with JEE scoring."""
        document = update.message.document
        
        # Check if it's an HTML file
        if not document.file_name.lower().endswith(('.html', '.htm')):
            await update.message.reply_text(
                "Please send an HTML file (.html or .htm extension)."
            )
            return
        
        await update.message.reply_text("🎯 Processing quiz with JEE scoring system...")
        
        try:
            # Download the file
            file = await document.get_file()
            
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.html', delete=False) as tmp_file:
                # Download content
                await file.download_to_drive(tmp_file.name)
                
                # Read the content
                with open(tmp_file.name, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Get custom brand if set
                brand_name = context.user_data.get('custom_brand', 'JEE Quiz')
                telegram_link = context.user_data.get('custom_link', 'https://t.me/King_Nomis')
                
                # Process HTML with JEE scoring
                processed_html = HTMLProcessor.process_html(
                    html_content, 
                    brand_name=brand_name,
                    telegram_link=telegram_link
                )
                
                if processed_html:
                    # Save processed HTML
                    processed_filename = f"jee_style_{document.file_name}"
                    processed_path = tmp_file.name + "_processed.html"
                    
                    with open(processed_path, 'w', encoding='utf-8') as f:
                        f.write(processed_html)
                    
                    # Send back the processed file
                    with open(processed_path, 'rb') as f:
                        caption = (
                            f"🎯 *JEE Main Style Quiz Ready!*\n\n"
                            f"📚 Brand: {brand_name}\n"
                            f"🔗 Link: {telegram_link}\n\n"
                            f"*Features Added:*\n"
                            f"✅ JEE (+4/-1) scoring system\n"
                            f"✅ Real-time score calculation\n"
                            f"✅ Detailed results analysis\n"
                            f"✅ Percentile estimation\n"
                            f"✅ Dark/Light themes\n\n"
                            f"Open in browser to use JEE scoring!"
                        )
                        
                        await update.message.reply_document(
                            document=f,
                            filename=processed_filename,
                            caption=caption,
                            parse_mode=ParseMode.MARKDOWN
                        )
                    
                    # Clean up
                    os.unlink(processed_path)
                    os.unlink(tmp_file.name)
                    
                else:
                    await update.message.reply_text(
                        "❌ Failed to process the HTML file. Please check the format."
                    )
                    
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            await update.message.reply_text(
                f"❌ An error occurred: {str(e)}"
            )
    
    async def handle_message(self, update: Update, context: CallbackContext) -> None:
        """Handle text messages."""
        text = update.message.text
        
        if text:
            # If user sends HTML content directly (for testing)
            if '<html' in text.lower() or '<!doctype' in text.lower():
                await update.message.reply_text(
                    "It looks like you sent HTML content. "
                    "Please send it as a file attachment for JEE scoring."
                )
            else:
                await update.message.reply_text(
                    "Send me an HTML quiz file to add JEE Main scoring!\n"
                    "Use /score to calculate JEE scores manually.\n"
                    "Use /help for more information."
                )
    
    def run(self):
        """Run the bot."""
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    # <<< PUT YOUR TOKEN HERE >>> 
    TOKEN = "8562065126:AAGeTFV45xNi-PYcJ03IoXln9Z1IiCXDI_k"
    
    if not TOKEN:
        print("Please set the TELEGRAM_BOT_TOKEN environment variable.")
        print("Example: export TELEGRAM_BOT_TOKEN='your_bot_token_here'")
        return
    
    # Create and run bot
    bot = TelegramBot(TOKEN)
    print("Bot is running with JEE scoring system...")
    bot.run()


if __name__ == '__main__':
    main()
