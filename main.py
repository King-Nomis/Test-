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
            # First apply brand changes
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
            
            # Apply JEE Main scoring logic
            processed_html = HTMLProcessor.apply_jee_scoring(processed_html)
            
            # Fix the start button onclick issue
            processed_html = HTMLProcessor.fix_start_button(processed_html)
            
            # Apply Nomis UI styles
            processed_html = HTMLProcessor.apply_nomis_styles(processed_html)
            
            return processed_html
            
        except Exception as e:
            logger.error(f"Error processing HTML: {e}")
            return None
    
    @staticmethod
    def fix_start_button(html_content: str) -> str:
        """
        Fix the start button onclick function call.
        """
        # Fix the start button onclick
        html_content = re.sub(
            r'<button[^>]*class="[^"]*start-btn[^"]*"[^>]*onclick="startTest\(\)"[^>]*>',
            '<button class="start-btn" onclick="startTest()">',
            html_content,
            flags=re.IGNORECASE
        )
        
        # Make sure the startTest function exists
        if 'function startTest()' not in html_content:
            # Add the startTest function if missing
            start_test_js = """
function startTest(){
  document.getElementById('start').style.display='none';
  document.getElementById('header').style.display='flex';
  document.getElementById('main').style.display='flex';
  document.getElementById('qContainer').style.display='block';
  document.getElementById('result').style.display='none';
  document.getElementById('nav').style.display='flex';
  if (document.getElementById('palette').children.length === 0) {
    initPalette();
  }
  show(0);
  if (!timerHandle) startTimer();
}
"""
            # Insert before the closing script tag
            html_content = html_content.replace('</script>', start_test_js + '\n</script>')
        
        return html_content
    
    @staticmethod
    def apply_jee_scoring(html_content: str) -> str:
        """
        Apply JEE Main scoring system to the quiz.
        JEE Main: +4 for correct, -1 for wrong, 0 for unanswered
        """
        # Find and fix the submit function
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
        # Find and replace the CSS
        style_pattern = r'<style[^>]*>.*?</style>'
        
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

        @media(max-width:768px){
          .container{flex-direction:column;margin-top:100px}
          .question-panel,.palette{width:100%}
          #nav{flex-direction:column}
          .header{flex-direction:column;gap:12px;align-items:stretch}
          .start-screen{padding:24px 16px}
        }
        </style>
        """
        
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
        
        # Ensure all JavaScript functions are properly defined
        html_content = HTMLProcessor.ensure_javascript_functions(html_content)
        
        return html_content
    
    @staticmethod
    def ensure_javascript_functions(html_content: str) -> str:
        """
        Ensure all necessary JavaScript functions are defined.
        """
        # Common JavaScript functions needed
        common_js = """
function pad(n){ return String(n).padStart(2,'0'); }

function initPalette(){
  const p = document.getElementById('palette');
  p.innerHTML = '';
  Q.forEach((_, i) => {
    const d = document.createElement('div');
    d.className = 'q-num'; d.textContent = i + 1; d.onclick = () => show(i);
    p.appendChild(d); rev[i] = false; vis[i] = false; qTimes[i] = 0;
  });
  updateStats();
}

function updatePalette(){
  document.querySelectorAll('.q-num').forEach((n, i) => {
    n.classList.remove('viewed','answered','reviewed','current');
    if (i === curr) n.classList.add('current');
    if (rev[i]) n.classList.add('reviewed');
    else if (ans[i]) n.classList.add('answered');
    else if (vis[i]) n.classList.add('viewed');
  });
}

function updateStats(){
  const a = Object.keys(ans).length;
  document.getElementById('ans').textContent = a;
  document.getElementById('notAns').textContent = Q.length - a;
  document.getElementById('notVis').textContent = vis.filter(v => !v).length;
  document.getElementById('rev').textContent = rev.filter(Boolean).length;
}

function mark(){ if (!done) { rev[curr] = !rev[curr]; updatePalette(); updateStats(); updateNav(); } }
function prev(){ if (curr > 0) show(curr - 1); }
function next(){ if (curr < Q.length - 1) show(curr + 1); }

function startTimer(){
  if (timerHandle) return;
  timerHandle = setInterval(() => {
    if (!reviewMode && qStart) {
      const e = Math.floor((Date.now() - qStart) / 1000);
      document.getElementById('qTimer').textContent = `Time: ${pad(Math.floor(e/60))}:${pad(e%60)}`;
    }
    const m = Math.floor(time / 60); const s = time % 60;
    document.getElementById('timer').textContent = `${pad(m)}:${pad(s)}`;
    if (time <= 300) document.getElementById('timer').classList.add('warning');
    if (time > 0) time--; else { stopAll(); alert('Time up!'); submit(true); }
  }, 1000);
}

function stopAll(){ if (timerHandle) { clearInterval(timerHandle); timerHandle = null; } qStart = null; }

function review(){
  reviewMode = true;
  document.getElementById('result').style.display = 'none';
  document.getElementById('qContainer').style.display = 'block';
  document.getElementById('nav').style.display = 'flex';
  show(curr = 0);
}

function show(i){
  if (qStart !== null && !reviewMode) qTimes[curr] += Math.floor((Date.now() - qStart) / 1000);
  if (done && !reviewMode) return;
  vis[i] = true; curr = i; const q = Q[i];
  document.getElementById('qNum').textContent = `Question ${i+1} of ${Q.length}`;
  document.getElementById('marks').textContent = q.marks;
  document.getElementById('qText').innerHTML = q.question;

  const opts = document.getElementById('options'); opts.innerHTML = '';
  document.getElementById('solutionSlot').innerHTML = '';

  if (reviewMode) {
    const t = qTimes[i];
    document.getElementById('qTimer').textContent = `Time: ${pad(Math.floor(t/60))}:${pad(t%60)}`;
    q.options.forEach((o, j) => {
      const li = document.createElement('li'); li.className = 'option';
      const letter = String.fromCharCode(65 + j);
      li.innerHTML = `${letter}. ` + o;
      const isCorrect = (j + 1) === q.correct;
      const isUser = ans[i] === (j + 1);
      if (isUser && isCorrect) li.classList.add('correct');
      else if (isUser) li.classList.add('wrong');
      else if (isCorrect) li.classList.add('correct');
      opts.appendChild(li);
    });

    const slot = document.getElementById('solutionSlot');
    const sol = document.createElement('div');
    sol.className = 'solution-wrap';
    sol.style.marginTop = '14px';
    const body = (Q[i].explanation || '');
    sol.innerHTML = `
      <details style="background:var(--opt);border:1px solid var(--border);border-radius:8px;padding:12px;">
        <summary style="cursor:pointer;font-weight:600;color:var(--primary)">View Solution</summary>
        <div style="margin-top:10px" class="solution-body">${body}</div>
      </details>
    `;
    slot.appendChild(sol);
    sol.querySelectorAll && sol.querySelectorAll('img').forEach(img => { img.style.maxWidth = '100%'; img.style.height = 'auto'; });
    const det = sol.querySelector('details');
    if (ans[i] && ans[i] !== q.correct) det.setAttribute('open','open');

    document.getElementById('nav').style.display = 'flex';
    document.getElementById('markBtn').disabled = true;
    document.getElementById('prevBtn').disabled = (curr === 0);
    document.getElementById('nextBtn').disabled = (curr === Q.length - 1);
  } else {
    document.getElementById('qTimer').textContent = 'Time: 00:00';
    q.options.forEach((o, j) => {
      const li = document.createElement('li'); li.className = 'option';
      const letter = String.fromCharCode(65 + j);
      const inp = document.createElement('input');
      inp.type = 'radio'; inp.name = 'answer'; inp.value = j + 1; inp.id = `o${i}-${j}`;
      if (ans[i] === (j + 1)) { inp.checked = true; li.classList.add('selected'); }
      inp.onchange = () => {
        ans[i] = parseInt(inp.value); updatePalette(); updateStats();
        document.querySelectorAll('#options .option').forEach(x => x.classList.remove('selected'));
        li.classList.add('selected');
      };
      const lbl = document.createElement('label'); lbl.htmlFor = inp.id; lbl.innerHTML = `${letter}. ` + o;
      li.appendChild(inp); li.appendChild(lbl);
      li.onclick = e => { if (e.target.tagName !== 'INPUT') { inp.checked = true; inp.onchange(); } };
      opts.appendChild(li);
    });
    document.getElementById('markBtn').disabled = false;
    document.getElementById('nav').style.display = 'flex';
    qStart = Date.now();
  }
  updatePalette(); updateStats(); updateNav();
  if (window.MathJax) MathJax.typeset([document.getElementById('qText'), document.getElementById('options'), document.getElementById('solutionSlot')]);
}

function updateNav(){
  const atEnd = curr === Q.length - 1;
  document.getElementById('prevBtn').disabled = curr === 0 && !reviewMode;
  document.getElementById('nextBtn').disabled = atEnd;
}

// Global variables
let time = TIME, curr = 0, ans = {}, rev = [], vis = [], qTimes = [], qStart = null;
let done = false, reviewMode = false, timerHandle = null;

// Theme toggle
function toggleTheme(){
  document.body.classList.toggle('dark-mode');
  const isDark = document.body.classList.contains('dark-mode');
  document.getElementById('themeBtn').textContent = isDark ? '☀️ Light' : '🌙 Dark';
  localStorage.setItem('theme', isDark ? 'dark' : 'light');
}

// Initialize theme on load
window.addEventListener('DOMContentLoaded', () => {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'dark') {
    document.body.classList.add('dark-mode');
    const btn = document.getElementById('themeBtn');
    if (btn) btn.textContent = '☀️ Light';
  }
});

// Keyboard shortcuts
document.addEventListener('keydown', e => {
  if (e.key === 'ArrowLeft') prev();
  else if (e.key === 'ArrowRight') next();
  else if (e.key === 'm' || e.key === 'M') mark();
  else if (e.key >= '1' && e.key <= '4') {
    const idx = parseInt(e.key) - 1;
    const inputs = document.querySelectorAll('input[type="radio"]');
    if (inputs[idx]) {
      inputs[idx].checked = true;
      inputs[idx].onchange();
    }
  }
});
"""
        
        # Insert the JavaScript before closing body tag
        body_close_pattern = r'</body>'
        if re.search(body_close_pattern, html_content, re.IGNORECASE):
            html_content = re.sub(
                body_close_pattern,
                f'<script>\n{common_js}\n</script>\n</body>',
                html_content,
                flags=re.IGNORECASE
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
            '• All buttons fixed and working\n'
            '• Percentile Estimation\n\n'
            'Commands:\n'
            '/html - Process HTML file\n'
            '/help - Show help information'
        )
    
    async def help(self, update: Update, context: CallbackContext) -> None:
        """Send a message when the command /help is issued."""
        help_text = (
            "🎯 *Nomis HTML Processor Bot with JEE Main Scoring*\n\n"
            "I convert quiz HTML files to JEE Main format with fully functional Nomis UI.\n\n"
            "*Fixed Issues:*\n"
            "• ✅ Start Test button now works\n"
            "• ✅ All navigation buttons functional\n"
            "• ✅ Keyboard shortcuts work\n"
            "• ✅ Theme toggle works\n\n"
            "*JEE Main Scoring:*\n"
            "• ✅ Correct Answer: +4 marks\n"
            "• ❌ Wrong Answer: -1 mark\n"
            "• 🔘 Unanswered: 0 marks\n\n"
            "*How to use:*\n"
            "1. Send me an HTML file\n"
            "2. I'll process it with JEE scoring\n"
            "3. Get back the updated version\n\n"
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
            "*All buttons will be fixed and working:*\n"
            "✅ Start Test button\n"
            "✅ Previous/Next buttons\n"
            "✅ Mark for review\n"
            "✅ Submit button\n"
            "✅ Theme toggle\n\n"
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
        
        await update.message.reply_text("📥 Processing your HTML file with JEE Main scoring...\n\n✅ Fixing all buttons...")
        
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
                
                # Process HTML with JEE scoring and button fixes
                processed_html = HTMLProcessor.process_html(
                    html_content, 
                    brand_name=brand_name,
                    telegram_link=telegram_link
                )
                
                if processed_html:
                    # Save processed HTML
                    processed_filename = f"JEE_FIXED_{document.file_name}"
                    processed_path = tmp_file.name + "_processed.html"
                    
                    with open(processed_path, 'w', encoding='utf-8') as f:
                        f.write(processed_html)
                    
                    # Send back the processed file
                    with open(processed_path, 'rb') as f:
                        await update.message.reply_document(
                            document=f,
                            filename=processed_filename,
                            caption="✅ HTML processed successfully!\n\n"
                                   f"🏷️ Brand: {brand_name}\n"
                                   f"🔗 Link: {telegram_link}\n"
                                   f"📊 Scoring: +4/-1 (JEE Main pattern)\n"
                                   f"🎨 UI: Nomis Modern Design\n"
                                   f"🔧 All buttons fixed and working"
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
            if '<html' in text.lower() or '<!doctype' in text.lower():
                await update.message.reply_text(
                    "It looks like you sent HTML content. "
                    "Please send it as a file attachment for processing."
                )
            else:
                await update.message.reply_text(
                    "Send me an HTML quiz file to convert to JEE Main format!\n"
                    "All buttons will be fixed and working.\n"
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
    print("Fixed: Start Test button and all navigation")
    print("Scoring: +4 for correct, -1 for wrong")
    bot.run()


if __name__ == '__main__':
    main()
