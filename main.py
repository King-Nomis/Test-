import os
import re
import tempfile
import logging
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your bot token (get from @BotFather)
BOT_TOKEN = "8562065126:AAGeTFV45xNi-PYcJ03IoXln9Z1IiCXDI_k"

class HTMLQuizProcessor:
    def __init__(self):
        # Complete mobile CSS replacement
        self.complete_css = """
        /* Full CSS Replacement for Responsive Design */
        :root {
          --primary: #4361ee;
          --secondary: #06d6a0;
          --danger: #ef476f;
          --warning: #ffd166;
          --info: #118ab2;
          --dark: #073b4c;
          --light: #f8f9fa;
          
          --bg: #f8f9fa;
          --bg2: #e9ecef;
          --card: #ffffff;
          --text: #333333;
          --muted: #6c757d;
          --border: #dee2e6;
          --shadow: 0 8px 30px rgba(0,0,0,0.08);
          --shadow-sm: 0 4px 6px rgba(0,0,0,0.04);
          --grad: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          --opt: #ffffff;
          --optH: #f1f8ff;
          
          --radius: 16px;
          --radius-sm: 8px;
          --radius-lg: 24px;
          
          --font-main: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
          --font-heading: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        }
        
        body.dark-mode {
          --primary: #5a6ff0;
          --secondary: #06d6a0;
          --danger: #ff6b9d;
          --warning: #ffd166;
          --info: #06b6d4;
          --dark: #0f172a;
          --light: #1e293b;
          
          --bg: #0f172a;
          --bg2: #1e293b;
          --card: #1e293b;
          --text: #e2e8f0;
          --muted: #94a3b8;
          --border: #334155;
          --shadow: 0 8px 30px rgba(0,0,0,0.3);
          --shadow-sm: 0 4px 6px rgba(0,0,0,0.2);
          --grad: linear-gradient(135deg, #7c3aed 0%, #10b981 100%);
          --opt: #2d3748;
          --optH: #374151;
        }
        
        * {
          box-sizing: border-box;
          margin: 0;
          padding: 0;
        }
        
        body {
          font-family: var(--font-main);
          background: var(--bg);
          color: var(--text);
          line-height: 1.6;
          min-height: 100vh;
          overflow-x: hidden;
          padding-bottom: 80px;
        }
        
        /* Header */
        .header {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          background: var(--card);
          backdrop-filter: blur(10px);
          border-bottom: 1px solid var(--border);
          padding: 12px 16px;
          display: flex;
          align-items: center;
          gap: 12px;
          z-index: 1000;
          flex-wrap: wrap;
        }
        
        .brand {
          background: linear-gradient(135deg, var(--primary), var(--info));
          color: white;
          padding: 8px 16px;
          border-radius: 50px;
          font-weight: 700;
          text-decoration: none;
          font-size: 14px;
          display: flex;
          align-items: center;
          gap: 6px;
          transition: all 0.3s ease;
          border: 1px solid rgba(255,255,255,0.1);
        }
        
        .brand:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 20px rgba(67, 97, 238, 0.3);
        }
        
        .theme-btn, .submit-btn {
          padding: 10px 20px;
          border: none;
          border-radius: 50px;
          font-weight: 700;
          cursor: pointer;
          font-size: 14px;
          transition: all 0.3s ease;
          display: flex;
          align-items: center;
          gap: 6px;
        }
        
        .theme-btn {
          background: var(--opt);
          color: var(--text);
          border: 1px solid var(--border);
        }
        
        .submit-btn {
          background: linear-gradient(135deg, var(--secondary), var(--info));
          color: white;
          border: none;
        }
        
        .timer {
          margin-left: auto;
          background: linear-gradient(135deg, var(--primary), var(--info));
          color: white;
          padding: 10px 20px;
          border-radius: 50px;
          font-weight: 700;
          font-size: 14px;
          display: flex;
          align-items: center;
          gap: 6px;
          box-shadow: var(--shadow-sm);
        }
        
        .timer.warning {
          background: linear-gradient(135deg, var(--danger), var(--warning));
          animation: pulse 1.5s infinite;
        }
        
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.7; }
        }
        
        /* Container */
        .container {
          display: flex;
          flex-direction: column;
          max-width: 1400px;
          margin: 80px auto 20px;
          padding: 0 16px;
          gap: 20px;
          min-height: calc(100vh - 180px);
        }
        
        @media (min-width: 992px) {
          .container {
            flex-direction: row;
            margin-top: 90px;
          }
        }
        
        /* Question Panel */
        .question-panel {
          flex: 1;
          background: var(--card);
          padding: 24px;
          border-radius: var(--radius-lg);
          box-shadow: var(--shadow);
          overflow-y: auto;
          max-height: calc(100vh - 200px);
        }
        
        .q-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          padding-bottom: 16px;
          border-bottom: 2px solid var(--primary);
        }
        
        .q-header span:first-child {
          font-size: 1.5rem;
          font-weight: 800;
          color: var(--primary);
          font-family: var(--font-heading);
        }
        
        .q-marks {
          background: var(--secondary);
          color: white;
          padding: 6px 16px;
          border-radius: 50px;
          font-weight: 700;
          font-size: 14px;
        }
        
        .q-text {
          margin: 24px 0;
          line-height: 1.8;
          font-size: 17px;
          background: var(--opt);
          padding: 20px;
          border-radius: var(--radius);
          border-left: 4px solid var(--primary);
        }
        
        /* Options */
        .options {
          list-style: none;
          margin-top: 24px;
        }
        
        .option {
          margin: 12px 0;
          padding: 18px;
          border-radius: var(--radius);
          background: var(--opt);
          border: 2px solid var(--border);
          cursor: pointer;
          display: flex;
          align-items: flex-start;
          gap: 12px;
          transition: all 0.2s ease;
        }
        
        .option:hover {
          background: var(--optH);
          border-color: var(--primary);
          transform: translateX(4px);
        }
        
        .option input {
          transform: scale(1.2);
          margin-top: 4px;
          accent-color: var(--primary);
        }
        
        .option.selected {
          background: var(--optH);
          border-color: var(--primary);
          font-weight: 600;
        }
        
        /* Palette */
        .palette {
          background: var(--card);
          padding: 20px;
          border-radius: var(--radius-lg);
          box-shadow: var(--shadow);
          height: fit-content;
          max-height: calc(100vh - 120px);
          overflow-y: auto;
          order: -1;
        }
        
        @media (min-width: 992px) {
          .palette {
            order: 0;
          }
        }
        
        .q-numbers {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(50px, 1fr));
          gap: 10px;
        }
        
        .q-num {
          aspect-ratio: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--opt);
          border: 2px solid var(--border);
          border-radius: 12px;
          cursor: pointer;
          font-weight: 700;
          font-size: 16px;
          transition: all 0.3s ease;
          color: var(--text);
        }
        
        .q-num.current {
          border-color: var(--primary);
          box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.2);
          transform: scale(1.1);
        }
        
        .q-num.answered {
          background: var(--secondary);
          color: white;
          border-color: var(--secondary);
        }
        
        .q-num.viewed {
          background: var(--primary);
          color: white;
          border-color: var(--primary);
        }
        
        .q-num.reviewed {
          background: var(--warning);
          color: var(--dark);
          border-color: var(--warning);
        }
        
        /* Mobile Navigation */
        .mobile-nav {
          position: fixed;
          bottom: 0;
          left: 0;
          right: 0;
          background: var(--card);
          border-top: 1px solid var(--border);
          padding: 12px 16px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          z-index: 1000;
          box-shadow: 0 -4px 20px rgba(0,0,0,0.1);
        }
        
        .mobile-nav-info {
          display: flex;
          flex-direction: column;
          align-items: center;
          min-width: 60px;
        }
        
        .mobile-q-number {
          font-size: 20px;
          font-weight: 800;
          color: var(--primary);
          margin-bottom: 4px;
        }
        
        .mobile-q-label {
          font-size: 12px;
          color: var(--muted);
          font-weight: 600;
        }
        
        .mobile-nav-buttons {
          display: flex;
          gap: 10px;
          flex: 1;
          justify-content: center;
        }
        
        .mobile-nav-btn {
          padding: 12px 24px;
          border: 2px solid var(--primary);
          background: var(--card);
          color: var(--primary);
          cursor: pointer;
          border-radius: var(--radius);
          font-weight: 700;
          font-size: 14px;
          transition: all 0.3s ease;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          min-width: 100px;
        }
        
        .mobile-palette-btn {
          padding: 12px;
          border-radius: 50%;
          background: var(--primary);
          color: white;
          border: none;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          width: 50px;
          height: 50px;
          font-size: 20px;
        }
        
        .mobile-palette-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0,0,0,0.8);
          z-index: 2000;
          display: none;
          align-items: center;
          justify-content: center;
          padding: 20px;
        }
        
        .mobile-palette-content {
          background: var(--card);
          border-radius: var(--radius-lg);
          padding: 24px;
          max-width: 500px;
          width: 100%;
          max-height: 80vh;
          overflow-y: auto;
        }
        
        /* Desktop Navigation */
        #nav {
          position: fixed;
          bottom: 20px;
          left: 50%;
          transform: translateX(-50%);
          z-index: 1000;
          display: flex;
          gap: 12px;
          width: calc(100% - 32px);
          max-width: 800px;
          background: var(--card);
          padding: 16px;
          border-radius: var(--radius-lg);
          box-shadow: 0 -8px 32px rgba(0,0,0,0.1);
          border: 1px solid var(--border);
        }
        
        #nav button {
          padding: 14px 20px;
          border: 2px solid var(--primary);
          background: var(--card);
          color: var(--primary);
          cursor: pointer;
          border-radius: var(--radius);
          font-weight: 700;
          flex: 1;
          font-size: 15px;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
          .header {
            padding: 10px;
            gap: 8px;
          }
          
          .brand, .theme-btn, .submit-btn, .timer {
            font-size: 13px;
            padding: 8px 12px;
          }
          
          .container {
            margin-top: 70px;
            padding: 0 12px;
            min-height: calc(100vh - 200px);
          }
          
          .question-panel, .palette {
            padding: 16px;
            border-radius: var(--radius);
          }
          
          .q-text {
            padding: 16px;
            font-size: 16px;
          }
          
          .option {
            padding: 14px;
            font-size: 15px;
          }
          
          #nav {
            display: none;
          }
          
          .mobile-nav {
            display: flex;
          }
          
          .q-numbers {
            grid-template-columns: repeat(auto-fill, minmax(45px, 1fr));
          }
        }
        
        @media (min-width: 769px) {
          .mobile-nav, .mobile-palette-btn, .mobile-palette-overlay {
            display: none !important;
          }
          
          #nav {
            display: flex;
          }
        }
        
        @media (max-width: 480px) {
          .q-header {
            flex-direction: column;
            gap: 12px;
            align-items: flex-start;
          }
          
          .q-header span:first-child {
            font-size: 1.3rem;
          }
          
          .mobile-nav {
            padding: 10px;
          }
          
          .mobile-nav-btn {
            padding: 10px 16px;
            min-width: 80px;
            font-size: 13px;
          }
          
          .q-numbers {
            grid-template-columns: repeat(5, 1fr);
          }
          
          .q-num {
            font-size: 14px;
          }
        }
        """
        
        self.complete_js = """
        // Complete JavaScript for mobile support
        const Q = []; // Will be replaced with actual questions
        
        function toggleMobilePalette() {
            const overlay = document.getElementById('mobilePaletteOverlay');
            overlay.style.display = overlay.style.display === 'flex' ? 'none' : 'flex';
            if (overlay.style.display === 'flex') {
                updateMobilePalette();
            }
        }
        
        function updateMobilePalette() {
            document.querySelectorAll('#mobilePalette .q-num').forEach((n, i) => {
                n.classList.remove('viewed','answered','reviewed','current');
                if (i === curr) n.classList.add('current');
                if (rev[i]) n.classList.add('reviewed');
                else if (ans[i]) n.classList.add('answered');
                else if (vis[i]) n.classList.add('viewed');
            });
            
            // Update mobile stats
            const a = Object.keys(ans).length;
            document.getElementById('mobileAns').textContent = a;
            document.getElementById('mobileNotAns').textContent = Q.length - a;
            document.getElementById('mobileNotVis').textContent = vis.filter(v => !v).length;
            document.getElementById('mobileRev').textContent = rev.filter(Boolean).length;
        }
        
        function initPalette(){
            const p = document.getElementById('palette');
            const mp = document.getElementById('mobilePalette');
            p.innerHTML = '';
            mp.innerHTML = '';
            
            Q.forEach((_, i) => {
                const d = document.createElement('div');
                d.className = 'q-num'; 
                d.textContent = i + 1; 
                d.onclick = () => {
                    show(i);
                    if (window.innerWidth <= 768) {
                        toggleMobilePalette();
                    }
                };
                p.appendChild(d);
                
                // Mobile palette
                const md = d.cloneNode(true);
                md.onclick = () => {
                    show(i);
                    toggleMobilePalette();
                };
                mp.appendChild(md);
                
                rev[i] = false; 
                vis[i] = false; 
                qTimes[i] = 0;
            });
            updateStats();
        }
        
        function show(i){
            document.getElementById('mobileQNum').textContent = i + 1;
            // Rest of show function will be merged...
        }
        
        function startTest(){
            document.getElementById('start').style.display='none';
            document.getElementById('header').style.display='flex';
            document.getElementById('main').style.display='flex';
            document.getElementById('qContainer').style.display='block';
            document.getElementById('result').style.display='none';
            
            // Show appropriate navigation based on screen size
            if (window.innerWidth <= 768) {
                document.getElementById('mobileNav').style.display = 'flex';
                document.getElementById('nav').style.display = 'none';
            } else {
                document.getElementById('nav').style.display = 'flex';
                document.getElementById('mobileNav').style.display = 'none';
            }
            
            if (document.getElementById('palette').children.length === 0) {
                initPalette();
            }
            show(0);
        }
        
        // Handle window resize
        window.addEventListener('resize', () => {
            if (window.innerWidth <= 768) {
                if (document.getElementById('main').style.display === 'flex') {
                    document.getElementById('nav').style.display = 'none';
                    document.getElementById('mobileNav').style.display = 'flex';
                }
            } else {
                if (document.getElementById('main').style.display === 'flex') {
                    document.getElementById('mobileNav').style.display = 'none';
                    document.getElementById('nav').style.display = 'flex';
                }
            }
        });
        
        // Escape key to close mobile palette
        document.addEventListener('keydown', e => {
            if (e.key === 'Escape') {
                const overlay = document.getElementById('mobilePaletteOverlay');
                if (overlay.style.display === 'flex') {
                    toggleMobilePalette();
                }
            }
        });
        """

    def process_html(self, html_content):
        """COMPLETE HTML processing - replaces everything with new UI"""
        
        # 1. Extract questions array from original
        q_array_match = re.search(r'const Q = \[(.*?)\];', html_content, re.DOTALL)
        if q_array_match:
            q_array = q_array_match.group(0)
        else:
            q_array = "const Q = [];"
        
        # 2. Replace ENTIRE CSS section
        # Find the entire style section and replace it
        style_pattern = r'<style>[\s\S]*?</style>'
        if re.search(style_pattern, html_content):
            html_content = re.sub(style_pattern, f'<style>\n{self.complete_css}\n</style>', html_content)
        else:
            # Insert after head if no style tag
            html_content = html_content.replace('</head>', f'<style>\n{self.complete_css}\n</style>\n</head>')
        
        # 3. Replace brand and links
        html_content = html_content.replace('Boss_Quiz_Robot', 'Nomis Test')
        html_content = html_content.replace('Boss Quiz Robot', 'Nomis Test')
        html_content = html_content.replace(
            'href="https://t.me/Boss_Quiz_Robot"',
            'href="https://t.me/King_Nomis"'
        )
        
        # Update brand HTML
        brand_pattern = r'<a class="brand"[^>]*>[\s\S]*?</a>'
        new_brand = '''<a class="brand" href="https://t.me/King_Nomis" target="_blank" rel="noopener">
      <span>👑</span> Nomis Test
    </a>'''
        html_content = re.sub(brand_pattern, new_brand, html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # 4. Add mobile navigation HTML
        mobile_nav_html = '''
        <!-- Mobile Navigation -->
        <div class="mobile-nav" id="mobileNav" style="display:none;">
            <div class="mobile-nav-info">
                <div class="mobile-q-number" id="mobileQNum">1</div>
                <div class="mobile-q-label">Question</div>
            </div>
            
            <div class="mobile-nav-buttons">
                <button class="mobile-nav-btn" id="mobilePrevBtn" onclick="prev()">
                    ← Prev
                </button>
                <button class="mobile-nav-btn" id="mobileMarkBtn" onclick="mark()">
                    ⭐ Mark
                </button>
                <button class="mobile-nav-btn" id="mobileNextBtn" onclick="next()">
                    Next →
                </button>
            </div>
            
            <button class="mobile-palette-btn" onclick="toggleMobilePalette()">
                📝
            </button>
        </div>

        <!-- Mobile Palette Overlay -->
        <div class="mobile-palette-overlay" id="mobilePaletteOverlay">
            <div class="mobile-palette-content">
                <div class="mobile-palette-header">
                    <h3 class="palette-title">📝 Questions Palette</h3>
                    <button class="mobile-palette-close" onclick="toggleMobilePalette()">
                        ×
                    </button>
                </div>
                <div class="status-legend">
                    <div class="status-item">
                        <div class="status-value" id="mobileAns">0</div>
                        <div class="status-label">Answered</div>
                    </div>
                    <div class="status-item">
                        <div class="status-value" id="mobileNotAns">20</div>
                        <div class="status-label">Not Answered</div>
                    </div>
                    <div class="status-item">
                        <div class="status-value" id="mobileNotVis">20</div>
                        <div class="status-label">Not Visited</div>
                    </div>
                    <div class="status-item">
                        <div class="status-value" id="mobileRev">0</div>
                        <div class="status-label">Marked</div>
                    </div>
                </div>
                <div class="q-numbers" id="mobilePalette"></div>
            </div>
        </div>
        '''
        
        # Insert before closing body tag
        html_content = html_content.replace('</body>', mobile_nav_html + '\n</body>')
        
        # 5. Replace JavaScript completely
        js_pattern = r'<script>[\s\S]*?</script>'
        
        # Extract important functions from original JS that we need to keep
        original_js = re.search(js_pattern, html_content, re.DOTALL)
        if original_js:
            original_js_content = original_js.group()
            
            # Extract specific functions we need
            func_patterns = {
                'show': r'function show\(i\)\{[\s\S]*?\n\}',
                'prev': r'function prev\(\)\{[\s\S]*?\n\}',
                'next': r'function next\(\)\{[\s\S]*?\n\}',
                'mark': r'function mark\(\)\{[\s\S]*?\n\}',
                'submit': r'function submit\([^)]*\)\{[\s\S]*?\n\}',
                'review': r'function review\(\)\{[\s\S]*?\n\}',
                'startTimer': r'function startTimer\(\)\{[\s\S]*?\n\}',
                'stopAll': r'function stopAll\(\)\{[\s\S]*?\n\}',
                'toggleTheme': r'function toggleTheme\(\)\{[\s\S]*?\n\}',
                'pad': r'function pad\(n\)\{[\s\S]*?\n\}',
                'updatePalette': r'function updatePalette\(\)\{[\s\S]*?\n\}',
                'updateStats': r'function updateStats\(\)\{[\s\S]*?\n\}',
                'updateNav': r'function updateNav\(\)\{[\s\S]*?\n\}',
            }
            
            extracted_funcs = {}
            for func_name, pattern in func_patterns.items():
                match = re.search(pattern, original_js_content, re.DOTALL)
                if match:
                    extracted_funcs[func_name] = match.group()
            
            # Create new JavaScript with mobile support
            new_js = f'''<script>
{q_array}

const TIME = 3000;

let time = TIME, curr = 0, ans = {{}}, rev = [], vis = [], qTimes = [], qStart = null;
let done = false, reviewMode = false, timerHandle = null;

{extracted_funcs.get('toggleTheme', 'function toggleTheme(){/* original function */}')}

{extracted_funcs.get('startTimer', 'function startTimer(){/* original function */}')}

{extracted_funcs.get('stopAll', 'function stopAll(){/* original function */}')}

{extracted_funcs.get('pad', 'function pad(n){return String(n).padStart(2,"0");}')}

{self.complete_js}

// Merge show function with mobile update
{extracted_funcs.get('show', 'function show(i){/* original show function */}').replace('function show(i){', '''function show(i){
    document.getElementById('mobileQNum').textContent = i + 1;''')}

{extracted_funcs.get('updatePalette', 'function updatePalette(){/* original function */}')}

{extracted_funcs.get('updateStats', 'function updateStats(){/* original function */}')}

{extracted_funcs.get('updateNav', 'function updateNav(){/* original function */}')}

{extracted_funcs.get('prev', 'function prev(){if (curr > 0) show(curr - 1);}')}

{extracted_funcs.get('next', 'function next(){if (curr < Q.length - 1) show(curr + 1);}')}

{extracted_funcs.get('mark', 'function mark(){if (!done) { rev[curr] = !rev[curr]; updatePalette(); updateStats(); updateNav(); }}')}

{extracted_funcs.get('submit', 'function submit(auto=false){/* original function */}')}

{extracted_funcs.get('review', 'function review(){reviewMode = true; document.getElementById("result").style.display = "none"; document.getElementById("qContainer").style.display = "block"; document.getElementById("nav").style.display = "flex"; show(curr = 0);}')}

// Initialize on load
window.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        const btn = document.getElementById('themeBtn');
        if (btn) btn.innerHTML = '<span>☀️</span> Light Mode';
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', e => {
    if (e.key === 'ArrowLeft') prev();
    else if (e.key === 'ArrowRight') next();
    else if (e.key === 'm' || e.key === 'M') mark();
    else if (e.key === 'Escape') {
        const overlay = document.getElementById('mobilePaletteOverlay');
        if (overlay.style.display === 'flex') {
            toggleMobilePalette();
        }
    }
});
</script>'''
            
            html_content = html_content.replace(original_js.group(), new_js)
        
        # 6. Update HTML structure if needed
        # Ensure palette has both desktop and mobile versions
        if '<div class="q-numbers" id="palette"></div>' in html_content:
            html_content = html_content.replace(
                '<div class="q-numbers" id="palette"></div>',
                '''<div class="q-numbers" id="palette"></div>
                <div class="q-numbers" id="mobilePalette" style="display:none;"></div>'''
            )
        
        # 7. Update start button if needed
        html_content = html_content.replace(
            '<button class="start-btn" onclick="startTest()">Start Test</button>',
            '<button class="start-btn" onclick="startTest()">🚀 Start Test</button>'
        )
        
        return html_content

# Initialize processor
processor = HTMLQuizProcessor()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    welcome_text = """
👑 *Nomis Test HTML Processor*

I will COMPLETELY transform your quiz HTML files with:
• Full UI redesign with modern colors
• Mobile-friendly navigation bar
• Current question display on mobile
• Palette overlay for mobile
• Updated branding: "Nomis Test" 👑
• Telegram link: @King_Nomis
• Responsive design for all screens

*How to use:*
1. Send me your HTML quiz file
2. I'll completely redesign it
3. Download the modern version

*What gets changed:*
✓ Entire CSS (colors, layout, responsive)
✓ JavaScript (mobile functions added)
✓ Branding (Nomis Test with crown)
✓ Navigation (desktop + mobile)
✓ Structure (mobile overlay added)

Send me an HTML file to see the magic! ✨
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message"""
    await update.message.reply_text(
        "Just send me an HTML file and I'll completely redesign it with Nomis branding and mobile features!",
        parse_mode='Markdown'
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document uploads"""
    if not update.message.document:
        await update.message.reply_text("📁 Please send an HTML file (.html)")
        return
    
    document = update.message.document
    file_name = document.file_name
    
    if not file_name.endswith('.html'):
        await update.message.reply_text("❌ Please send an HTML file with .html extension")
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text("🎨 Redesigning your HTML file... This may take a moment.")
    
    try:
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        
        # Download file
        file = await document.get_file()
        input_path = Path(temp_dir) / file_name
        await file.download_to_drive(input_path)
        
        # Read file
        with open(input_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Process HTML - COMPLETE REDESIGN
        processed_content = processor.process_html(html_content)
        
        # Save processed file
        output_filename = f"nomis_redesigned_{file_name}"
        output_path = Path(temp_dir) / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(processed_content)
        
        # Send processed file
        with open(output_path, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=output_filename,
                caption=f"""✅ COMPLETE REDESIGN COMPLETE!

{file_name} → {output_filename}

✨ *What's New:*
• Modern UI with purple/blue theme
• Mobile navigation bar at bottom
• Question number always visible on mobile
• Palette overlay (tap 📝)
• Nomis Test branding with crown 👑
• Updated to @King_Nomis link
• Fully responsive design

📱 *Test on Mobile:*
1. Open in browser
2. Try the bottom navigation
3. Tap 📝 for question palette
4. Notice question number display

The file has been completely transformed!"""
            )
        
        # Send before/after comparison
        comparison = """
🔄 *Before vs After:*

*BEFORE:*
• Basic quiz interface
• No mobile optimization
• Boss Quiz Robot branding
• Old Telegram link

*AFTER:*
• Modern, colorful UI
• Mobile navigation bar
• Question number display
• Nomis Test branding 👑
• @King_Nomis link
• Palette overlay
• Responsive design

Open the file on both desktop and mobile to see the difference!"""
        
        await update.message.reply_text(comparison, parse_mode='Markdown')
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        
        await processing_msg.delete()
        
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)[:200]}")
        
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except:
            pass
        
        await processing_msg.delete()

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    text = update.message.text.lower()
    
    if text in ['hi', 'hello', 'hey']:
        await update.message.reply_text("👋 Hello! Send me an HTML quiz file and I'll completely redesign it!")
    elif 'html' in text:
        await update.message.reply_text("📄 Send me your HTML file! I'll give it a complete makeover with Nomis branding and mobile features.")
    else:
        await update.message.reply_text("Send me an HTML file to transform it! Type /start for more info.")

def main():
    """Start the bot"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("🎨 Nomis Test HTML Redesign Bot is running...")
    print("✨ Ready to completely transform HTML files!")
    print("📱 Send /start to begin")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("⚠️  IMPORTANT: Replace BOT_TOKEN with your actual bot token!")
        print("1. Message @BotFather on Telegram")
        print("2. Create new bot with /newbot")
        print("3. Copy the token (looks like: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz)")
        print("4. Replace 'YOUR_BOT_TOKEN_HERE' with your token")
    else:
        main()
