import re
import json
from telebot import TeleBot, types
from html.parser import HTMLParser

# --- CONFIGURATION ---
# ⚠️ 1. Replace with your actual bot token from BotFather
API_TOKEN = '8562065126:AAGeTFV45xNi-PYcJ03IoXln9Z1IiCXDI_k' 
# ⚠️ 2. The name of the HTML file uploaded
QUIZ_HTML_FILE = '(voraclasses)(chapter_test_maths)(uncategorized)(sets) (1).html' 

# State Management: {chat_id: {'current_q': int, 'score': float, 'total_answered': int, 'answers': {q_index: user_answer}}}
user_state = {}

# --- HELPER FUNCTIONS ---

def extract_quiz_data_from_html(html_file_path):
    """Reads the HTML file and extracts the JSON array assigned to the 'Q' variable."""
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {html_file_path}")
        return []

    # Regex to find the 'const Q = [...];' part
    # The 're.DOTALL' flag allows '.' to match newlines
    match = re.search(r'const Q\s*=\s*(\[.*?\]);', content, re.DOTALL)
    
    if not match:
        print("Error: Could not find 'const Q = [...]' array in the HTML content.")
        return []
    
    json_string = match.group(1).strip()
    
    # Remove trailing semicolon if present
    if json_string.endswith(';'):
        json_string = json_string[:-1]
    
    try:
        # Parse the JSON string into a Python list
        quiz_data = json.loads(json_string)
        print(f"Successfully loaded {len(quiz_data)} questions.")
        return quiz_data
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON quiz data: {e}")
        return []

def clean_html_for_telegram(html_text):
    """Simplifies complex HTML/MathJax to be readable in a Telegram message (supports HTML parse mode)."""
    # 1. Remove style/font tags common in the file
    text = re.sub(r'<\/?p.*?>|<\/?span.*?>', '', html_text)
    
    # 2. Replace <img> tags with a placeholder for the URL, since Telegram can't render the image
    # directly as a part of the text, but the user can see the link.
    text = re.sub(r'<img\s+src="([^"]+)".*?>', r' [Image: \1] ', text)
    
    # 3. Use Telegram's <b> tag for emphasis where needed (e.g., if there were original <strong> tags)
    # 4. Clean up whitespace and newlines
    text = re.sub(r'\s{2,}', ' ', text).strip()
    
    return text.replace('&nbsp;', ' ').replace('<br>', '\n')

# --- INITIAL DATA LOAD ---
QUIZ_QUESTIONS = extract_quiz_data_from_html(QUIZ_HTML_FILE)
bot = TeleBot(API_TOKEN)

# --- BOT HANDLERS ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Handles the /start command."""
    bot.send_message(message.chat.id, 
                     "Hello! I'm a quiz bot. Use /quiz to begin the test based on the loaded HTML data.")

@bot.message_handler(commands=['quiz'])
def start_quiz(message):
    """Handles the /quiz command to start a new quiz session."""
    chat_id = message.chat.id
    if not QUIZ_QUESTIONS:
        bot.send_message(chat_id, "❌ Quiz data not loaded. Please check the `QUIZ_HTML_FILE` path and format.")
        return
    
    # Initialize a new quiz state for the user
    user_state[chat_id] = {'current_q': 0, 'score': 0.0, 'total_answered': 0, 'answers': {}}
    
    # Send the first question
    send_question(chat_id, 0)

def send_question(chat_id, q_index):
    """Sends a specific question to the user with inline keyboard options."""
    if q_index >= len(QUIZ_QUESTIONS):
        # End of quiz
        end_quiz(chat_id)
        return

    q = QUIZ_QUESTIONS[q_index]
    
    # Prepare the question text, cleaning the embedded HTML
    q_text_raw = clean_html_for_telegram(q['question'])
    q_number = q_index + 1
    total_questions = len(QUIZ_QUESTIONS)
    
    question_text = (
        f"<b>Question {q_number}/{total_questions}</b> (Marks: {q['marks']}):\n\n"
        f"{q_text_raw}"
    )
    
    # Create the inline keyboard for options
    keyboard = types.InlineKeyboardMarkup()
    for i, option_html in enumerate(q['options']):
        option_letter = chr(65 + i) # Convert 0, 1, 2, 3 to A, B, C, D
        option_text = clean_html_for_telegram(option_html)
        
        # Callback data format: 'q_index|user_answer_index' (e.g., '0|1' for question 1, option 1)
        callback_data = f"{q_index}|{i+1}" 
        
        # Create a user-friendly button text (Letter. Option Snippet)
        button_text = f"{option_letter}. {option_text[:40].splitlines()[0]}" # Use first line, max 40 chars
        
        keyboard.add(types.InlineKeyboardButton(text=button_text, callback_data=callback_data))

    # Send the message using HTML parse mode
    bot.send_message(chat_id, question_text, reply_markup=keyboard, parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: True)
def callback_answer(call):
    """Handles user's answer selection from the inline keyboard."""
    chat_id = call.message.chat.id
    
    if chat_id not in user_state:
        bot.answer_callback_query(call.id, "Quiz session expired. Use /quiz to start a new one.")
        return
        
    try:
        # Parse the callback data: 'q_index|answer_index'
        q_index_str, user_answer_str = call.data.split('|')
        q_index = int(q_index_str)
        user_answer = int(user_answer_str)
        
        current_state = user_state[chat_id]
        question = QUIZ_QUESTIONS[q_index]
        
        # Check if the user is answering the current expected question
        if q_index != current_state['current_q']:
             bot.answer_callback_query(call.id, "Please answer the current question only.")
             return
             
        # Process the answer
        is_correct = user_answer == question['correct']
        
        # Update user state/score
        current_state['total_answered'] += 1
        current_state['answers'][q_index] = user_answer
        
        feedback_icon = "✅" if is_correct else "❌"
        
        # Assuming your marks are in a string format, convert them to float for calculation
        marks = float(question.get('marks', '1'))
        
        if is_correct:
            current_state['score'] += marks
            feedback_text = f"{feedback_icon} *Correct!* You gained {marks} marks."
        else:
            # Assuming a negative marking rule, e.g., -0.25 (common in competitive exams)
            negative_marks = marks * 0.25
            current_state['score'] -= negative_marks
            feedback_text = f"{feedback_icon} *Wrong!* You lost {negative_marks} marks."
        
        # Prepare the full feedback message
        correct_option_letter = chr(64 + question['correct'])
        correct_option_text = clean_html_for_telegram(question['options'][question['correct'] - 1])
        
        full_feedback = (
            f"*{feedback_text}*\n\n"
            f"The correct option was: {correct_option_letter}. {correct_option_text}"
        )

        if question.get('explanation'):
            explanation_text = clean_html_for_telegram(question['explanation'])
            full_feedback += f"\n\n_Explanation:_ {explanation_text[:500]}..." # Truncate long explanations
        
        # Acknowledge the callback and edit the original message to remove buttons and show feedback
        bot.answer_callback_query(call.id, "Answer registered!")
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=call.message.text.split('\n\n')[0] + f"\n\n---\n{full_feedback}",
            parse_mode='Markdown'
        )
        
        # Move to the next question
        current_state['current_q'] += 1
        send_question(chat_id, current_state['current_q'])
        
    except Exception as e:
        print(f"Error in callback: {e}")
        bot.answer_callback_query(call.id, "An unexpected error occurred while processing your answer.")
        
def end_quiz(chat_id):
    """Sends the final score and removes the user's state."""
    state = user_state.pop(chat_id, None)
    
    if not state:
        return
        
    total_q = len(QUIZ_QUESTIONS)
    final_score = state['score']
    
    summary = (
        f"🎉 *Quiz Finished!* 🎉\n"
        f"You have completed all {total_q} questions.\n\n"
        f"📝 *Summary:*\n"
        f"• *Total Questions:* {total_q}\n"
        f"• *Questions Attempted:* {state['total_answered']}\n"
        f"• *Final Score:* {final_score:.2f} marks"
    )
    
    bot.send_message(chat_id, summary, parse_mode='Markdown')

# --- RUN THE BOT ---
if QUIZ_QUESTIONS:
    print("Bot is polling for messages...")
    # This function keeps the bot running and listening for new messages/callbacks
    # bot.polling(none_stop=True) 
else:
    print("Bot configuration failed due to missing or malformed quiz data.")

# Note: You will need to uncomment bot.polling(none_stop=True) when you run this code.
