import os
import re
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from telegram.constants import ParseMode
import tempfile

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class HTMLProcessor:
    @staticmethod
    def process_html(html_content: str, brand_name: str = "Nomis Quiz", 
                    telegram_link: str = "https://t.me/King_Nomis") -> str:
        """
        Process HTML content and apply the Nomis UI modifications with JEE Main scoring.
        """
        try:
            # Apply JEE Main scoring logic to the JavaScript
            processed_html = HTMLProcessor.apply_jee_scoring(html_content)
            
            # Replace brand name and link
            processed_html = re.sub(
                r'<a[^>]*href="[^"]*"[^>]*>.*?Boss_Quiz_Robot.*?</a>',
                f'<a class="brand" href="{telegram_link}" target="_blank" rel="noopener">{brand_name}</a>',
                processed_html,
                flags=re.DOTALL | re.IGNORECASE
            )
            
            # Replace any other occurrences of Boss_Quiz_Robot
            processed_html = re.sub(
                r'Boss_Quiz_Robot',
                brand_name,
                processed_html,
                flags=re.IGNORECASE
            )
            
            # Apply Nomis UI styles
            processed_html = HTMLProcessor.apply_nomis_styles(processed_html)
            
            return processed_html
            
        except Exception as e:
            logger.error(f"Error processing HTML: {e}")
            return None
    
    @staticmethod
    def apply_jee_scoring(html_content: str) -> str:
        """
        Apply JEE Main scoring system to the quiz.
        JEE Main: +4 for correct, -1 for wrong, 0 for unanswered
        """
        # Find the submit function
        submit_function_pattern = r'function submit\([^)]*\)\s*\{[^}]*\}'
        
        jee_scoring_code = """
function submit(auto=false){
  if (done) return;
  if (!auto) {
    const un = Q.length - Object.keys(ans).length;
    if (un > 0 && time > 0 && !confirm(`${un} unanswered. Submit?`)) return;
  }
  if (qStart && !reviewMode) qTimes[curr] += Math.floor((Date.now() - qStart) / 1000);
  done = true; stopAll();

  document.getElementById('submitBtn').disabled = true;
  document.querySelectorAll('input[type=radio]').forEach(r => r.disabled = true);

  // JEE Main Scoring: +4 for correct, -1 for wrong, 0 for unanswered
  let cor = 0, wrg = 0, una = 0;
  Q.forEach((q, i) => { 
    if (!ans[i]) {
      una++; 
    } else if (ans[i] === q.correct) {
      cor++; 
    } else {
      wrg++; 
    }
  });
  
  // JEE Main raw score calculation
  const raw_score = (cor * 4) - (wrg * 1);
  const max_score = Q.length * 4;
  
  // Calculate percentage
  const percentage = (cor / Q.length * 100).toFixed(2);
  
  // JEE Main style percentile estimation (simplified)
  const percentile = Math.min(99.99, (cor / Q.length * 100).toFixed(2));
  
  const spent = TIME - time;
  const tm = `${pad(Math.floor(spent/60))}:${pad(spent%60)}`;
  
  document.getElementById('metrics').innerHTML = `
    <div class="metric"><div class="metric-value">${raw_score}/${max_score}</div><div>Raw Score (JEE)</div></div>
    <div class="metric"><div class="metric-value">${cor}</div><div>Correct (+4)</div></div>
    <div class="metric"><div class="metric-value">${wrg}</div><div>Wrong (-1)</div></div>
    <div class="metric"><div class="metric-value">${una}</div><div>Unanswered (0)</div></div>
    <div class="metric"><div class="metric-value">${percentage}%</div><div>Accuracy</div></div>
    <div class="metric"><div class="metric-value">~${percentile}</div><div>Percentile*</div></div>
    <div class="metric"><div class="metric-value">${tm}</div><div>Time</div></div>
    <div style="grid-column: span 3; text-align: center; margin-top: 10px; font-size: 12px; color: var(--muted);">
      *JEE Main Scoring: +4 for correct, -1 for wrong<br>
      Percentile is estimated based on accuracy
    </div>
  `;
  
  document.getElementById('qContainer').style.display = 'none';
  document.getElementById('result').style.display = 'block';
  document.getElementById('nav').style.display = 'none';
}
"""
        
        # Replace the submit function
        if re.search(submit_function_pattern, html_content, re.DOTALL):
            html_content = re.sub(
                submit_function_pattern,
                jee_scoring_code,
                html_content,
                flags=re.DOTALL
            )
        
        # Also update the start screen instructions to mention JEE scoring
        instructions_pattern = r'<div class="instructions">.*?</div>'
        
        jee_instructions = """
<div class="instructions">
  <h2>Test Instructions (JEE Main Pattern)</h2>
  <div class="instruction-item">📊 Total Questions: 20</div>
  <div class="instruction-item">⏱️ Time Limit: 50 minutes</div>
  <div class="instruction-item">✅ Correct Answer: +4 marks</div>
  <div class="instruction-item">❌ Wrong Answer: -1 mark</div>
  <div class="instruction-item">🔘 Unanswered: 0 marks</div>
  <div class="instruction-item">🎯 Mark for review with ⭐ button</div>
  <div class="instruction-item">⌨️ Use keyboard: Arrow keys, 1-4 for options, M for mark</div>
</div>
"""
        
        if re.search(instructions_pattern, html_content, re.DOTALL):
            html_content = re.sub(
                instructions_pattern,
                jee_instructions,
                html_content,
                flags=re.DOTALL
            )
        
        return html_content
    
    @staticmethod
    def apply_nomis_styles(html_content: str) -> str:
        """
        Apply the Nomis UI styles to the HTML content.
        """
        # Same CSS as before, but add JEE scoring highlights
        nomis_css = """
        <style>
        :root {
          --primary:#3a86ff; --secondary:#00bbf9; --danger:#ff5a5f; --warning:#ff9e00;
          --bg:#f0f2f5; --bg2:#e1e5eb; --card:#ffffff; --text:#1a1a1a; --muted:#666666; --border:#d1d9e6;
          --shadow:0 2px 8px rgba(0,0,0,0.08); --grad:linear-gradient(135deg,#3a86ff,#00bbf9);
          --opt:#f8fafc; --optH:#edf2f7;
          --correct:#10b981; --wrong:#ef4444; --unanswered:#6b7280;
        }
        body.dark-mode {
          --bg:#121826; --bg2:#1a2236; --card:#1f2937; --text:#e2e8f0; --muted:#94a3b8; --border:#374151; --opt:#2d3748; --optH:#374151;
          --correct:#10b981; --wrong:#ef4444; --unanswered:#6b7280;
        }
        
        /* JEE Scoring Highlights */
        .jee-score-highlight {
          background: linear-gradient(135deg, #3a86ff, #00bbf9);
          color: white;
          padding: 15px;
          border-radius: 10px;
          margin: 15px 0;
          text-align: center;
          font-weight: bold;
          border: 2px solid #3a86ff;
        }
        
        .jee-positive { color: var(--correct); font-weight: bold; }
        .jee-negative { color: var(--wrong); font-weight: bold; }
        .jee-neutral { color: var(--unanswered); }
        
        *{box-sizing:border-box;margin:0;padding:0}
        body{font-family:'Segoe UI', system-ui, -apple-system, sans-serif;background:var(--bg);color:var(--text);line-height:1.5;padding:16px;min-height:100vh}
        .header{position:fixed;top:16px;left:16px;right:16px;display:flex;gap:12px;z-index:1001;align-items:center;justify-content:space-between}
        .brand{background:linear-gradient(135deg,#3a86ff,#00bbf9);color:#ffffff;padding:8px 16px;border-radius:8px;font-weight:600;text-decoration:none;font-size:14px;display:flex;align-items:center;gap:6px}
        .brand:hover{opacity:0.9;transform:translateY(-1px)}
        .timer{background:var(--card);color:var(--primary);padding:8px 16px;border-radius:8px;font-weight:600;border:2px solid var(--primary);font-size:14px}
        .timer.warning{background:var(--danger);color:#fff;animation:pulse 1s infinite}
        @keyframes pulse{50%{opacity:0.7}}
        .theme-btn,.submit-btn{background:var(--card);color:var(--primary);padding:8px 16px;border:2px solid var(--primary);border-radius:8px;font-weight:600;cursor:pointer;font-size:14px;transition:all 0.2s}
        .submit-btn{background:var(--primary);color:#fff}
        .theme-btn:hover,.submit-btn:hover{opacity:0.9;transform:translateY(-1px)}

        .start-screen{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:calc(100vh - 32px);background:linear-gradient(135deg,#3a86ff 0%,#00bbf9 100%);text-align:center;border-radius:16px;padding:40px 24px}
        .start-title{font-size:2em;font-weight:700;color:#fff;margin-bottom:20px}
        .instructions{background:var(--card);padding:24px;border-radius:12px;box-shadow:var(--shadow);max-width:500px;width:100%}
        .instructions h2{color:var(--primary);margin-bottom:16px;font-size:1.2em}
        .instruction-item{margin:12px 0;color:var(--muted);display:flex;align-items:center;gap:8px}
        .start-btn{background:#fff;color:var(--primary);padding:12px 32px;border:none;border-radius:25px;font-weight:600;cursor:pointer;margin-top:24px;font-size:16px;transition:all 0.2s}
        .start-btn:hover{transform:translateY(-2px);box-shadow:0 4px 12px rgba(0,0,0,0.15)}

        .container{display:flex;max-width:1200px;margin:80px auto 20px;gap:20px;min-height:calc(100vh - 120px)}
        .question-panel{flex:3;background:var(--card);padding:24px;border-radius:12px;box-shadow:var(--shadow)}
        .q-header{font-size:18px;font-weight:600;color:var(--primary);padding-bottom:12px;margin-bottom:16px;display:flex;justify-content:space-between;align-items:center}
        .q-marks{background:var(--primary);color:#fff;padding:4px 12px;border-radius:20px;font-size:13px}
        .q-timer{color:var(--primary);padding:8px 12px;background:var(--optH);border-radius:6px;text-align:right;margin-bottom:16px;font-size:14px}
        .q-text{margin:16px 0;line-height:1.7;font-size:16px;background:var(--opt);padding:16px;border-radius:8px;border-left:3px solid var(--primary)}

        .options{list-style:none;margin-top:20px}
        .option{margin:10px 0;padding:14px 16px;border-radius:8px;background:var(--opt);border:1px solid var(--border);cursor:pointer;display:flex;align-items:center;gap:12px;transition:all 0.2s}
        .option:hover{background:var(--optH);border-color:var(--primary)}
        .option input{transform:scale(1.1)}
        .option.selected{background:var(--optH);border-color:var(--primary);font-weight:500}
        .option.correct{background:#d1fae5!important;border-color:#10b981!important;color:#065f46}
        .option.wrong{background:#fee2e2!important;border-color:#ef4444!important;color:#7f1d1d}

        .palette{flex:1;background:var(--card);padding:20px;border-radius:12px;box-shadow:var(--shadow);height:fit-content}
        .status-legend{background:var(--opt);padding:16px;border-radius:8px;margin-bottom:20px;display:grid;grid-template-columns:repeat(2,1fr);gap:12px;text-align:center}
        .status-item div:first-child{font-size:20px;margin-bottom:4px;font-weight:600}
        .palette-title{font-weight:600;margin-bottom:16px;color:var(--primary);text-align:center;font-size:16px}
        .q-numbers{display:grid;grid-template-columns:repeat(5,1fr);gap:8px}
        .q-num{background:#e2e8f0;padding:12px;text-align:center;cursor:pointer;border-radius:6px;font-weight:600;transition:all 0.2s;min-height:42px;display:flex;align-items:center;justify-content:center;font-size:14px}
        .q-num.answered{background:#10b981;color:#fff}
        .q-num.viewed{background:#3b82f6;color:#fff}
        .q-num.reviewed{background:#f59e0b;color:#1f2937}
        .q-num.current{border:2px solid var(--primary);box-shadow:0 0 0 2px rgba(58,134,255,0.2)}

        body.dark-mode .q-num { background:#374151; color:#e5e7eb; }
        body.dark-mode .q-num.current { background:#1e40af; color:#fff; }
        body.dark-mode .q-num.answered { background:#065f46; color:#fff; }
        body.dark-mode .q-num.viewed { background:#1d4ed8; color:#fff; }
        body.dark-mode .q-num.reviewed { background:#d97706; color:#1f2937; }

        #nav{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);z-index:1000;display:flex;gap:12px;width:calc(100% - 32px);max-width:800px;background:var(--card);padding:16px;border-radius:12px;box-shadow:var(--shadow)}
        #nav button{padding:12px 20px;border:2px solid var(--primary);background:var(--card);color:var(--primary);cursor:pointer;border-radius:8px;font-weight:600;flex:1;transition:all 0.2s}
        #nav button:disabled{background:#e5e7eb;color:#6b7280;cursor:not-allowed;border-color:#e5e7eb;opacity:0.6}
        #nav button:not(:disabled):hover{background:var(--primary);color:#fff}

        .result{text-align:center;padding:32px;background:linear-gradient(135deg,#f1f5f9,#e2e8f0);border-radius:12px}
        body.dark-mode .result{background:linear-gradient(135deg,#1f2937,#374151)}
        .result-title{font-size:24px;font-weight:700;color:var(--primary);margin-bottom:24px}
        .metrics{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-bottom:24px}
        @media(min-width:768px){.metrics{grid-template-columns:repeat(3,1fr)}}
        .metric{background:var(--card);padding:16px;border-radius:8px;box-shadow:var(--shadow)}
        .metric .metric-value{font-size:20px;font-weight:700;color:var(--primary);margin-bottom:4px}
        
        /* JEE Score Card */
        .jee-score-card {
          background: linear-gradient(135deg, #f8fafc, #e2e8f0);
          border-radius: 12px;
          padding: 20px;
          margin: 20px 0;
          border: 2px solid var(--primary);
        }
        
        .jee-score-row {
          display: flex;
          justify-content: space-between;
          margin: 10px 0;
          padding: 8px 0;
          border-bottom: 1px solid var(--border);
        }
        
        .jee-score-label {
          font-weight: 600;
          color: var(--muted);
        }
        
        .jee-score-value {
          font-weight: 700;
          color: var(--primary);
        }

        @media(max-width:768px){
          .container{flex-direction:column;margin-top:100px}
          .question-panel,.palette{width:100%}
          #nav{flex-direction:column}
          .header{flex-direction:column;gap:12px;align-items:stretch}
          .start-screen{padding:24px 16px}
        }
        </style>
        """
        
        # Find and replace the CSS
        style_pattern = r'<style[^>]*>.*?</style>'
        
        if re.search(style_pattern, html_content, re.DOTALL | re.IGNORECASE):
            # Replace existing style with Nomis style
            html_content = re.sub(
                style_pattern,
                nomis_css,
                html_content,
                flags=re.DOTALL | re.IGNORECASE
            )
        else:
            # Insert Nomis style after head tag
            head_pattern = r'</head>'
            html_content = re.sub(
                head_pattern,
                nomis_css + '</head>',
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
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
    
    async def start(self, update: Update, context: CallbackContext) -> None:
        """Send a message when the command /start is issued."""
        user = update.effective_user
        await update.message.reply_text(
            f'Hi {user.first_name}! I am the Nomis HTML Processor Bot with JEE Main Scoring.\n\n'
            'Send me an HTML quiz file and I\'ll convert it with:\n'
            '• JEE Main Scoring (+4/-1)\n'
            '• Nomis UI Design\n'
            '• Percentile Estimation\n\n'
            'Commands:\n'
            '/html - Process HTML file\n'
            '/help - Show help information'
        )
    
    async def help(self, update: Update, context: CallbackContext) -> None:
        """Send a message when the command /help is issued."""
        help_text = (
            "🎯 *Nomis HTML Processor Bot with JEE Main Scoring*\n\n"
            "I convert quiz HTML files to JEE Main format with Nomis UI.\n\n"
            "*JEE Main Scoring System:*\n"
            "• ✅ Correct Answer: +4 marks\n"
            "• ❌ Wrong Answer: -1 mark\n"
            "• 🔘 Unanswered: 0 marks\n\n"
            "*How to use:*\n"
            "1. Send me an HTML file\n"
            "2. I'll process it with JEE scoring\n"
            "3. Get back the updated version\n\n"
            "*Features:*\n"
            "• JEE Main (+4/-1) scoring system\n"
            "• Percentile estimation\n"
            "• Nomis modern UI\n"
            "• Custom branding support\n\n"
            "*Commands:*\n"
            "/start - Start the bot\n"
            "/html [brand] [link] - Process with custom brand\n"
            "/help - Show this help"
        )
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def html_command(self, update: Update, context: CallbackContext) -> None:
        """Handle the /html command."""
        await update.message.reply_text(
            "📁 Send me an HTML quiz file to convert to JEE Main format.\n\n"
            "*JEE Main Scoring will be applied:*\n"
            "✅ Correct: +4 marks\n"
            "❌ Wrong: -1 mark\n"
            "🔘 Unanswered: 0 marks\n\n"
            "Custom brand: /html BrandName https://telegram.link"
        )
        
        # Check if custom brand is provided
        if len(context.args) >= 1:
            brand_name = context.args[0]
            telegram_link = context.args[1] if len(context.args) >= 2 else "https://t.me/King_Nomis"
            context.user_data['custom_brand'] = brand_name
            context.user_data['custom_link'] = telegram_link
            
            await update.message.reply_text(
                f"✅ Brand set: {brand_name}\n"
                f"🔗 Link: {telegram_link}\n\n"
                "Now send me an HTML file!"
            )
    
    async def handle_document(self, update: Update, context: CallbackContext) -> None:
        """Handle document upload."""
        document = update.message.document
        
        # Check if it's an HTML file
        if not document.file_name.lower().endswith(('.html', '.htm')):
            await update.message.reply_text(
                "❌ Please send an HTML file (.html or .htm extension)."
            )
            return
        
        await update.message.reply_text("📥 Processing your HTML file with JEE Main scoring...")
        
        try:
            # Download the file
            file = await document.get_file()
            
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.html', delete=False, encoding='utf-8') as tmp_file:
                # Download content
                await file.download_to_drive(tmp_file.name)
                
                # Read the content
                with open(tmp_file.name, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Get custom brand if set
                brand_name = context.user_data.get('custom_brand', 'Nomis Quiz')
                telegram_link = context.user_data.get('custom_link', 'https://t.me/King_Nomis')
                
                # Process HTML with JEE scoring
                processed_html = HTMLProcessor.process_html(
                    html_content, 
                    brand_name=brand_name,
                    telegram_link=telegram_link
                )
                
                if processed_html:
                    # Save processed HTML
                    processed_filename = f"JEE_{document.file_name}"
                    processed_path = tmp_file.name + "_processed.html"
                    
                    with open(processed_path, 'w', encoding='utf-8') as f:
                        f.write(processed_html)
                    
                    # Send back the processed file
                    with open(processed_path, 'rb') as f:
                        await update.message.reply_document(
                            document=f,
                            filename=processed_filename,
                            caption="✅ HTML processed with JEE Main scoring!\n\n"
                                   f"🏷️ Brand: {brand_name}\n"
                                   f"🔗 Link: {telegram_link}\n"
                                   f"📊 Scoring: +4/-1 (JEE Main pattern)\n"
                                   f"🎨 UI: Nomis Modern Design"
                        )
                    
                    # Clean up
                    os.unlink(processed_path)
                    os.unlink(tmp_file.name)
                    
                else:
                    await update.message.reply_text(
                        "❌ Failed to process the HTML file. Please check if it's a valid quiz HTML."
                    )
                    
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            await update.message.reply_text(
                f"❌ An error occurred: {str(e)}\n\n"
                "Please make sure the HTML file is a valid quiz format."
            )
    
    async def handle_message(self, update: Update, context: CallbackContext) -> None:
        """Handle text messages."""
        text = update.message.text
        
        if text:
            # If user sends HTML content directly
            if '<html' in text.lower() or '<!doctype' in text.lower():
                await update.message.reply_text(
                    "It looks like you sent HTML content. "
                    "Please send it as a file attachment for processing."
                )
            else:
                await update.message.reply_text(
                    "Send me an HTML quiz file to convert to JEE Main format!\n"
                    "Use /help for more information."
                )
    
    def run(self):
        """Run the bot."""
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    # PUT YOUR TOKEN HERE
    TOKEN = "8562065126:AAGeTFV45xNi-PYcJ03IoXln9Z1IiCXDI_k"
    
    if not TOKEN:
        print("Please set the TELEGRAM_BOT_TOKEN.")
        return
    
    # Create and run bot
    bot = TelegramBot(TOKEN)
    print("Bot is running with JEE Main scoring...")
    print("Scoring System: +4 for correct, -1 for wrong")
    bot.run()


if __name__ == '__main__':
    main()
